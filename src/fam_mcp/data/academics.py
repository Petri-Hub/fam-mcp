from dataclasses import dataclass

@dataclass
class GradeItem:
  title: str
  activity_id: str | None
  date: str | None  # ISO date; the portal shows dd/mm only, the year is the current one
  max_score: float | None
  score: float | None
  graded: bool
  raw: str  # what the portal printed in the score cell, e.g. "NC"

@dataclass
class CourseGrades:
  code: str
  name: str
  items: list[GradeItem]
  stage_average: float | None  # N1/N2/N3 column of the results page, null until a grade is posted

@dataclass
class StageGrades:
  stage: str
  stage_name: str
  weight_percent: int | None
  courses: list[CourseGrades]

@dataclass
class Grades:
  term: str
  stages: list[StageGrades]

@dataclass
class GradingRules:
  pass_average: float
  recovery_pass_average: float
  min_attendance_percent: int
  rounding: str

@dataclass
class CourseResult:
  code: str
  name: str
  grading: str  # "available" or "not_available" (courses the portal does not grade, e.g. complementary activities)
  n1: float | None = None
  mp1: float | None = None
  n2: float | None = None
  mp2: float | None = None
  n3: float | None = None
  mp3: float | None = None
  semester_average: float | None = None
  recovery: float | None = None
  final_average: float | None = None
  max_absences: int | None = None
  absences: int | None = None
  raw_flag: str | None = None  # unlabeled "SIM" cell next to AR; meaning not confirmed

@dataclass
class TermResults:
  term: str
  as_of: str | None
  rules: GradingRules
  weights: dict[str, int]
  courses: list[CourseResult]

@dataclass
class MonthAbsences:
  month: str
  absences: int

@dataclass
class CourseAbsences:
  code: str
  name: str
  workload_hours: int | None
  max_absences: int | None
  total_absences: int | None
  remaining: int | None
  updated_at: str | None
  by_month: list[MonthAbsences]

@dataclass
class Absences:
  term: str
  total: int
  courses: list[CourseAbsences]
  note: str

@dataclass
class TranscriptStudent:
  name: str
  ra: str
  course: str

@dataclass
class TranscriptCourse:
  term: str | None  # "2024/1"; null for courses still to take
  code: str
  name: str
  workload_hours: int | None
  n1: float | None
  n2: float | None
  n3: float | None
  recovery: float | None
  average: float | None
  absences: int | None
  status: str  # approved | to_take | failed | other
  raw_status: str

@dataclass
class TranscriptSemester:
  semester: int
  courses: list[TranscriptCourse]

@dataclass
class Transcript:
  student: TranscriptStudent
  semesters: list[TranscriptSemester]
