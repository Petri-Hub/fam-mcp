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

class ConfigurationError(Error):
  details = ErrorDetails.CONFIGURATION_ERROR

class FamUrlConfigurationError(ConfigurationError):
  details = ErrorDetails.FAM_URL_CONFIGURATION_ERROR

class FamUsernameConfigurationError(ConfigurationError):
  details = ErrorDetails.FAM_USERNAME_CONFIGURATION_ERROR

class FamPasswordConfigurationError(ConfigurationError):
  details = ErrorDetails.FAM_PASSWORD_CONFIGURATION_ERROR

class ToolError(Error):
  details = ErrorDetails.TOOL_ERROR

class InboxToolError(ToolError):
  details = ErrorDetails.INBOX_TOOL_ERROR
