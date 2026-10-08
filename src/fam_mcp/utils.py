import re

from bs4 import BeautifulSoup, Tag
from datetime import date, datetime, timedelta, timezone

from .errors import PortalParseError

BRAZIL_TZ = timezone(timedelta(hours=-3)) 

def to_soup(html: str) -> BeautifulSoup:
  return BeautifulSoup(html, 'html.parser')

def text(node: Tag | None) -> str:
  """Visible text of a node with whitespace (including &nbsp;) collapsed; empty string for None."""
  if node is None:
    return ""
  return re.sub(r"\s+", " ", node.get_text(" ")).strip()

def require[T](value: T | None) -> T:
  """Return value, or raise PortalParseError when a selector found nothing (the portal layout changed)."""
  if value is None:
    raise PortalParseError()
  return value

def parse_number(raw: str | None) -> float | None:
  """'8,67' -> 8.67, '10.00' -> 10.0, '', '-', 'NC' -> None."""
  if raw is None:
    return None
  cleaned = raw.strip().replace(".", "").replace(",", ".") if "," in raw else raw.strip()
  try:
    return float(cleaned)
  except ValueError:
    return None

def parse_date(raw: str | None) -> str | None:
  """'28/09/2026' -> '2026-09-28'."""
  match = re.search(r"(\d{2})/(\d{2})/(\d{4})", raw or "")
  if not match:
    return None
  day, month, year = map(int, match.groups())
  return date(year, month, day).isoformat()

def parse_datetime(raw: str | None) -> str | None:
  """'01/11/2026 23:59' -> '2026-11-01T23:59:00-03:00'. A date without time becomes midnight."""
  match = re.search(r"(\d{2})/(\d{2})/(\d{4})(?:\D+(\d{2}):(\d{2})(?::(\d{2}))?)?", raw or "")
  if not match:
    return None
  day, month, year, hour, minute, second = match.groups()
  return datetime(int(year), int(month), int(day), int(hour or 0), int(minute or 0), int(second or 0), tzinfo=BRAZIL_TZ).isoformat()

def mask(value: str, keep_start: int = 0, keep_end: int = 2) -> str:
  """Hide the middle of a sensitive value: mask('12345678901', 3, 2) -> '123******01'."""
  if len(value) <= keep_start + keep_end:
    return "*" * len(value)
  return value[:keep_start] + "*" * (len(value) - keep_start - keep_end) + value[len(value) - keep_end:]

def parse_int(raw: str | None) -> int | None:
  number = parse_number(raw)
  return None if number is None else int(number)

def current_term() -> str:
  """Calendar term the portal is showing, e.g. '2026-2' (the second semester starts in August)."""
  today = datetime.now(BRAZIL_TZ)
  return f"{today.year}-{1 if today.month < 8 else 2}"
