from dataclasses import replace

from ..data import ComplementaryActivity, ComplementaryCategory, ComplementaryCourse, ComplementaryHours, SubmissionWindow
from ..server import mcp, portal, READ_ONLY
from ..utils import parse_datetime, parse_number, require, text

from pydantic import Field
from typing import Annotated, Literal

import re

PORTAL_STATUSES = {"APROVADO": "approved", "REPROVADO": "rejected", "AGUARDANDO APROVAÇÃO": "pending"}

async def fetch_complementary_hours() -> ComplementaryHours:
  """Everything on the Atividade Complementar page, unfiltered, categories included."""
  soup = await portal.page("frame_alu_ativcomp_aluno.php")

  registered = require(soup.find("td", class_="tit_corpo", string="ATIVIDADES REGISTRADAS")).find_parent("table")
  activities = []
  course = None

  for row in registered.find_all("tr"):
    cells = row.find_all("td", recursive=False)

    if len(cells) == 1:  # group heading: "Atividade(s) [NÃO] atribuida(s) a disciplina <code> - <name> no Histórico Escolar"
      heading = re.search(r"disciplina\s+(\d+)\s*-\s*(.+?)\s+no Histórico", text(cells[0]))
      if "atribuida" in text(cells[0]):
        course = ComplementaryCourse(code=heading.group(1), name=heading.group(2)) if heading and "NÃO" not in text(cells[0]) else None
      continue

    if len(cells) != 7 or not (cells[0].get("class") or [""])[0].startswith("Linha"):
      continue  # column titles and totals

    link = row.find("a", href=True)
    portal_status = text(cells[4])
    activities.append(ComplementaryActivity(
      category=text(cells[0]),
      term=text(cells[1]),
      period=text(cells[2]) or None,
      hours=int(parse_number(text(cells[3])) or 0),
      status=PORTAL_STATUSES.get(portal_status.upper(), re.sub(r"\W+", "_", portal_status.lower()).strip("_")),
      portal_status=portal_status,
      note=text(cells[5]).lstrip("/ ").strip() or None,
      proof_url=link["href"] if link else None,
      assigned_to_course=course
    ))

  page_text = text(soup)
  window = re.search(r"Período para envio de Atividades de (.+?) a (\d{2}/\d{2}/\d{4}[^<]*?)(?:\s{2,}|$|Atividades Dispon)", page_text)
  records = re.search(r"Total de registros:\s*(\d+)", page_text)
  approved = re.search(r"Total de Horas Aprovadas:\s*(\d+)", page_text)

  select = soup.find("select", attrs={"name": "id_atividade"})
  categories = []
  for option in select.find_all("option") if select else []:
    category_id = re.search(r"id_atividade=(\d+)", option.get("value", ""))
    if category_id and text(option):
      categories.append(ComplementaryCategory(id=category_id.group(1), name=text(option)))

  return ComplementaryHours(
    submission_window=SubmissionWindow(
      starts_at=parse_datetime(window.group(1)) if window else None,
      ends_at=parse_datetime(window.group(2)) if window else None
    ),
    total_records=int(require(records).group(1)),
    approved_hours=int(require(approved).group(1)),
    activities=activities,
    categories=categories
  )

@mcp.tool(title="Complementary hours", tags={"admin", "academics"}, annotations=READ_ONLY)
async def get_complementary_hours(
  status: Annotated[Literal["approved", "rejected", "pending", "all"], Field(description="Filter the registered activities by result. pending = waiting for approval.")] = "all",
  include_categories: Annotated[bool, Field(description="Also list the categories the portal accepts for new submissions (about 40).")] = False
) -> ComplementaryHours:
  """Complementary activity hours (Atividades Complementares) the student registered: each item with hours and result, the total of approved hours, and the period in which new activities can be submitted.
  Use it for "how many complementary hours do I have" or "which activities were rejected". total_records and approved_hours always cover every record, even when the activities list is filtered."""
  hours = await fetch_complementary_hours()

  return replace(
    hours,
    activities=[a for a in hours.activities if status in ("all", a.status)],
    categories=hours.categories if include_categories else None
  )
