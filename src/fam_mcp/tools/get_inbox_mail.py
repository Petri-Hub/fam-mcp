from ..data import InboxMailContent, MailAttachment
from ..errors import PortalNotFoundError
from ..server import mcp, portal, READ_ONLY
from ..utils import text, require

@mcp.tool(title="Read inbox message", tags={"communication"}, annotations=READ_ONLY)
async def get_inbox_mail(mail_id: str) -> InboxMailContent:
  """Read the full content of one inbox message from the FAM portal, given its id (from get_inbox), including the files attached to it.
  Note that the portal marks a message as read when it is opened."""

  soup = await portal.page("frame_avisos.php", entrada="X", msg_read="X", view="X", msg_id=mail_id)

  header_cell = soup.find("td", class_="aviso_titulo_plano")
  if header_cell is None:  # an unknown id renders the page without the message header
    raise PortalNotFoundError()

  header = header_cell.find_all("td")
  subject_label = require(soup.find("td", class_="aviso_titulo", string="Assunto:"))
  body_label = require(soup.find("td", class_="aviso_titulo", string="Mensagem:"))

  attachments = []
  for link in soup.find_all("input", attrs={"name": "mat_link"}):  # "Material Associado" rows keep the file URL in a hidden field
    row = link.find_parent("tr")
    type_label = row.find("font", class_="Mensagens")
    attachments.append(MailAttachment(
      name=text(row.find("td")),
      url=link["value"],
      type=text(type_label) or None
    ))

  return InboxMailContent(
    id=mail_id,
    sender=text(header[1]),
    subject=text(require(subject_label.find_parent("tr").find_next_sibling("tr"))),
    time=text(header[2]),
    body=require(body_label.find_parent("tr").find_next_sibling("tr")).get_text("\n", strip=True),
    attachments=attachments
  )
