from typing import Annotated, Literal

from pydantic import Field

import asyncio
import re

from ..data import ClassSchedule, ScheduleSlot
from ..errors import PortalNotFoundError
from ..server import mcp, portal, READ_ONLY
from ..utils import text, require
from .list_courses import parse_plan

# Column order of the timetable grid.
WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT"]

@mcp.tool(title="Class schedule", tags={"academics"}, annotations=READ_ONLY)
async def get_class_schedule(
  weekday: Annotated[Literal["MON", "TUE", "WED", "THU", "FRI", "SAT"] | None, Field(description="Return only this weekday.")] = None,
  course_code: Annotated[str | None, Field(description="Return only slots of this course; the code comes from list_courses, e.g. '1234'.")] = None
) -> ClassSchedule:
  """Weekly timetable of the student's class: which course, teacher and lesson slot falls on each weekday.

  Lessons are numbered (P1, P2 on Saturday, 01 to 04 on weekdays); the portal does not publish clock times.
  """

  plan, grade = await asyncio.gather(portal.page("frame_alu_plano.php", atual="X"), portal.page("frame_alu_gradealuno.php"))
  term, _, courses = parse_plan(plan)

  if course_code and course_code not in {course.code for course in courses}:
    raise PortalNotFoundError()

  table = require(grade.find("table", class_="Grade"))
  slots: list[ScheduleSlot] = []

  for row in table.find_all("tr"):
    cells = row.find_all("td", recursive=False)
    if len(cells) != len(WEEKDAYS) + 1 or text(cells[0]) == "AULA":
      continue

    lesson = text(cells[0])
    for day, cell in zip(WEEKDAYS, cells[1:]):
      lines = cell.get_text("\n", strip=True).split("\n")
      for index, line in enumerate(lines):
        code = re.match(r"\S+\[(\d+)\]$", line)
        if not code or index < 2:
          continue

        teacher = re.match(r"(.+?)\s*\((\d+)\)$", lines[index - 1])
        slots.append(ScheduleSlot(
          weekday=day,
          lesson=lesson,
          course_code=code.group(1),
          course=lines[index - 2] if teacher else lines[index - 1],
          teacher=teacher.group(1) if teacher else None,
          teacher_id=teacher.group(2) if teacher else None
        ))

  class_id = next((course.class_id for course in courses), "")
  slots = [slot for slot in slots if (not weekday or slot.weekday == weekday) and (not course_code or slot.course_code == course_code)]

  return ClassSchedule(term=term, class_id=class_id, total=len(slots), slots=slots)
