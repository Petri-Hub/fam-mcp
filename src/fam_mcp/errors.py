from .constants import ErrorDetails

class Error(Exception):
  details: ErrorDetails
  retryable: bool = False

  def __init__(self, reason: str | None = None) -> None:
    super().__init__(reason)
    self.reason = reason

  def __str__(self) -> str:
    return f"{self.details.code} - {self.details.message}"

class PortalError(Error):
  details = ErrorDetails.PORTAL_ERROR

class PortalUnknownError(PortalError):
  details = ErrorDetails.PORTAL_UNKNOWN_ERROR
  retryable = True

class PortalSystemError(PortalError):
  details = ErrorDetails.PORTAL_SYSTEM_ERROR
  retryable = True

class PortalUnavailableError(PortalError):
  details = ErrorDetails.PORTAL_UNAVAILABLE_ERROR
  retryable = True

class PortalUnauthorizedError(PortalError):
  details = ErrorDetails.PORTAL_UNAUTHORIZED_ERROR

class PortalSessionExpiredError(PortalError):
  details = ErrorDetails.PORTAL_SESSION_EXPIRED_ERROR

class PortalParseError(PortalError):
  details = ErrorDetails.PORTAL_PARSE_ERROR

class PortalNotFoundError(PortalError):
  details = ErrorDetails.PORTAL_NOT_FOUND_ERROR

class AuthenticationError(PortalError):
  details = ErrorDetails.AUTHENTICATION_ERROR

class ConfigurationError(Error):
  details = ErrorDetails.CONFIGURATION_ERROR

class FamUsernameConfigurationError(ConfigurationError):
  details = ErrorDetails.FAM_USERNAME_CONFIGURATION_ERROR

class FamPasswordConfigurationError(ConfigurationError):
  details = ErrorDetails.FAM_PASSWORD_CONFIGURATION_ERROR

class InvalidArgumentsError(Error):
  details = ErrorDetails.INVALID_ARGUMENTS_ERROR

class ToolError(Error):
  details = ErrorDetails.TOOL_ERROR

class InboxToolError(ToolError):
  details = ErrorDetails.INBOX_TOOL_ERROR
