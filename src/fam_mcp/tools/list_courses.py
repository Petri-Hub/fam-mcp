from typing import Annotated, Literal

from pydantic import Field
from bs4 import BeautifulSoup, Tag

import asyncio
import re

from ..data import Course, CourseList, Teacher
from ..server import mcp, portal, READ_ONLY
from ..utils import text, require

CourseRefTuple = tuple[str, str]

# Image shown by the portal for each teaching-plan state (alt text of the status icon).
PLAN_STATUS = {
  "Em Elaboração": "in_preparation",
  "Enviado P/ Aprovação": "submitted",
  "Aprovado": "approved",
  "Reprovado": "rejected",
  "Não criado": "not_created"
}

def parse_term(soup: BeautifulSoup) -> str:
  """'2026 - 2º Semestre' -> '2026-2'."""
  title = require(soup.find("td", class_="tit_corpo"))
  match = require(re.search(r"(\d{4})\s*-\s*(\d)", text(title)))
  return f"{match.group(1)}-{match.group(2)}"

def parse_plan(soup: BeautifulSoup) -> tuple[str, CourseRefTuple, list[Course]]:
  """Read the Plano de Ensino page: term, course (name, code) and the discipline rows (teacher left empty)."""
  term = parse_term(soup)
  header = re.match(r"(.+?)\s*\[(\d+)\]", text(require(soup.find("td", class_="aviso_titulo"))))
  course = (require(header).group(2), header.group(1))

  # The page nests forms inside table rows, so walk it in document order instead of by row.
  courses: list[Course] = []
  current: Course | None = None
  status_seen = False
  terms_seen = 0

  for node in require(soup.find("table", class_="GradeNotas")).find_all_next():
    if isinstance(node, Tag) and node.name == "td" and "tit_corpo" in node.get("class", []):
      terms_seen += 1  # the previous-terms page stacks older semesters below; only the first one is read
      if terms_seen > 1:
        break
    elif isinstance(node, Tag) and node.name == "td" and node.find("td") is None and re.match(r"Linha(Par|Impar)", " ".join(node.get("class", []))):
      match = re.match(r"(.+?)\s*\[(\d+)\]\s*/\s*(\S+)$", text(node))
      if match:
        current = Course(code=match.group(2), name=match.group(1), class_id=match.group(3), teacher=None, teaching_plan_status="not_created", google_classroom=False)
        courses.append(current)
        status_seen = False
    elif current and isinstance(node, Tag) and node.name == "img" and node.get("alt") and not status_seen and not re.search(r"EAD|google", node.get("src", ""), re.IGNORECASE):
      current.teaching_plan_status = PLAN_STATUS.get(node["alt"].strip(), node["alt"].strip().lower())
      status_seen = True
    elif current and isinstance(node, Tag) and node.name == "a" and "Google Classroom" in node.get_text():
      current.google_classroom = True

  return term, course, courses

def parse_teachers(grade: BeautifulSoup) -> dict[str, Teacher]:
  """Map course code -> teacher from the timetable grid (cells read 'Course / Teacher(id) / class[code]')."""
  teachers: dict[str, Teacher] = {}
  for cell in grade.find_all("td", class_=re.compile("Linha")):
    lines = cell.get_text("\n", strip=True).split("\n")
    for index, line in enumerate(lines):
      code = re.match(r"\S+\[(\d+)\]$", line)
      teacher = re.match(r"(.+?)\s*\((\d+)\)$", lines[index - 1]) if code and index > 0 else None
      if code and teacher:
        teachers[code.group(1)] = Teacher(name=teacher.group(1), id=teacher.group(2))
  return teachers

@mcp.tool(title="Courses of the term", tags={"academics"}, annotations=READ_ONLY)
async def list_courses(
  term: Annotated[Literal["current", "previous"], Field(description="'current' is the ongoing semester; 'previous' is the last one (teachers are not available for it). Older terms are in get_transcript.")] = "current"
) -> CourseList:
  """List the student's courses (disciplinas) of the current or previous semester with teacher, class and teaching-plan status.

  Use it to resolve a course name to its code: every other tool that filters by course takes the code returned here.
  """

  if term == "previous":
    plan_term, _, courses = parse_plan(await portal.page("frame_alu_plano.php", anterior="X"))
  else:
    plan, grade = await asyncio.gather(portal.page("frame_alu_plano.php", atual="X"), portal.page("frame_alu_gradealuno.php"))
    plan_term, _, courses = parse_plan(plan)
    teachers = parse_teachers(grade)
    for course in courses:
      course.teacher = teachers.get(course.code)

  return CourseList(term=plan_term, total=len(courses), courses=courses)
