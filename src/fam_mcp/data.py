from dataclasses import dataclass

@dataclass
class InboxMail:
  id: str
  sender: str
  subject: str
  time: str
  unread: bool
  has_attachment: bool

@dataclass
class InboxMailContent:
  id: str
  sender: str
  subject: str
  time: str
  body: str
