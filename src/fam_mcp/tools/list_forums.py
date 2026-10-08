from typing import Annotated, Literal

from datetime import datetime
from pydantic import Field

from ..data import Forum, ForumLastPost, ForumList
from ..server import mcp, portal, READ_ONLY
from ..utils import BRAZIL_TZ, parse_date, parse_datetime, parse_number, require, text
from .list_activities import split_course

import re

MONTHS = {
  "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4, "maio": 5, "junho": 6,
  "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12
}

def parse_long_datetime(raw: str) -> str | None:
  """'terça, 22 de setembro de 2026, 21:03' -> '2026-09-22T21:03:00-03:00'."""
  match = re.search(r"(\d{1,2}) de (\w+) de (\d{4}),?\s+(\d{2}):(\d{2})", raw.lower())
  if not match or match.group(2) not in MONTHS:
    return None
  day, month, year, hour, minute = match.group(1), MONTHS[match.group(2)], match.group(3), match.group(4), match.group(5)
  return parse_datetime(f"{int(day):02d}/{month:02d}/{year} {hour}:{minute}")

async def fetch_forums() -> ForumList:
  """Every forum of the current term, unfiltered, in the portal's order."""
  soup = await portal.page("frame_avisos.php", forum="X", permissao_aluno="X", qtd_msg="X", jumpm=200)
  today = datetime.now(BRAZIL_TZ).date().isoformat()

  forums = []
  for row in soup.find_all("tr", onclick=re.compile("for_id=")):
    cells = row.find_all("td", class_="nicepadding", recursive=False)
    info = require(cells[0].find("td", class_="MensagensAtv"))
    created_by, _, period = text(info).partition("||")
    starts, _, ends = period.partition(" - ")

    post_lines = [text(td) for td in cells[2].find_all("td", class_="MensagensAtv")]  # [author, 'date Nº Idf. For. => id'] or ['', 'Seja o Primeiro...']
    author = post_lines[0] if post_lines else ""
    posted_at = parse_long_datetime(post_lines[1]) if len(post_lines) > 1 else None

    course, class_id = split_course(text(cells[0].find("td", class_="Mensagens", width="95%")))
    ends_at = parse_date(ends)

    forums.append(Forum(
      id=require(re.search(r"for_id=(\d+)", row["onclick"])).group(1),
      title=text(cells[0].find("td", width="95%")),
      course=course,
      class_id=class_id,
      created_by=created_by.replace("Criado por:", "").strip(),
      starts_at=parse_date(starts.replace("Período de Vigência:", "")),
      ends_at=ends_at,
      closed=ends_at is not None and ends_at < today,
      replies=int(text(cells[1]) or 0),
      last_post=ForumLastPost(author=author, posted_at=posted_at) if author else None,
      grade=parse_number(text(info.find_next_sibling("td")))
    ))

  return ForumList(total=len(forums), forums=forums)

@mcp.tool(title="Forums", tags={"communication", "forums"}, annotations=READ_ONLY)
async def list_forums(
  status: Annotated[Literal["open", "closed", "all"], Field(description="open = has not ended yet (includes forums that open later), closed = already ended")] = "open",
  course_code: Annotated[str | None, Field(description="Only this course, using the code from list_courses, e.g. '1234'")] = None
) -> ForumList:
  """List the course forums of the current term with period, reply count and last post.

  The forum id it returns feeds get_forum. Forum titles are cut at 70 characters by the portal."""

  result = await fetch_forums()
  forums = result.forums

  if status != "all":
    forums = [f for f in forums if f.closed == (status == "closed")]

  if course_code:
    forums = [f for f in forums if f.course.code == course_code]

  return ForumList(total=len(forums), forums=forums)
