from dataclasses import dataclass

@dataclass
class CourseRef:
  code: str
  name: str

@dataclass
class Contact:
  email_primary: str | None
  email_alternate: str | None
  phone_mobile: str | None
  phone_home: str | None
  phone_work: str | None

@dataclass
class Address:
  street: str
  number: str | None
  neighborhood: str
  complement: str | None
  city: str
  state: str
  zip_code: str

@dataclass
class PersonalDocuments:
  cpf: str
  rg: str
  birth_date: str | None
  address: Address

@dataclass
class StudentProfile:
  name: str
  ra: str
  login: str
  course: CourseRef
  class_id: str
  series: str
  section: str
  room: str
  current_term: str
  last_access: str | None
  contact: Contact
  documents: PersonalDocuments | None
  editable_fields_note: str

@dataclass
class Teacher:
  name: str
  id: str

@dataclass
class Course:
  code: str
  name: str
  class_id: str
  teacher: Teacher | None
  teaching_plan_status: str
  google_classroom: bool

@dataclass
class CourseList:
  term: str
  total: int
  courses: list[Course]

@dataclass
class ScheduleSlot:
  weekday: str
  lesson: str
  course_code: str
  course: str
  teacher: str | None
  teacher_id: str | None

@dataclass
class ClassSchedule:
  term: str
  class_id: str
  total: int
  slots: list[ScheduleSlot]

@dataclass
class Exam:
  name: str
  stage: str | None
  course: str
  series: str
  section: str
  discipline: str
  weekday: str | None
  date: str | None
  lessons: int | None

@dataclass
class ExamCalendar:
  total: int
  exams: list[Exam]
  disclaimer: str
