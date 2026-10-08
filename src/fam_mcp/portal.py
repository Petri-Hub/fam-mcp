import asyncio
import sys

from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from http import HTTPStatus

from .errors import AuthenticationError, PortalSessionExpiredError, PortalSystemError, PortalUnavailableError, PortalUnknownError
from .utils import to_soup

class Portal:
  """Async session against the FAM portal: logs in, renews the session when it expires, decodes pages.

  One instance serves the whole server; its lifetime is managed by the lifespan in server.py."""

  def __init__(self, base_url: str, username: str, password: str) -> None:
    """Prepare the session holder; nothing is sent to the portal until start() or the first request.

    base_url is the portal address, username the CPF (digits only) and password the portal password."""
    self._base_url = base_url
    self._username = username
    self._password = password
    self._client = self._new_client()  # one client for the whole run, so in-flight requests are never cut by a re-login
    self._login_lock = asyncio.Lock()
    self._session = 0  # bumped on every successful login; lets concurrent calls share one re-login
    self._sid: str | None = None
    self._host = urlparse(base_url).hostname or ""

  def _new_client(self) -> httpx.AsyncClient:
    """Build the HTTP client: 30 s timeout (10 s to connect) and no automatic redirects, because a redirect is how the portal signals both a successful login and an expired session."""
    return httpx.AsyncClient(base_url=self._base_url, timeout=httpx.Timeout(30, connect=10), follow_redirects=False)

  async def start(self) -> None:
    """Log in when the server starts. A failure is only logged, so the server still starts; the first tool call tries again and reports the error to the client."""
    try:
      await self.login()
    except Exception as error:  # a tool call will retry the login and report the failure properly
      print(f"Initial login failed: {error!r}", file=sys.stderr)

  async def close(self) -> None:
    """Close the HTTP client when the server shuts down."""
    await self._client.aclose()

  async def login(self, seen_session: int | None = None) -> None:
    """Open a fresh session. The portal answers 302 to pg_portal.php on success and to index.php?login_falha=1 on bad credentials.

    seen_session is the session number a failed request was made with; if another call already renewed it, there is nothing to do.
    Raises AuthenticationError on bad credentials."""
    async with self._login_lock:
      if seen_session is not None and seen_session != self._session:
        return

      self._client.cookies.clear()
      response = await self._client.post("fam/validacao.php", data={"user": self._username, "senha": self._password})
      self._raise_for_status(response)
      self._sid = response.cookies.get("PHPSESSID")

      if response.status_code != HTTPStatus.FOUND:
        raise PortalUnknownError()

      if not response.headers.get("location", "").startswith("pg_portal.php"):
        raise AuthenticationError()

      # A CPA survey page can replace the home page until it is dismissed; this is the "answer later" request.
      self._restore_cookie()
      await self._client.post("fam/pg_portal.php", params={"frame": "frame_avisos.php", "entrada": "X", "libera_menu": "X"}, data={"libera_menu": ""})
      self._session += 1

  def _restore_cookie(self) -> None:
    """The portal answers even an expired request with a fresh anonymous PHPSESSID. When such a late response lands after another call
    has logged in again, it would replace the authenticated cookie, so put the authenticated one back before every attempt."""
    if self._sid and {cookie.value for cookie in self._client.cookies.jar if cookie.name == "PHPSESSID"} != {self._sid}:
      self._client.cookies.clear()
      self._client.cookies.set("PHPSESSID", self._sid, domain=self._host, path="/")

  async def request(self, method: str, path: str, params: dict | None = None, data: dict | None = None, headers: dict | None = None) -> httpx.Response:
    """Send a request and return the response, logging in again once if the session expired.

    Raises PortalSessionExpiredError if the portal still sends us to the login page afterwards, and PortalSystemError or PortalUnavailableError on server-side failures."""
    for attempt in range(2):
      session = self._session
      self._restore_cookie()
      response = await self._send(method, path, params, data, headers)
      self._raise_for_status(response)

      if self._session_expired(response):
        if attempt == 0:
          await self.login(session)
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
    """GET a portal path with optional query parameters and headers; see request()."""
    return await self.request("GET", path, params=params, headers=headers)

  async def post(self, path: str, params: dict | None = None, data: dict | None = None) -> httpx.Response:
    """POST form data to a portal path with optional query parameters; see request()."""
    return await self.request("POST", path, params=params, data=data)

  async def page(self, frame: str, **params: str | int) -> BeautifulSoup:
    """GET pg_portal.php?frame=<frame>&... and return the parsed HTML. Extra keyword arguments become query parameters."""
    response = await self.get("fam/pg_portal.php", params={"frame": frame, **params})
    return to_soup(self._decode(response))

  async def page_post(self, frame: str, data: dict, **params: str | int) -> BeautifulSoup:
    """Same as page(), for the few read-only screens that need a form POST; data is the form body."""
    response = await self.post("fam/pg_portal.php", params={"frame": frame, **params}, data=data)
    return to_soup(self._decode(response))

  @staticmethod
  def _decode(response: httpx.Response) -> str:
    """The portal declares ISO-8859-1 but serves Windows-1252 (a teacher's pasted en dash arrives as byte 0x96); cp1252 is identical for every other character."""
    return response.content.decode("cp1252", errors="replace")

  @staticmethod
  def _session_expired(response: httpx.Response) -> bool:
    """True when the portal redirected to its login page (index.php), meaning the session is no longer valid."""
    return response.is_redirect and "index.php" in response.headers.get("location", "")

  @staticmethod
  def _raise_for_status(response: httpx.Response) -> None:
    """Turn the portal's server-side failures into our errors: HTTP 500 is PortalSystemError, 502/503/504 are PortalUnavailableError. Other statuses pass through."""
    if response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
      raise PortalSystemError()
    if response.status_code in (HTTPStatus.BAD_GATEWAY, HTTPStatus.SERVICE_UNAVAILABLE, HTTPStatus.GATEWAY_TIMEOUT):
      raise PortalUnavailableError()
