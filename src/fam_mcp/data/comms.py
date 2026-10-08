from dataclasses import dataclass, field

@dataclass
class InboxMail:
  id: str
  sender: str
  subject: str
  time: str
  unread: bool
  has_attachment: bool

@dataclass
class MailAttachment:
  name: str
  url: str
  type: str | None

@dataclass
class InboxMailContent:
  id: str
  sender: str
  subject: str
  time: str
  body: str
  attachments: list[MailAttachment] = field(default_factory=list)

@dataclass
class Inbox:
  total: int
  mails: list[InboxMail]
