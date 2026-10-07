from typing import Annotated

from pydantic import Field

import asyncio
import re

from ..data import Address, Contact, CourseRef, PersonalDocuments, StudentProfile
from ..server import mcp, portal, READ_ONLY
from ..utils import text, require, parse_date, parse_datetime
from .list_courses import parse_plan

EDITABLE_FIELDS_NOTE = "Only email, phone and school type can be changed on the portal."

def mask_cpf(digits: str) -> str:
  return f"{digits[:3]}.***.***-{digits[-2:]}" if len(digits) == 11 else "*" * len(digits)

def mask_rg(raw: str) -> str:
  return re.sub(r"\d", "*", raw[:-2]) + raw[-2:] if raw else raw

def mask_phone(raw: str) -> str | None:
  digits = re.sub(r"\D", "", raw)
  if not digits.strip("0"):
    return None  # the portal stores "0" for a missing phone
  if len(digits) == 11:
    return f"({digits[:2]}) {digits[2]}****-{digits[-4:]}"
  return "*" * (len(digits) - 4) + digits[-4:]

@mcp.tool(title="Student profile", tags={"profile"}, annotations=READ_ONLY)
async def get_student_profile(
  include_documents: Annotated[bool, Field(description="Also return birth date and home address, plus CPF and RG (always masked). Off by default.")] = False
) -> StudentProfile:
  """Who is logged in: name, RA (Registro do Aluno), class, current term, room, last access and the contact data from the registration form.

  Call it first to learn the RA, class and current term. The login is the student's CPF, so it is always returned masked.
  """

  registration, plan = await asyncio.gather(portal.page("frame_cadastro.php"), portal.page("frame_alu_plano.php", atual="X"))
  term, (course_code, course_name), _ = parse_plan(plan)

  def field(name: str) -> str:
    return (require(registration.find("input", attrs={"name": name})).get("value") or "").strip()

  header = require(re.match(r"(.+?)\s*\(\s*(\d+)\s*\)", text(require(registration.find("table", class_="login")).find("td"))))
  banner = text(require(registration.find(string=re.compile("último acesso")).find_parent("td")))
  last_access = re.search(r"(\d{2}/\d{2}/\d{4}) - (\d{2}:\d{2}:\d{2})", banner)
  login = require(re.search(r"Login:\s*\[(\d+)\]", banner)).group(1)

  def after_label(label: str) -> str:
    """Value printed under a 'Turma:' / 'Localização:' label in the header."""
    marker = require(registration.find(string=re.compile(label)))
    return text(require(marker.find_parent("font").find_next("font", class_="login-u")))

  class_id = after_label("Turma")
  room = after_label("Localiza")
  series, section = require(re.match(r"\d+-(\w+)-(\w+)", class_id)).groups()

  documents = None
  if include_documents:
    number = field("dados_numero")
    documents = PersonalDocuments(
      cpf=mask_cpf(re.sub(r"\D", "", field("dados_cpf"))),
      rg=mask_rg(field("dados_rg")),
      birth_date=parse_date(field("dados_dt_nasc2")),
      address=Address(
        street=field("dados_endereco"),
        number=number if number.strip("0") else None,
        neighborhood=field("dados_bairro"),
        complement=field("dados_complemento") or None,
        city=field("dados_cidade"),
        state=field("dados_estado"),
        zip_code=field("dados_cep")
      )
    )

  return StudentProfile(
    name=header.group(1),
    ra=header.group(2),
    login=mask_cpf(login),
    course=CourseRef(code=course_code, name=course_name),
    class_id=class_id,
    series=series,
    section=section,
    room=room,
    current_term=term,
    last_access=parse_datetime(f"{last_access.group(1)} {last_access.group(2)}") if last_access else None,
    contact=Contact(
      email_primary=field("dados_email1") or None,
      email_alternate=field("dados_email2") or None,
      phone_mobile=mask_phone(field("dados_fone_cel")),
      phone_home=mask_phone(field("dados_fone_res")),
      phone_work=mask_phone(field("dados_fone_com"))
    ),
    documents=documents,
    editable_fields_note=EDITABLE_FIELDS_NOTE
  )
