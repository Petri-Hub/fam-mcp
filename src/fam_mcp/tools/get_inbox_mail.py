from ..data import InboxMailContent
from ..server import mcp, client
from ..utils import to_soup
from ..errors import InboxToolError

@mcp.tool
def get_inbox_mail(mail_id: str) -> InboxMailContent:
  """Read the full content of one inbox message from the FAM portal, given its id (from get_inbox)."""

  try:
    response = client.get("fam/pg_portal.php", params={
      "frame": "frame_avisos.php",
      "entrada": "X",
      "msg_read": "X",
      "view": "X",
      "msg_id": mail_id
    })

    soup = to_soup(response.content.decode("latin-1"))

    header = soup.find("td", class_="aviso_titulo_plano").find_all("td")
    subject_label = soup.find("td", class_="aviso_titulo", string="Assunto:")
    body_label = soup.find("td", class_="aviso_titulo", string="Mensagem:")

    return InboxMailContent(
      id=mail_id,
      sender=header[1].get_text(strip=True),
      subject=subject_label.find_parent("tr").find_next_sibling("tr").get_text(strip=True),
      time=header[2].get_text(strip=True),
      body=body_label.find_parent("tr").find_next_sibling("tr").get_text("\n", strip=True)
    )
  except Exception as error:
    raise InboxToolError() from error
