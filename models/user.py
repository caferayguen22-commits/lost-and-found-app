import sqlite3
from dataclasses import dataclass, asdict


@dataclass
class User:
    email: str
    password_hash: str
    id: int | None = None
    created_at: str | None = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "User":
        return cls(**dict(row))

    def to_dict(self) -> dict:
        """Öffentliche Repräsentation. password_hash darf niemals über eine
        API-Antwort nach außen gehen -- deshalb hier zentral ausgeschlossen,
        genau wie secret_feature bei Item."""
        data = asdict(self)
        data.pop("password_hash", None)
        return data
