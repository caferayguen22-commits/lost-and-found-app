import sqlite3
from dataclasses import dataclass, asdict


@dataclass
class ClaimAttempt:
    item_id: int
    success: bool
    claimant_email: str | None = None
    id: int | None = None
    attempted_at: str | None = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "ClaimAttempt":
        data = dict(row)
        data["success"] = bool(data["success"])
        return cls(**data)

    def to_dict(self) -> dict:
        return asdict(self)
