from dataclasses import dataclass

@dataclass
class AgendaItem:
  date: str
  time: str | None  # HH:MM when the portal gives one
  kind: str  # activity | exam | forum | invoice
  title: str
  detail: str | None
  course: str | None
  ref: dict[str, str]  # ids to pass to the matching tool, e.g. {"activity_id": "10001"}

@dataclass
class Agenda:
  from_date: str
  to_date: str
  total: int
  items: list[AgendaItem]
  unavailable_sources: list[str]  # sources that failed to load; their items are missing from the list

@dataclass
class NextCourse:
  code: str
  name: str
  workload_hours: int | None

@dataclass
class DegreeProgress:
  approved_courses: int
  to_take_courses: int  # still to take, not counting the courses of the current term
  current_term_courses: int
  failed_courses: int
  semesters_total: int
  workload_hours_approved: int
  workload_hours_to_take: int
  overall_average: float | None  # mean of the averages of approved courses with a grade
  complementary_hours_approved: int
  next_up: list[NextCourse]
