from ..data import BeneficiaryCheck, FinancialStatus, Invoice
from ..server import mcp, portal, READ_ONLY
from ..utils import parse_date, parse_number, require, text

import re

async def fetch_financial_status() -> FinancialStatus:
  soup = await portal.page("frame_ficha_financeira.php")
  # The "TÍTULOS EM ABERTO" heading only exists while an invoice is open, so the always-present bank notice proves we got the right page.
  require(soup.find(string=re.compile("Código do Cedente")))

  invoices = []
  for table in soup.find_all("table"):
    if table.find("table") or "Nosso Número" not in table.get_text():
      continue  # only the innermost table of each invoice

    values = _values_after_labels(table)
    digitable = table.find("td", string=re.compile("Linha Digitável"))
    bank_code = re.search(r"banco(\d+)", str(table.find("img", src=re.compile("banco\\d+")) or ""))

    invoices.append(Invoice(
      installment=values.get("Parcela:", ""),
      due_date=parse_date(values.get("Vencimento:")),
      amount=parse_number(values.get("Valor do Título:")),
      currency="BRL",
      nosso_numero=values.get("Nosso Número:", ""),
      bank=bank_code.group(1) if bank_code else None,
      agency_cedente=values.get("Agência/Código do Cedente:"),
      digitable_line=text(digitable.find_next_sibling("td")) if digitable else None
    ))

  page_text = text(soup)
  bank_name = re.search(r"Banco - (\w+)", page_text)
  code = re.search(r"Código do Banco - (\d+)", page_text)
  agency = re.search(r"Agência - (\d+)", page_text)
  cedente = re.search(r"Código do Cedente - ((?:\d+(?:\s+ou\s+)?)+)", page_text)
  beneficiary = BeneficiaryCheck(
    bank=bank_name.group(1) if bank_name else None,
    bank_code=code.group(1) if code else None,
    agency=agency.group(1) if agency else None,
    cedente_codes=re.findall(r"\d+", cedente.group(1)) if cedente else []
  ) if bank_name or code or agency or cedente else None

  for invoice in invoices:  # the barcode images are named after the bank code; show it with the name
    if invoice.bank and beneficiary and beneficiary.bank:
      invoice.bank = f"{beneficiary.bank} ({invoice.bank})"

  notices = [text(node) for node in soup.find_all(string=re.compile(r"desconsiderar caso tenha sido quitado|parcelas geradas sem registro", re.I))]
  term = re.match(r"(\d{4}-\d)", invoices[0].installment) if invoices else None

  return FinancialStatus(
    term=term.group(1) if term else None,
    open_invoices=invoices,
    beneficiary_check=beneficiary,
    notice=" ".join(n.strip("* ").strip() for n in notices)
  )

def _values_after_labels(table) -> dict[str, str]:
  """Each cell reads 'Label:<br/>value'; pair every label with the text that follows it."""
  strings = [s.strip() for s in table.stripped_strings]
  return {label: strings[i + 1] for i, label in enumerate(strings) if label.endswith(":") and i + 1 < len(strings) and not strings[i + 1].endswith(":")}

@mcp.tool(title="Financial status", tags={"finance"}, annotations=READ_ONLY)
async def get_financial_status() -> FinancialStatus:
  """Open tuition invoices (boletos) of the current semester with due date, amount and barcode line.
  Use it for "what do I owe", "when is my next payment" or to pay an invoice. The result also carries the bank data the official invoices use (beneficiary_check); compare it with any invoice before paying, because the portal warns about fraudulent boletos. Paid history is not included."""
  return await fetch_financial_status()
