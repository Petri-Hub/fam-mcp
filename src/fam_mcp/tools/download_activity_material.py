from typing import Annotated

from pathlib import Path
from pydantic import Field
from urllib.parse import urlparse

from ..data import ActivityMaterialFile
from ..errors import PortalNotFoundError
from ..server import mcp, portal, READ_ONLY
from .get_activity import fetch_activity_page, parse_materials

import mimetypes

CACHE_DIR = Path.home() / ".cache" / "fam-mcp"

@mcp.tool(title="Download assignment material", tags={"assignments"}, annotations=READ_ONLY)
async def download_activity_material(
  activity_id: Annotated[str, Field(pattern=r"^\d+$", description="The activity id from list_activities, e.g. '10001'")],
  material_index: Annotated[int, Field(ge=1, description="1-based position of the file in get_activity().materials")]
) -> ActivityMaterialFile:
  """Download one file the teacher attached to an assignment (instructions PDF, DOCX template...) and return where it was saved.

  Use get_activity first to see the list of materials and their indexes."""

  materials = parse_materials(await fetch_activity_page(activity_id))

  if material_index > len(materials):
    raise PortalNotFoundError()

  title, _, url = materials[material_index - 1]
  # The file lives on the portal host and is only served with a portal Referer (otherwise 302 to the login page).
  response = await portal.get(urlparse(url).path, headers={"Referer": f"{url.split('/fam/')[0]}/fam/pg_portal.php"})

  if response.status_code != 200:
    raise PortalNotFoundError()

  filename = Path(urlparse(url).path).name
  target = CACHE_DIR / activity_id
  target.mkdir(parents=True, exist_ok=True)
  (target / filename).write_bytes(response.content)

  mime_type = response.headers.get("content-type", "").split(";")[0] or mimetypes.guess_type(filename)[0] or "application/octet-stream"
  return ActivityMaterialFile(filename=filename, title=title, mime_type=mime_type, size_bytes=len(response.content), saved_to=str(target / filename))
