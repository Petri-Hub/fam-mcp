from ..data import DegreeProgress, NextCourse
from ..server import mcp, READ_ONLY
from .get_complementary_hours import fetch_complementary_hours
from .get_transcript import fetch_transcript
from .list_courses import list_courses

NEXT_UP_LIMIT = 6

@mcp.tool(title="Degree progress", tags={"academics"}, annotations=READ_ONLY)
async def get_degree_progress() -> DegreeProgress:
  """How far the student is in the degree: approved and remaining courses with workload, the overall average, and approved complementary hours.

  Use it for "how much is left" or "am I on track" questions. Courses of the current term are counted separately from the ones still to take."""

  transcript = await fetch_transcript()
  complementary = await fetch_complementary_hours()
  current = {course.code for course in (await list_courses()).courses}

  courses = [course for semester in transcript.semesters for course in semester.courses]
  approved = [course for course in courses if course.status == "approved"]
  failed = [course for course in courses if course.status == "failed"]
  remaining = [course for course in courses if course.status == "to_take" and course.code not in current]
  averages = [course.average for course in approved if course.average]

  return DegreeProgress(
    approved_courses=len(approved),
    to_take_courses=len(remaining),
    current_term_courses=len(current),
    failed_courses=len(failed),
    semesters_total=len(transcript.semesters),
    workload_hours_approved=sum(course.workload_hours or 0 for course in approved),
    workload_hours_to_take=sum(course.workload_hours or 0 for course in remaining),
    overall_average=round(sum(averages) / len(averages), 2) if averages else None,
    complementary_hours_approved=complementary.approved_hours,
    next_up=[NextCourse(course.code, course.name, course.workload_hours) for course in remaining[:NEXT_UP_LIMIT]]
  )
