from typing import Annotated

from pydantic import Field

from ..data import Survey, SurveyList
from ..server import mcp, portal, READ_ONLY
from ..utils import require, text

import re

def _survey(row) -> Survey:
  """One row: 'Pesquisa / [Professor / Disciplina /] Curso / Turma / Aplicado por' labels plus a receipt form when answered."""
  fields = {text(label).rstrip(": "): (label.next_sibling or "").strip() for label in row.find_all("a", class_="aviso_titulo")}
  receipt = row.find("input", attrs={"name": "cpa"})

  return Survey(
    id=receipt["value"] if receipt else None,
    name=require(fields.get("Pesquisa")),
    course=fields.get("Curso"),
    class_id=fields.get("Turma"),
    professor=fields.get("Professor"),
    discipline=fields.get("Disciplina"),
    applied_by=fields.get("Aplicado por"),
    participated="Participação Não Registrada" not in text(row)
  )

@mcp.tool(title="CPA surveys", tags={"communication", "surveys"}, annotations=READ_ONLY)
async def list_surveys(
  term: Annotated[str | None, Field(pattern=r"^\d{4}-[12]$", description="Term such as '2026-1'. Defaults to the current term")] = None
) -> SurveyList:
  """List the institutional surveys (CPA Pesquisas / Enquetes) assigned to the student in a term, and whether each one was answered.

  Each answered CPA survey counts as 1 complementary hour. The message field carries the portal's note when no survey is open right now. Answering a survey is not possible through this tool."""

  params = {"ano3": term[:4], "sem3": term[-1]} if term else {}
  soup = await portal.page("frame_avisos.php", enquetes="X", **params)

  rows = soup.find_all("tr", class_=re.compile(r"^Linha(Impar|Par)$"))
  surveys = [_survey(row) for row in rows if row.find("a", class_="aviso_titulo", string=re.compile("Pesquisa"))]
  message = soup.find("td", colspan="6", string=re.compile("Nenhuma pesquisa"))

  return SurveyList(
    term=term or require(re.search(r"Período \[(\d{4}-\d)\]", text(soup))).group(1),
    total=len(surveys),
    participated=sum(s.participated for s in surveys),
    surveys=surveys,
    message=text(message) or None
  )
