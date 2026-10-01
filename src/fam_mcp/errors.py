from .constants import ErrorDetails

class Error(Exception):
  details: ErrorDetails

  def __str__(self) -> str:
    return f"{self.details.code} - {self.details.message}"

class PortalError(Error):
  details = ErrorDetails.PORTAL_ERROR

class PortalUnknownError(PortalError):
  details = ErrorDetails.PORTAL_UNKNOWN_ERROR

class PortalSystemError(PortalError):
  details = ErrorDetails.PORTAL_SYSTEM_ERROR

class PortalUnavailableError(PortalError):
  details = ErrorDetails.PORTAL_UNAVAILABLE_ERROR

class PortalUnauthorizedError(PortalError):
  details = ErrorDetails.PORTAL_UNAUTHORIZED_ERROR

class AuthenticationError(PortalError):
  details = ErrorDetails.AUTHENTICATION_ERROR

class InboxToolError(Error):
  details = ErrorDetails.INBOX_TOOL_ERROR
