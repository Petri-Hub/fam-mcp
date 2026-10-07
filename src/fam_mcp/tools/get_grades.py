import re

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field

from ..data import CourseGrades, GradeItem, Grades, StageGrades
from ..errors import PortalNotFoundError
from ..server import mcp, portal, READ_ONLY
from ..utils import BRAZIL_TZ, current_term, parse_date, parse_number, require, text
from .get_term_results import fetch_term_results

STAGE_NAMES = {
  "N1": "Avaliação do Professor / Tutor",
  "N2": "Avaliação Colegiada",
  "N3": "Avaliação Integradora"
}

def _items(row) -> list[GradeItem]:
  items = []
  year = datetime.now(BRAZIL_TZ).year

  for cell in row.find_all("td", class_="GradeNotas", recursive=False)[3:]:
    title = date = max_score = None
    for inner in cell.find_all("td"):
      content = text(inner)
      if "GradeNotasDestaque" in (inner.get("class") or []):
        raw = content
        score = parse_number(raw)
        activity = re.fullmatch(r"(.*?)\s*\((\d+)\)", title or "")
        items.append(GradeItem(
          title=activity.group(1) if activity else (title or ""),
          activity_id=activity.group(2) if activity else None,
          date=parse_date(f"{date}/{year}") if date else None,
          max_score=max_score,
          score=score,
          graded=score is not None,
          raw=raw
        ))
        title = date = max_score = None
      elif "Nota Máx" in content:
        found = re.match(r"(\d{2}/\d{2})\s*-\s*Nota Máx\.\[([\d.,]+)\]", content)
        date, max_score = (found.group(1), parse_number(found.group(2))) if found else (None, None)
      elif content:
        title = content

  return items

async def _stage(stage: str, average_of: dict[str, float | None]) -> StageGrades:
  extra = {"upeso": "X"} if stage == "N1" else {}
  soup = await portal.page("frame_alu_notas.php", slc="X", frame_notas="frame_alu_notas_grade.php", etapa=stage, **extra)

  courses = []
  weight = None
  for row in soup.find_all("tr"):
    cells = row.find_all("td", class_="GradeNotas", recursive=False)
    if len(cells) < 3 or not re.fullmatch(r"\d+", text(cells[0])):
      continue

    weight = weight if weight is not None else (int(parse_number(re.sub(r"[^\d,.]", "", text(cells[2]))) or 0) or None)
    courses.append(CourseGrades(code=text(cells[0]), name=text(cells[1]), items=_items(row), stage_average=average_of.get(text(cells[0]))))

  require(courses or None)
  return StageGrades(stage=stage, stage_name=STAGE_NAMES[stage], weight_percent=weight, courses=courses)

@mcp.tool(title="Grades", tags={"academics"}, annotations=READ_ONLY)
async def get_grades(
  stage: Annotated[Literal["N1", "N2", "N3", "all"], Field(description="Evaluation stage: N1 professor (50%), N2 colegiada (30%), N3 integradora (20%). Default all.")] = "all",
  course_code: Annotated[str | None, Field(description="Course code from list_courses, e.g. '1234'. Omit for every course.")] = None
) -> Grades:
  """Scored items (assignments and tests) per course for the current term, grouped by evaluation stage. Use it to see which individual grades are posted; use get_term_results for averages and pass/fail status. Items still ungraded have score null."""

  results = await fetch_term_results()
  stages = ["N1", "N2", "N3"] if stage == "all" else [stage]

  grades = []
  for name in stages:
    averages = {course.code: getattr(course, name.lower()) for course in results.courses}
    grades.append(await _stage(name, averages))

  if course_code:
    for item in grades:
      item.courses = [course for course in item.courses if course.code == course_code]
    if not any(item.courses for item in grades):
      raise PortalNotFoundError()

  return Grades(term=current_term(), stages=grades)
