import asyncio

from datetime import datetime, timedelta
from typing import Annotated, Literal

from pydantic import Field

from ..data import Agenda, AgendaItem
from ..server import mcp, READ_ONLY
from ..utils import BRAZIL_TZ
from .get_exam_calendar import get_exam_calendar
from .get_financial_status import fetch_financial_status
from .list_activities import fetch_activities
from .list_forums import fetch_forums

Source = Literal["activities", "exams", "forums", "invoices"]

def _split(iso: str | None) -> tuple[str | None, str | None]:
  """'2026-11-01T23:59:00-03:00' -> ('2026-11-01', '23:59'); a date-only value gives no time."""
  if not iso:
    return None, None
  return iso[:10], iso[11:16] if len(iso) > 10 else None

@mcp.tool(title="Agenda dates", tags={"assignments", "exams", "finance"}, annotations=READ_ONLY)
async def get_agenda(
  days_ahead: Annotated[int, Field(ge=1, le=365, description="How many days ahead to look, starting today.")] = 14,
  include: Annotated[list[Source] | None, Field(description="Limit the sources. Omit for all four: activities, exams, forums, invoices.")] = None
) -> Agenda:
  """Everything with a date in the next N days (the student agenda), merged and sorted: assignment deadlines (open ones), exams, forum closings and invoice due dates.

  Use it first for "what do I need to do this week" or "what is coming up". Each item carries the ids to pass to get_activity, get_forum or get_financial_status."""

  sources = set(include or ["activities", "exams", "forums", "invoices"])
  today = datetime.now(BRAZIL_TZ).date()
  last = today + timedelta(days=days_ahead)

  def in_window(day: str | None) -> bool:
    return day is not None and today.isoformat() <= day <= last.isoformat()

  async def nothing():
    return None

  results = await asyncio.gather(
    fetch_activities() if "activities" in sources else nothing(),
    get_exam_calendar() if "exams" in sources else nothing(),
    fetch_forums() if "forums" in sources else nothing(),
    fetch_financial_status() if "invoices" in sources else nothing(),
    return_exceptions=True
  )

  # One broken page must not hide the other three; report it instead. If every requested source failed, raise the first error.
  failed = {name: result for name, result in zip(["activities", "exams", "forums", "invoices"], results) if isinstance(result, BaseException)}
  if failed and len(failed) == len(sources):
    raise next(iter(failed.values()))
  activities, exams, forums, invoices = (None if isinstance(result, BaseException) else result for result in results)

  items: list[AgendaItem] = []

  for activity in activities.activities if activities else []:
    day, time = _split(activity.due_at)
    if activity.status == "open" and in_window(day):
      items.append(AgendaItem(day, time, "activity", activity.title, f"Due in {activity.days_left} day(s)" if activity.days_left is not None else None, activity.course.name, {"activity_id": activity.id}))

  for exam in exams.exams if exams else []:
    if in_window(exam.date):
      items.append(AgendaItem(exam.date, None, "exam", exam.name, f"{exam.lessons} lesson slots" if exam.lessons else None, None if exam.discipline.startswith("T") else exam.discipline, {}))

  for forum in forums.forums if forums else []:
    day, time = _split(forum.ends_at)
    if not forum.closed and in_window(day):
      items.append(AgendaItem(day, time, "forum", forum.title, "Forum closes", forum.course.name, {"forum_id": forum.id}))

  for invoice in invoices.open_invoices if invoices else []:
    if in_window(invoice.due_date):
      items.append(AgendaItem(invoice.due_date, None, "invoice", f"Installment {invoice.installment}", f"R$ {invoice.amount:.2f}" if invoice.amount is not None else None, None, {"nosso_numero": invoice.nosso_numero}))

  items.sort(key=lambda item: (item.date, item.time or ""))

  return Agenda(from_date=today.isoformat(), to_date=last.isoformat(), total=len(items), items=items, unavailable_sources=sorted(failed))
