from dataclasses import dataclass

@dataclass
class ActivityCourse:
  code: str
  name: str

@dataclass
class Activity:
  id: str
  title: str
  course: ActivityCourse
  class_id: str
  created_by: str
  type: str
  starts_at: str | None
  due_at: str | None
  days_left: int | None
  status: str  # open | upcoming | done | other
  portal_status: str
  submitted: bool
  grade: float | None

@dataclass
class ActivityList:
  term: str
  total: int
  activities: list[Activity]

@dataclass
class ActivityMaterial:
  index: int
  title: str
  type: str  # PDF, DOCX... for files; LINK for an external link (see url)
  url: str | None  # only set for LINK materials

@dataclass
class ActivityWindow:
  starts_at: str | None
  ends_at: str | None

@dataclass
class ActivitySubmission:
  title: str
  submitted_by: str
  delivered_on: str | None
  file_type: str | None
  corrected: bool
  teacher_comment: str | None
  grade: float | None

@dataclass
class ActivityDetail:
  id: str
  title: str
  created_by: str
  published_at: str | None
  description: str
  office_hours: str | None
  materials: list[ActivityMaterial]
  submission_window: ActivityWindow
  allowed_file_types: list[str]
  closed: bool
  deliveries: int
  submission: ActivitySubmission | None

@dataclass
class ActivityMaterialFile:
  filename: str
  title: str
  mime_type: str
  size_bytes: int
  saved_to: str

@dataclass
class ForumLastPost:
  author: str
  posted_at: str | None

@dataclass
class Forum:
  id: str
  title: str
  course: ActivityCourse
  class_id: str
  created_by: str
  starts_at: str | None
  ends_at: str | None
  closed: bool
  replies: int
  last_post: ForumLastPost | None
  grade: float | None

@dataclass
class ForumList:
  total: int
  forums: list[Forum]

@dataclass
class ForumPost:
  author: str
  posted_at: str | None
  body: str

@dataclass
class ForumDetail:
  id: str
  title: str
  closed: bool
  created_by: str
  published_at: str | None
  instructions: str
  total_posts: int
  posts: list[ForumPost]

@dataclass
class Survey:
  id: str | None
  name: str
  course: str | None
  class_id: str | None
  professor: str | None
  discipline: str | None
  applied_by: str | None
  participated: bool

@dataclass
class SurveyList:
  term: str
  total: int
  participated: int
  surveys: list[Survey]
  message: str | None
