from dataclasses import dataclass

@dataclass
class Invoice:
  installment: str
  due_date: str | None
  amount: float | None
  currency: str
  nosso_numero: str
  bank: str | None
  agency_cedente: str | None
  digitable_line: str | None

@dataclass
class BeneficiaryCheck:
  bank: str | None
  bank_code: str | None
  agency: str | None
  cedente_codes: list[str]

@dataclass
class FinancialStatus:
  term: str | None
  open_invoices: list[Invoice]
  beneficiary_check: BeneficiaryCheck | None
  notice: str

@dataclass
class SecretariaRequest:
  number: str
  type_code: str
  type: str
  requested_at: str | None

@dataclass
class SecretariaRequestList:
  pending: list[SecretariaRequest]
  in_progress: list[SecretariaRequest]
  finished: list[SecretariaRequest]

@dataclass
class ComplementaryCourse:
  code: str
  name: str

@dataclass
class ComplementaryActivity:
  category: str
  term: str
  period: str | None
  hours: int
  status: str  # approved | rejected | pending
  portal_status: str
  note: str | None
  proof_url: str | None
  assigned_to_course: ComplementaryCourse | None

@dataclass
class ComplementaryCategory:
  id: str
  name: str

@dataclass
class SubmissionWindow:
  starts_at: str | None
  ends_at: str | None

@dataclass
class ComplementaryHours:
  submission_window: SubmissionWindow
  total_records: int
  approved_hours: int
  activities: list[ComplementaryActivity]
  categories: list[ComplementaryCategory] | None
