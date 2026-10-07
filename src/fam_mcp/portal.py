import asyncio
import sys

import httpx
from bs4 import BeautifulSoup

from http import HTTPStatus

from .errors import AuthenticationError, PortalSessionExpiredError, PortalSystemError, PortalUnavailableError, PortalUnknownError
from .utils import to_soup

class Portal:
  """Async session against the FAM portal: logs in, renews the session when it expires, decodes pages."""

  def __init__(self, base_url: str, username: str, password: str) -> None:
    self._base_url = base_url
    self._username = username
    self._password = password
    self._client: httpx.AsyncClient | None = None
    self._login_lock = asyncio.Lock()

  def _new_client(self) -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=self._base_url, timeout=httpx.Timeout(30, connect=10), follow_redirects=False)

  async def start(self) -> None:
    self._client = self._new_client()
    try:
      await self.login()
    except Exception as error:  # a tool call will retry the login and report the failure properly
      print(f"Initial login failed: {error!r}", file=sys.stderr)

  async def close(self) -> None:
    if self._client:
      await self._client.aclose()
      self._client = None

  async def login(self) -> None:
    """Open a fresh session. The portal answers 302 to pg_portal.php on success and to index.php?login_falha=1 on bad credentials."""
    async with self._login_lock:
      if self._client:
        await self._client.aclose()
      self._client = self._new_client()

      response = await self._client.post("fam/validacao.php", data={"user": self._username, "senha": self._password})
      self._raise_for_status(response)

      if response.status_code != HTTPStatus.FOUND:
        raise PortalUnknownError()

      if not response.headers.get("location", "").startswith("pg_portal.php"):
        raise AuthenticationError()

      # A CPA survey page can replace the home page until it is dismissed; this is the "answer later" request.
      await self._client.post("fam/pg_portal.php", params={"frame": "frame_avisos.php", "entrada": "X", "libera_menu": "X"}, data={"libera_menu": ""})

  async def request(self, method: str, path: str, params: dict | None = None, data: dict | None = None, headers: dict | None = None) -> httpx.Response:
    """Send a request, logging in again once if the session expired."""
    if self._client is None:
      await self.login()

    for attempt in range(2):
      response = await self._send(method, path, params, data, headers)
      self._raise_for_status(response)

      if self._session_expired(response):
        if attempt == 0:
          await self.login()
          continue
        raise PortalSessionExpiredError()

      return response

    raise PortalUnknownError()

  async def _send(self, method: str, path: str, params: dict | None, data: dict | None, headers: dict | None) -> httpx.Response:
    """The portal's Apache sometimes drops a reused keep-alive connection; every request here is a read, so retry once."""
    try:
      return await self._client.request(method, path, params=params, data=data, headers=headers)
    except (httpx.RemoteProtocolError, httpx.ReadError, httpx.WriteError):
      return await self._client.request(method, path, params=params, data=data, headers=headers)

  async def get(self, path: str, params: dict | None = None, headers: dict | None = None) -> httpx.Response:
    return await self.request("GET", path, params=params, headers=headers)

  async def post(self, path: str, params: dict | None = None, data: dict | None = None) -> httpx.Response:
    return await self.request("POST", path, params=params, data=data)

  async def page(self, frame: str, **params: str | int) -> BeautifulSoup:
    """Fetch pg_portal.php?frame=<frame>&... and parse it."""
    response = await self.get("fam/pg_portal.php", params={"frame": frame, **params})
    return to_soup(self._decode(response))

  async def page_post(self, frame: str, data: dict, **params: str | int) -> BeautifulSoup:
    """Same as page(), for the few read-only screens that need a form POST."""
    response = await self.post("fam/pg_portal.php", params={"frame": frame, **params}, data=data)
    return to_soup(self._decode(response))

  @staticmethod
  def _decode(response: httpx.Response) -> str:
    """The portal declares ISO-8859-1 but serves Windows-1252 (a teacher's pasted en dash arrives as byte 0x96); cp1252 is identical for every other character."""
    return response.content.decode("cp1252", errors="replace")

  @staticmethod
  def _session_expired(response: httpx.Response) -> bool:
    return response.is_redirect and "index.php" in response.headers.get("location", "")

  @staticmethod
  def _raise_for_status(response: httpx.Response) -> None:
    if response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
      raise PortalSystemError()
    if response.status_code in (HTTPStatus.BAD_GATEWAY, HTTPStatus.SERVICE_UNAVAILABLE, HTTPStatus.GATEWAY_TIMEOUT):
      raise PortalUnavailableError()
