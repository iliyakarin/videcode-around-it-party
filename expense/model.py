from dataclasses import dataclass

@dataclass(frozen=True)
class LineIn:
    date: str | None
    description: str
    amount: object
    paid_with: str | None
    category: str | None

@dataclass(frozen=True)
class NormalizedLine:
    date: str
    description: str
    amount: float | None
    paid_with: str
    category: str
    notes: str
    date_from_message: bool
    outside_october: bool
    amount_missing: bool
