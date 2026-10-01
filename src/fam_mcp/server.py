import fastmcp
import os
import httpx
import dotenv

from http import HTTPStatus
from .errors import AuthenticationError, PortalSystemError, PortalUnauthorizedError, PortalUnavailableError, PortalUnknownError, FamUrlConfigurationError, FamUsernameConfigurationError, FamPasswordConfigurationError

dotenv.load_dotenv()

FAM_MCP_NAME = os.getenv("FAM_MCP_NAME")
FAM_URL = os.getenv("FAM_URL")
FAM_USERNAME = os.getenv("FAM_USERNAME")
FAM_PASSWORD = os.getenv("FAM_PASSWORD")

mcp = fastmcp.FastMCP(name=FAM_MCP_NAME)
client = httpx.Client(base_url=FAM_URL or "")  # validate() reports a missing FAM_URL

def validate() -> None:
  if not FAM_URL:
    raise FamUrlConfigurationError()

  if not FAM_USERNAME:
    raise FamUsernameConfigurationError()

  if not FAM_PASSWORD:
    raise FamPasswordConfigurationError()

def authenticate() -> None:
  try:
    response = client.post(url="fam/validacao.php", data={
      "user": FAM_USERNAME,
      "senha": FAM_PASSWORD
    })

    if response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
      raise PortalSystemError()
      
    if response.status_code == HTTPStatus.SERVICE_UNAVAILABLE:
      raise PortalUnavailableError()

    if response.status_code != HTTPStatus.FOUND:
      raise PortalUnknownError()

    if not response.cookies.get("PHPSESSID"):
      raise PortalUnauthorizedError()

    print("Authenticated into FAM portal successfully.")

  except Exception as error:
    raise AuthenticationError() from error

def serve() -> None:
  mcp.run()