import re

from typing import Annotated

from pydantic import Field

from ..data import CourseResult, GradingRules, TermResults
from ..errors import PortalNotFoundError
from ..server import mcp, portal, READ_ONLY
from ..utils import current_term, parse_int, parse_number, require, text

def _rule(pattern: str, body: str, default: float) -> float:
  match = re.search(pattern, body)
  return float(match.group(1).replace(",", ".")) if match else default

async def fetch_term_results() -> TermResults:
  soup = await portal.page("frame_alu_notas.php", slc="X", frame_notas="frame_alu_notas_resultados.php")
  page_text = text(soup)

  courses = []
  for row in soup.find_all("tr"):
    cells = row.find_all("td", class_=re.compile("^Coluna"), recursive=False)
    if len(cells) < 12 or not re.fullmatch(r"\d+", text(cells[0])):
      continue

    code, name = text(cells[0]), text(cells[1])
    if "Não disponível" in text(row):
      courses.append(CourseResult(code=code, name=name, grading="not_available"))
      continue

    if len(cells) < 17:
      require(None)

    courses.append(CourseResult(
      code=code, name=name, grading="available",
      n1=parse_number(text(cells[2])), mp1=parse_number(text(cells[4])),
      n2=parse_number(text(cells[5])), mp2=parse_number(text(cells[7])),
      n3=parse_number(text(cells[8])), mp3=parse_number(text(cells[10])),
      semester_average=parse_number(text(cells[11])),
      raw_flag=text(cells[12]) or None,
      recovery=parse_number(text(cells[13])),
      final_average=parse_number(text(cells[14])),
      max_absences=parse_int(text(cells[15])), absences=parse_int(text(cells[16]))
    ))

  require(courses or None)

  as_of = re.search(r"Resultado Parcial em:\s*(\d{2})-(\d{2})-(\d{4})", page_text)
  weights = {stage: int(weight) for stage, weight in re.findall(r"(N[123]) => [^=]*= (\d+) %", page_text)}

  return TermResults(
    term=current_term(),
    as_of=f"{as_of.group(3)}-{as_of.group(2)}-{as_of.group(1)}" if as_of else None,
    rules=GradingRules(
      pass_average=_rule(r"igual ou superior a ([\d,]+)", page_text, 6.0),
      recovery_pass_average=_rule(r"no mínimo ([\d,]+)", page_text, 5.0),
      min_attendance_percent=int(_rule(r"frequência mínima de (\d+)%", page_text, 75)),
      rounding="none" if "NÃO HÁ ARREDONDAMENTO" in page_text.upper() else "unknown"
    ),
    weights=weights,
    courses=courses
  )

@mcp.tool(title="Term results", tags={"academics"}, annotations=READ_ONLY)
async def get_term_results(
  course_code: Annotated[str | None, Field(description="Course code from list_courses, e.g. '1234'. Omit for every course.")] = None
) -> TermResults:
  """Partial result of the current term per course: N1/N2/N3 averages, semester average (MS), recovery (AR), final average (MF) and absence limits, plus the approval rules (pass at 6.0, recovery pass at 5.0, 75% attendance). Use it to answer "how am I doing" or "what do I need to pass"."""

  results = await fetch_term_results()

  if course_code:
    results.courses = [course for course in results.courses if course.code == course_code]
    if not results.courses:
      raise PortalNotFoundError()

  return results
