import re

from ..data import Exam, ExamCalendar
from ..server import mcp, portal, READ_ONLY
from ..utils import text, parse_date

WEEKDAYS = {"segunda": "MON", "terça": "TUE", "quarta": "WED", "quinta": "THU", "sexta": "FRI", "sábado": "SAT", "domingo": "SUN"}

DISCLAIMER = "If a course is missing, tell the Secretaria or the course coordination so its exam is generated."

@mcp.tool(title="Exam calendar", tags={"exams"}, annotations=READ_ONLY)
async def get_exam_calendar() -> ExamCalendar:
  """Official exam dates (N2 and N3 evaluations) published for the student's class.

  'lessons' is how many lesson slots the exam takes; the portal publishes no clock time. An empty list means no exam table is published yet.
  """

  soup = await portal.page("frame_alu_calendario_provas.php")

  exams = []
  for title in soup.find_all("td", class_="Descricoes", colspan="7"):
    name = text(title)

    for row in title.find_parent("table").find_all("tr"):
      cells = row.find_all("td", recursive=False)
      if len(cells) != 7 or "Descricoes" in cells[0].get("class", []):
        continue

      course, series, section, discipline, weekday, date, time = (text(cell) for cell in cells)
      lessons = re.match(r"(\d+)\s*AULAS?", time, re.IGNORECASE)

      exams.append(Exam(
        name=name,
        stage=(re.match(r"(N\d)\b", name) or [None, None])[1],
        course=re.sub(r"^\d+\s+", "", course),
        series=series,
        section=section,
        discipline=re.sub(r"^T\s*-\s*", "", discipline),
        weekday=WEEKDAYS.get(weekday.split("-")[0].strip().lower()),
        date=parse_date(date),
        lessons=int(lessons.group(1)) if lessons else None
      ))

  return ExamCalendar(total=len(exams), exams=exams, disclaimer=DISCLAIMER)
