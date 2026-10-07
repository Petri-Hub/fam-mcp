from typing import Annotated, Literal

from pydantic import Field

from ..data import ForumDetail, ForumPost
from ..errors import PortalNotFoundError
from ..server import mcp, portal, READ_ONLY
from ..utils import require, text
from .list_forums import parse_long_datetime

import re

FRAME = dict(frame="frame_avisos.php", forum="X", permissao_aluno="X", tipo_acesso="", curso="", serie="", turma="", disc="", ano="", sem="", for_read="X", view="X")

# Replies are mostly other students' registration data; keep what they said, drop their identifiers.
IDENTIFIER_LINES = re.compile(r"^\W*(nome|ra|r\.a\.?|registro|curso|per[ií]odo|semestre|turma)\b|^\W*\d{1,2}\s*[º°o]?\s*(semestre|per[ií]odo)|^\W*\d{6,}\W*$", re.I)

def _lines(cell) -> list[str]:
  """Paragraph-level lines of a post body."""
  paragraphs = [text(p) for p in cell.find_all("p")]
  lines = paragraphs if any(paragraphs) else [line.strip() for line in cell.get_text("\n").split("\n")]
  return [line for line in lines if line]

INLINE_IDENTIFIERS = re.compile(r"\b(?:r\.?a\.?\s*:?\s*)?\d{6,}\b|[-–,]?\s*\b\d{1,2}\s*[º°o]?\s*(?:semestre|per[ií]odo)\b", re.I)

def _anonymize(lines: list[str]) -> str:
  """Drop identifiers from a reply. When a reply was a registration form, its leftover bare name/course words go too."""
  kept = [line for line in lines if not IDENTIFIER_LINES.search(line)]
  scrubbed = [INLINE_IDENTIFIERS.sub("", line).strip() for line in kept]
  touched = len(kept) < len(lines) or scrubbed != kept

  if touched:
    scrubbed = [line for line in scrubbed if len(line.split()) > 5 or re.search(r"[.!?:]", line)]

  return "\n".join(line for line in scrubbed if line)

def _posts(soup) -> list[tuple[str, str | None, list[str], str]]:
  """(author, posted_at, body lines, title cell text) for the opening post and every reply, in page order."""
  posts = []
  for meta in soup.find_all("td", class_="MensagensAtv"):
    match = re.match(r"por:\s*(?P<author>.+?)\s+-\s+(?P<when>[^-]*\d{1,2} de .+)$", text(meta))
    if not match:
      continue

    body_cell = require(require(meta.find_parent("tr")).find_next_sibling("tr")).find("td")
    title_row = meta.find_parent("tr").find_previous_sibling("tr")
    posts.append((match["author"], parse_long_datetime(match["when"]), _lines(body_cell), text(title_row.find("td", style=True)) if title_row else ""))

  return posts

@mcp.tool(title="Forum thread", tags={"communication", "forums"}, annotations=READ_ONLY)
async def get_forum(
  forum_id: Annotated[str, Field(pattern=r"^\d+$", description="The forum id from list_forums, e.g. '2001'")],
  order: Annotated[Literal["newest", "oldest"], Field(description="Order of the replies")] = "newest"
) -> ForumDetail:
  """Read a forum: the teacher's opening message (instructions) and every reply, with author names and dates.

  Use it after list_forums. Other students' RA, course and semester lines are removed from replies."""

  soup = await portal.page(**FRAME, for_id=forum_id)

  if not _posts(soup):
    raise PortalNotFoundError()

  # The portal hides replies already seen unless the "show all messages" form is posted; that form is a POST.
  everything = await portal.page_post(data={"for_semfiltro": "X", "for_id": forum_id}, **FRAME, for_id=forum_id)
  posts = _posts(everything) or _posts(soup)

  opening, replies = posts[0], posts[1:]
  cleaned = [ForumPost(author=author, posted_at=when, body=_anonymize(lines)) for author, when, lines, _ in replies]
  cleaned.sort(key=lambda post: post.posted_at or "", reverse=order == "newest")

  return ForumDetail(
    id=forum_id,
    title=opening[3],
    closed="FÓRUM ENCERRADO" in text(soup),
    created_by=opening[0],
    published_at=opening[1],
    instructions="\n".join(opening[2]),
    total_posts=len(cleaned),
    posts=cleaned
  )
