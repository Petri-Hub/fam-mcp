from ..data import InboxMail, Inbox
from ..server import mcp, portal, READ_ONLY
from ..utils import text, require, parse_date

from pydantic import Field
from typing import Annotated

import re
import unicodedata

def _fold(value: str) -> str:
  """Lowercase and strip accents so 'jose' matches 'JOSÉ'."""
  return "".join(c for c in unicodedata.normalize("NFKD", value.casefold()) if not unicodedata.combining(c))

@mcp.tool(title="Inbox", tags={"communication"}, annotations=READ_ONLY)
async def get_inbox(
  unread_only: Annotated[bool, Field(description="Only messages not opened yet (shown in bold on the portal).")] = False,
  from_contains: Annotated[str | None, Field(description="Keep messages whose sender contains this text, ignoring case and accents. The portal cuts sender names at 20 characters, so use a first name or surname.")] = None,
  limit: Annotated[int, Field(ge=1, le=200, description="Maximum number of messages to return, newest first.")] = 50
) -> Inbox:
  """List the student's inbox messages (Entrada) from the FAM portal, newest first.
  Use it to see what the teachers and the secretaria sent; open one with get_inbox_mail. `total` counts every message that matches the filters, even when `limit` returns fewer."""

  soup = await portal.page("frame_avisos.php", entrada="X", qtd_msg="X", jumpm=200, msg_email="N", msg_popup="N")

  mails = []
  for row in soup.find_all("tr", onclick=re.compile("msg_id="), class_=re.compile("lovelyrow")):
    cells = row.find_all("td", class_="nicepadding", recursive=False)

    mails.append(InboxMail(
      id=require(re.search(r"msg_id=(\d+)", row["onclick"])).group(1),
      sender=text(cells[0]),
      subject=text(cells[1].find("td")),
      time=parse_date(text(cells[2])) or text(cells[2]),  # the list only shows the date
      unread="lovelyrow1" in row["class"],  # lovelyrow1 is styled bold
      has_attachment=cells[1].find("img", alt="clipes") is not None
    ))

  if unread_only:
    mails = [mail for mail in mails if mail.unread]

  if from_contains:
    mails = [mail for mail in mails if _fold(from_contains) in _fold(mail.sender)]

  return Inbox(total=len(mails), mails=mails[:limit])
