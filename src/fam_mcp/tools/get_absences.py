import re

from typing import Annotated

from pydantic import Field

from ..data import Absences, CourseAbsences, MonthAbsences
from ..errors import PortalNotFoundError
from ..server import mcp, portal, READ_ONLY
from ..utils import current_term, parse_date, parse_int, require, text

AT_RISK_SHARE = 0.75

@mcp.tool(title="Absences", tags={"academics"}, annotations=READ_ONLY)
async def get_absences(
  course_code: Annotated[str | None, Field(description="Course code from list_courses, e.g. '1234'. Omit for every course.")] = None,
  only_at_risk: Annotated[bool, Field(description="Only courses that already used 75% or more of their allowed absences.")] = False
) -> Absences:
  """Absences per course for the current term with the allowed maximum, how many absences are left, and a month-by-month breakdown. Use it for "can I still miss class" questions. Teachers enter absences themselves, so totals can lag."""

  soup = await portal.page("frame_alu_faltas.php")

  courses = []
  for row in soup.find_all("tr"):
    cells = row.find_all("td", recursive=False)
    label = re.match(r"(\d+)\s+(.+)", text(cells[0])) if len(cells) >= 5 and "GradeNotas" in (cells[0].get("class") or []) else None
    if not label:
      continue

    max_absences = parse_int(text(cells[2]))
    total = parse_int(text(cells[3]))
    if total is None and max_absences is not None:
      total = 0  # the teacher has not entered any absence yet

    by_month = []
    for cell in cells[5:]:
      month, count = text(cell.find("td", class_="ct")), parse_int(text(cell.find("td", class_="GradeNotasDestaque")))
      if month and count is not None:
        by_month.append(MonthAbsences(month=month, absences=count))

    courses.append(CourseAbsences(
      code=label.group(1), name=label.group(2),
      workload_hours=parse_int(text(cells[1])),
      max_absences=max_absences,
      total_absences=total,
      remaining=None if max_absences is None else max_absences - (total or 0),
      updated_at=parse_date(text(cells[4])),
      by_month=by_month
    ))

  require(courses or None)

  if course_code:
    courses = [course for course in courses if course.code == course_code]
    if not courses:
      raise PortalNotFoundError()

  if only_at_risk:
    courses = [course for course in courses if course.max_absences and (course.total_absences or 0) >= AT_RISK_SHARE * course.max_absences]

  return Absences(
    term=current_term(),
    total=len(courses),
    courses=courses,
    note="Absences are entered by each professor, so totals can lag."
  )
