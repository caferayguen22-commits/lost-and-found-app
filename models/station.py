import sqlite3
from dataclasses import dataclass, asdict


@dataclass
class Station:
    name: str
    type: str
    address: str
    district: str
    serves_category: str
    note: str | None = None
    lat: float | None = None
    lon: float | None = None
    id: int | None = None  # None vor dem Insert, danach von SQLite vergeben

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Station":
        return cls(**dict(row))

    def to_dict(self) -> dict:
        return asdict(self)
