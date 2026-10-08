import json
import sys
import traceback

import httpx

from fastmcp.exceptions import NotFoundError, ToolError as McpToolError, ValidationError
from fastmcp.server.middleware import Middleware, MiddlewareContext

from .errors import Error, InvalidArgumentsError, PortalUnavailableError, PortalUnknownError, ToolError

def _find[E: BaseException](exception: BaseException | None, kind: type[E]) -> E | None:
  """FastMCP wraps whatever a tool raises in its own ToolError; the original is on __cause__."""
  while exception is not None:
    if isinstance(exception, kind):
      return exception
    exception = exception.__cause__
  return None

class ErrorTranslator(Middleware):
  """Turns every tool failure into {"error": {"code", "message", "retryable", "tool"}} JSON."""

  async def on_call_tool(self, context: MiddlewareContext, call_next):
    try:
      return await call_next(context)
    except NotFoundError:
      raise  # an unknown tool name is the client's mistake; FastMCP's own message says so
    except Exception as raised:
      details = {}

      if domain := _find(raised, Error):
        error = domain
        if domain.reason:
          details = {"details": domain.reason}
      elif _find(raised, httpx.TimeoutException) or _find(raised, httpx.ConnectError):
        error = PortalUnavailableError()
      elif _find(raised, httpx.HTTPError):
        error = PortalUnknownError()
      elif invalid := _find(raised, ValidationError):
        error = InvalidArgumentsError()
        cause = invalid.__cause__
        problems = cause.errors() if hasattr(cause, "errors") else []
        details = {"details": "; ".join(f"{'.'.join(map(str, p['loc']))}: {p['msg']}" for p in problems) or str(invalid)}
      else:
        error = ToolError()

      print(traceback.format_exc(), file=sys.stderr)  # the real cause stays in the log; the model only sees the payload

      payload = {"error": {
        "code": error.details.code,
        "message": error.details.message,
        "retryable": error.retryable,
        "tool": context.message.name,
        **details
      }}
      raise McpToolError(json.dumps(payload, ensure_ascii=False)) from raised
