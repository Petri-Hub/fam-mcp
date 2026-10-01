from ..data import InboxMail
from ..server import mcp, client
from ..utils import to_soup
from ..errors import InboxToolError

import re

@mcp.tool()
def get_inbox() -> list[InboxMail]:
  """List the student's inbox messages (Entrada) from the FAM portal."""

  try:
    response = client.get("fam/pg_portal.php", params={
      "frame": "frame_avisos.php",
      "entrada": "X",
      "qtd_msg": "X",
      "jumpm": 200,
      "msg_email": "N",
      "msg_popup": "N"
    })

    soup = to_soup(response.content.decode("latin-1"))

    mails = []
    for row in soup.find_all("tr", onclick=re.compile("msg_id="), class_=re.compile("lovelyrow")):
      cells = row.find_all("td", class_="nicepadding", recursive=False)

      mails.append(InboxMail(
        id=re.search(r"msg_id=(\d+)", row["onclick"]).group(1),
        sender=cells[0].get_text(strip=True),
        subject=cells[1].find("td").get_text(strip=True),
        time=cells[2].get_text(strip=True),
        unread="lovelyrow1" in row["class"],  # lovelyrow1 is styled bold
        has_attachment=cells[1].find("img", alt="clipes") is not None
      ))

    return mails
  except Exception as error:
    raise InboxToolError() from error
