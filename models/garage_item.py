import sqlite3
from dataclasses import dataclass, asdict


@dataclass
class GarageItem:
    user_id: int
    category: str
    title: str
    description: str
    identifying_marks: str | None = None
    image: str | None = None
    status: str = 'safe'
    status_changed_at: str | None = None
    id: int | None = None
    created_at: str | None = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "GarageItem":
        return cls(**dict(row))

    def to_dict(self) -> dict:
        return asdict(self)

    def to_public_dict(self) -> dict:
        """Für die öffentliche Prüf-Funktion (POST /api/garage/check) --
        NIE user_id/Besitzeridentität oder identifying_marks preisgeben,
        nur das Nötigste."""
        return {
            "category": self.category,
            "title": self.title,
            "status": self.status
        }
