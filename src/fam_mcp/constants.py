from enum import Enum, unique

@unique
class ErrorDetails(Enum):
  PORTAL_ERROR              = ("PT-000", "Core Portal error, something went wrong.")
  PORTAL_UNKNOWN_ERROR      = ("PT-001", "Portal returned an unknown error. Try again in a moment.")
  PORTAL_SYSTEM_ERROR       = ("PT-002", "Portal returned a fatal error. Test again in a moment.")
  PORTAL_UNAVAILABLE_ERROR  = ("PT-003", "Portal is currently unavailable. Test again later.")
  PORTAL_UNAUTHORIZED_ERROR = ("PT-004", "You don't have permission to do this action.")
  PORTAL_SESSION_EXPIRED_ERROR = ("PT-005", "Portal session expired and logging in again failed.")
  PORTAL_PARSE_ERROR        = ("PT-006", "Portal page layout changed; the data could not be read.")
  PORTAL_NOT_FOUND_ERROR    = ("PT-007", "The portal has no item with that id.")
  AUTHENTICATION_ERROR      = ("AU-001", "Authentication failed. Check your credentials.")
  CONFIGURATION_ERROR       = ("CF-000", "Invalid configuration. Check your environment variables.")
  FAM_URL_CONFIGURATION_ERROR      = ("CF-001", "FAM_URL is missing. Set it in your environment or .env file.")
  FAM_USERNAME_CONFIGURATION_ERROR = ("CF-002", "FAM_USERNAME is missing. Set it in your environment or .env file.")
  FAM_PASSWORD_CONFIGURATION_ERROR = ("CF-003", "FAM_PASSWORD is missing. Set it in your environment or .env file.")
  INVALID_ARGUMENTS_ERROR   = ("AR-001", "Invalid arguments.")
  TOOL_ERROR                = ("TL-000", "Unknown error while calling this MCP tool.")
  INBOX_TOOL_ERROR          =("TL-001", "Something went wrong when using this Inbox tool.")

  def __init__(self, code: str, message: str):
    self.code = code
    self.message = message
