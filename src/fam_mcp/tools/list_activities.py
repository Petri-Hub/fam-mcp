from typing import Annotated, Literal

from datetime import datetime
from pydantic import Field

from ..data import Activity, ActivityCourse, ActivityList
from ..server import mcp, portal, READ_ONLY
from ..utils import BRAZIL_TZ, parse_datetime, parse_number, require, text

import re

STATUSES = {
  "Em andamento": "open",
  "Não liberada": "upcoming",
  "Finalizada": "done",
  "Participação Registrada": "done"
}

def _term(soup) -> str:
  """'Página Inicial - Período [2026-2]' -> '2026-2'."""
  return require(re.search(r"Período \[(\d{4}-\d)\]", text(soup))).group(1)

def split_course(raw: str) -> tuple[ActivityCourse, str]:
  """'Course Name [1234] / 10-01-A' -> (ActivityCourse('1234', 'Course Name'), '10-01-A')."""
  match = require(re.match(r"(?P<name>.+?)\s*\[(?P<code>[^\]]+)\]\s*/\s*(?P<class_id>\S+)", raw))
  return ActivityCourse(code=match["code"], name=match["name"]), match["class_id"]

async def fetch_activities() -> ActivityList:
  """Every activity of the current term, unfiltered, in the portal's order."""
  soup = await portal.page("frame_avisos.php", atividades="X", permissao_aluno="X", qtd_msg="X", jumpm=200)

  activities = []
  for row in soup.find_all("tr", onclick=re.compile("atv_id=")):
    cells = row.find_all("td", class_="nicepadding", recursive=False)
    info = require(cells[0].find("td", class_="MensagensAtv"))
    meta = text(info)  # 'Criado por: X || Período de Vigência: 28/09/2026 00:00 - 01/11/2026 23:59'
    created_by, _, period = meta.partition("||")
    starts, _, ends = period.partition(" - ")

    status_text = text(cells[1].find("td", class_="MensagensAtv"))  # 'Situação: Em andamento Nº Idf. Atv. => 10001'
    portal_status = require(re.search(r"Situação:\s*(.+?)\s*Nº Idf", status_text)).group(1)

    indicator = text(cells[2].find("div"))  # '30 dia(s)' while open, 'OK' once delivered, '/' when missed
    course, class_id = split_course(text(cells[0].find("td", class_="Mensagens", width="95%")))
    days = re.match(r"(\d+)", indicator)

    activities.append(Activity(
      id=require(re.search(r"atv_id=(\d+)", row["onclick"])).group(1),
      title=text(cells[0].find("td", width="95%")),
      course=course,
      class_id=class_id,
      created_by=created_by.replace("Criado por:", "").strip(),
      type=text(cells[1].find("td")),
      starts_at=parse_datetime(starts),
      due_at=parse_datetime(ends),
      days_left=int(days.group(1)) if days else None,
      status=STATUSES.get(portal_status, "other"),
      portal_status=portal_status,
      submitted=indicator == "OK",
      grade=parse_number(text(info.find_next_sibling("td")))  # right-aligned cell next to the metadata; "Nota" is just a header
    ))

  return ActivityList(term=_term(soup), total=len(activities), activities=activities)

@mcp.tool(title="Assignments", tags={"assignments"}, annotations=READ_ONLY)
async def list_activities(
  status: Annotated[Literal["open", "upcoming", "done", "all"], Field(description="open = still to deliver (Em andamento), upcoming = not released yet (Não liberada), done = finished or delivered, all = everything")] = "open",
  course_code: Annotated[str | None, Field(description="Only this course, using the code from list_courses, e.g. '1234'")] = None,
  due_within_days: Annotated[int | None, Field(ge=0, description="Only activities whose deadline falls within this many days from now")] = None,
  limit: Annotated[int, Field(ge=1, le=200, description="Maximum number of activities to return")] = 50
) -> ActivityList:
  """List the student's assignments (Atividades) of the current term, soonest deadline first.

  Use it for "what do I still have to deliver" (default) or to review past work and grades. The activity id it returns feeds get_activity and download_activity_material."""

  result = await fetch_activities()
  activities = result.activities

  if status != "all":
    activities = [a for a in activities if a.status == status]

  if course_code:
    activities = [a for a in activities if a.course.code == course_code]

  if due_within_days is not None:
    now = datetime.now(BRAZIL_TZ)
    activities = [a for a in activities if a.due_at and 0 <= (datetime.fromisoformat(a.due_at) - now).days <= due_within_days]

  activities = sorted(activities, key=lambda a: a.due_at or "")
  return ActivityList(term=result.term, total=len(activities), activities=activities[:limit])  # total counts every match, like get_inbox
