import fastmcp
import os
import dotenv

from contextlib import asynccontextmanager
from fastmcp.server.middleware.timing import TimingMiddleware

from .errors import FamUrlConfigurationError, FamUsernameConfigurationError, FamPasswordConfigurationError
from .middleware import ErrorTranslator
from .portal import Portal

dotenv.load_dotenv()

FAM_MCP_NAME = os.getenv("FAM_MCP_NAME") or "fam"
FAM_URL = os.getenv("FAM_URL")
FAM_USERNAME = os.getenv("FAM_USERNAME")
FAM_PASSWORD = os.getenv("FAM_PASSWORD")

INSTRUCTIONS = """\
FAM student portal (Faculdade de Americana). Read-only access to ONE student's data.
Start with get_student_profile to learn the RA, class and current term. Use list_courses to resolve a course name to its code; every course filter takes the code, not the name.
For "what is due", "what is coming up" or "what is on my agenda" questions call get_agenda first; for "can I still miss class" call get_absences; for "how am I doing" call get_term_results.
Dates are ISO 8601 in America/Sao_Paulo. Grades are 0-10 numbers; null means not graded yet.
The portal is slow (several seconds per page): prefer one broad call over many narrow ones.
Failures return {"error": {"code", "message", "retryable", "tool"}}; retry only when retryable is true.
"""

portal = Portal(FAM_URL or "", FAM_USERNAME or "", FAM_PASSWORD or "")  # validate() reports missing settings

@asynccontextmanager
async def portal_session(_server: fastmcp.FastMCP):
  await portal.start()
  try:
    yield {}
  finally:
    await portal.close()

mcp = fastmcp.FastMCP(
  name=FAM_MCP_NAME,
  instructions=INSTRUCTIONS,
  version="0.2.0",
  middleware=[ErrorTranslator(), TimingMiddleware()],
  lifespan=portal_session,
  mask_error_details=True,
  strict_input_validation=True,
)

# Every tool only reads from the portal: safe to auto-approve, safe to repeat.
READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True}

def validate() -> None:
  if not FAM_URL:
    raise FamUrlConfigurationError()

  if not FAM_USERNAME:
    raise FamUsernameConfigurationError()

  if not FAM_PASSWORD:
    raise FamPasswordConfigurationError()

def serve() -> None:
  mcp.run()
