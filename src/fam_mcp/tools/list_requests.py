from ..data import SecretariaRequest, SecretariaRequestList
from ..server import mcp, portal, READ_ONLY
from ..utils import parse_date, require, text

from pydantic import Field
from typing import Annotated, Literal

import re

@mcp.tool(title="Secretaria requests", tags={"admin"}, annotations=READ_ONLY)
async def list_requests(
  status: Annotated[Literal["pending", "in_progress", "finished", "all"], Field(description="Which group to return; the other groups come back empty. pending = not yet submitted, in_progress = being processed, finished = closed.")] = "all"
) -> SecretariaRequestList:
  """List the requests (requerimentos) the student opened with the Secretaria, such as transcripts, course-load analysis or enrollment locking.
  Use it to check whether a request is still being processed."""

  soup = await portal.page("frame_alu_requerimentos.php")
  require(soup.find(class_="titulo", string=re.compile("Requerimentos")))

  groups: dict[str, list[SecretariaRequest]] = {"pending": [], "in_progress": [], "finished": []}

  for heading in soup.find_all("td", class_=re.compile("^ReqAlerta")):
    title = text(heading).lower()
    group = "pending" if "pendente" in title else "in_progress" if "processo" in title else "finished" if "finalizad" in title else None
    if group is None:
      continue

    for row in heading.find_parent("table").find_all("tr"):
      cells = row.find_all("td", recursive=False)
      if len(cells) < 4 or not re.fullmatch(r"\d+", text(cells[0])):
        continue  # heading, column titles, totals

      groups[group].append(SecretariaRequest(
        number=text(cells[0]),
        type_code=text(cells[1]),
        type=text(cells[2]),
        requested_at=parse_date(text(cells[3]))
      ))

  return SecretariaRequestList(**{name: items if status in (name, "all") else [] for name, items in groups.items()})
