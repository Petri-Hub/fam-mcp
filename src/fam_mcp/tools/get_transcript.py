import re

from typing import Annotated, Literal

from pydantic import Field

from ..data import Transcript, TranscriptCourse, TranscriptSemester, TranscriptStudent
from ..errors import PortalNotFoundError
from ..server import mcp, portal, READ_ONLY
from ..utils import parse_int, parse_number, require, text

STATUSES = {"Aprovado": "approved", "A Cursar": "to_take", "Reprovado": "failed"}

def _field(soup, label: str) -> str:
  cell = require(soup.find("td", class_="Descricoes", string=lambda value: value and value.strip() == label))
  return text(require(cell.find_next_sibling("td")))

async def fetch_transcript() -> Transcript:
  """Parse Extrato de Notas into a Transcript (all semesters, all courses); reused by get_degree_progress."""
  soup = await portal.page("frame_alu_extrato_notas.php")

  # The portal's HTML nests every semester table inside the previous one, so walk all rows in document order
  # and attach each course row to the latest "SEMESTRE nn" header seen.
  semesters = []
  for row in soup.find_all("tr"):
    title = row.find("td", class_="titulo", string=re.compile(r"SEMESTRE\s+\d+"), recursive=False)
    if title:
      semesters.append(TranscriptSemester(semester=int(re.search(r"\d+", text(title)).group()), courses=[]))
      continue

    cells = row.find_all("td", class_="GradeNotas", recursive=False)
    label = re.match(r"(\d+)\s+(.+)", text(cells[1])) if len(cells) == 10 else None
    if not label or not semesters:
      continue

    raw_status = text(cells[9])
    term = text(cells[0])
    semesters[-1].courses.append(TranscriptCourse(
      term=term if re.fullmatch(r"\d{4}/\d", term) else None,
      code=label.group(1), name=label.group(2),
      workload_hours=parse_int(text(cells[2])),
      n1=parse_number(text(cells[3])), n2=parse_number(text(cells[4])), n3=parse_number(text(cells[5])),
      recovery=parse_number(text(cells[6])), average=parse_number(text(cells[7])),
      absences=parse_int(text(cells[8])),
      status=STATUSES.get(raw_status, "other"), raw_status=raw_status
    ))

  require(semesters or None)

  return Transcript(
    student=TranscriptStudent(name=_field(soup, "ALUNO(A):"), ra=_field(soup, "RA:"), course=_field(soup, "CURSO:")),
    semesters=semesters
  )

@mcp.tool(title="Transcript", tags={"academics"}, annotations=READ_ONLY)
async def get_transcript(
  semester: Annotated[int | None, Field(ge=1, le=12, description="Curriculum semester (1-8), not the calendar term. Omit for all semesters.")] = None,
  status: Annotated[Literal["approved", "to_take", "all"], Field(description="Filter courses by result. Default all.")] = "all"
) -> Transcript:
  """Full grade history by curriculum semester (Extrato de Notas): every course with its three grades, recovery, average, absences and result, including courses still to take. Use it for past grades or to see what remains in the degree; use get_term_results for the current term."""

  transcript = await fetch_transcript()

  if semester is not None:
    transcript.semesters = [item for item in transcript.semesters if item.semester == semester]
    if not transcript.semesters:
      raise PortalNotFoundError(f"The transcript has no semester {semester}.")

  if status != "all":
    for item in transcript.semesters:
      item.courses = [course for course in item.courses if course.status == status]

  return transcript
