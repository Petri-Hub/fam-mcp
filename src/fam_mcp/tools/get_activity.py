from typing import Annotated

from pydantic import Field

from ..data import ActivityDetail, ActivityMaterial, ActivitySubmission, ActivityWindow
from ..errors import PortalNotFoundError
from ..server import mcp, portal, READ_ONLY
from ..utils import parse_date, parse_datetime, parse_number, require, text

import re

from urllib.parse import urlparse

# Blocks inside the description cell that are exposed through their own fields.
SEPARATE_SECTIONS = {"Material Associado", "Período de Vigência"}

async def fetch_activity_page(activity_id: str):
  """The detail page of one activity; PortalNotFoundError when the portal returns an empty frame for the id."""
  soup = await portal.page(
    "frame_avisos.php", atividades="X", permissao_aluno="X", tipo_acesso="", curso="", serie="", turma="", disc="", ano="", sem="",
    atv_read="X", view="X", atv_id=activity_id, tipo_ativ="N"
  )

  if soup.find("td", class_="aviso_titulo", string="Título da Atividade:") is None:
    raise PortalNotFoundError("The portal shows nothing for this id: it does not exist or the activity is not released yet (status 'upcoming' in list_activities).")

  return soup

def parse_materials(soup) -> list[tuple[str, str, str]]:
  """(title, file type, absolute url) of every file attached by the teacher, in page order."""
  materials = []
  for field in soup.find_all("input", attrs={"name": "mat_link"}):
    row = field.find_parent("tr")
    materials.append((text(row.find("td")), text(row.find("font", class_="Mensagens")), field["value"]))
  return materials

def is_external(url: str) -> bool:
  """Teachers can attach a plain link (e.g. Google Classroom) instead of a file; only files live on the portal host."""
  return not (urlparse(url).hostname or "").endswith("famportal.com.br")

def _value_below(soup, label: str):
  """The cell in the row below a 'Título da Atividade:'-style label cell."""
  return require(require(soup.find("td", class_="aviso_titulo", string=label)).find_parent("tr").find_next_sibling("tr")).find("td")

def _description(cell) -> list[str]:
  """Readable lines of the teacher's HTML description, minus the sections that have their own fields."""
  tables = cell.find_all("table", recursive=False)
  blocks = []

  for table in tables or [cell]:
    lines = []
    for element in table.find_all(["p", "li"]):
      if element.name == "p" and element.find_parent("li"):
        continue
      line = text(element)
      if line:
        lines.append(f"- {line}" if element.name == "li" else line)

    if tables and lines and lines[0] in SEPARATE_SECTIONS:
      continue

    if tables and lines and lines[0] == "Descrição da Atividade":
      lines = lines[1:]  # banner row of the teacher's template

    blocks.append("\n".join(lines))

  return [block for block in blocks if block]

def _window(soup) -> ActivityWindow:
  """'De: 28/09/2026 à 01/11/2026' + 'Horário De: 00:00:01 à 23:59:59' (the delivery period)."""
  label = require(soup.find("td", class_="aviso_titulo", string="Período de Vigência:"))
  dates = text(label.find_parent("tr").find_next_sibling("tr"))
  times = text(label.find_parent("tr").find_next_sibling("tr").find_next_sibling("tr"))

  day_from, day_to = re.findall(r"\d{2}/\d{2}/\d{4}", dates)[:2]
  time_from, time_to = (re.findall(r"\d{2}:\d{2}:\d{2}", times) + ["00:00:00", "23:59:59"])[:2]
  return ActivityWindow(starts_at=parse_datetime(f"{day_from} {time_from}"), ends_at=parse_datetime(f"{day_to} {time_to}"))

def _submissions(soup) -> list[ActivitySubmission]:
  """The student's deliveries. The portal's table markup is broken (misplaced </form>), so walk the document order instead of sibling rows."""
  submissions = []
  for meta in soup.find_all("td", class_="MensagensAtv"):
    if "Entregue por:" not in text(meta):
      continue

    info = re.match(r"Entregue por:\s*(.+?)\s*\[\d+\]\s*\|\|\s*Data de Entrega:\s*(\S+)", text(meta))
    verdict = require(require(meta.find_next(string=re.compile("Devolutiva"))).find_parent("td"))
    comment_cell = require(verdict.find_next("td"))
    comment = text(comment_cell)
    grade_cell = comment_cell.find_next("td")

    submissions.append(ActivitySubmission(
      title=text(meta.find_previous("td")),
      submitted_by=info.group(1) if info else "",
      delivered_on=parse_date(info.group(2)) if info else None,
      file_type=text(meta.find_next("font", class_="Mensagens")) or None,
      corrected="JÁ CORRIGIDO" in text(verdict),
      teacher_comment=None if not comment or comment.startswith("Nenhum comentário") else comment,
      grade=parse_number(text(grade_cell))
    ))
  return submissions

@mcp.tool(title="Assignment detail", tags={"assignments"}, annotations=READ_ONLY)
async def get_activity(
  activity_id: Annotated[str, Field(pattern=r"^\d+$", description="The activity id from list_activities, e.g. '10001'")]
) -> ActivityDetail:
  """Read one assignment in full: instructions, attached materials, delivery window, accepted file types and the student's own delivery with grade and teacher feedback, if any.

  Use it after list_activities when the student needs to know what an assignment asks for."""

  soup = await fetch_activity_page(activity_id)

  header = require(soup.find("td", class_="aviso_titulo_planob")).find_all("td")
  lines = _description(_value_below(soup, "Descrição da Atividade:"))
  description = "\n\n".join(lines)
  submissions = _submissions(soup)

  allowed = []
  permitted = soup.find("td", string="Arquivos Permitidos:")
  if permitted:
    allowed = [text(font) for font in permitted.find_parent("tr").find_all("font", class_="Mensagens")]

  return ActivityDetail(
    id=activity_id,
    title=text(_value_below(soup, "Título da Atividade:")),
    created_by=text(header[1]).title(),
    published_at=parse_date(text(header[2])),
    description=description,
    office_hours=next((line.lstrip("- ") for line in description.split("\n") if re.search(r"plant[ãa]o", line, re.I)), None),
    materials=[
      ActivityMaterial(index=i, title=title, type="LINK" if is_external(url) else kind, url=url if is_external(url) else None)
      for i, (title, kind, url) in enumerate(parse_materials(soup), start=1)
    ],
    submission_window=_window(soup),
    allowed_file_types=allowed,
    closed="Prazo Encerrado para Entregas" in text(soup),
    deliveries=len(submissions),
    submission=submissions[0] if submissions else None
  )
