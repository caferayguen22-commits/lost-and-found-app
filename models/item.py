import sqlite3
from dataclasses import dataclass, asdict


@dataclass
class Item:
    type: str
    category: str
    title: str
    description: str
    location: str
    corrected_location: str
    tracking_code: str
    user_hint: str
    match_found: bool = False
    location_lat: float | None = None
    location_lon: float | None = None
    location_postcode: str | None = None
    location_district: str | None = None
    location_road: str | None = None
    location_house_number: str | None = None
    current_location: str | None = None
    email: str | None = None
    image: str | None = None
    matched_item_id: int | None = None
    match_probability: int | None = None
    ai_summary: str | None = None
    recommended_station_id: int | None = None
    recommended_station_distance_km: float | None = None
    secret_feature: str | None = None
    id: int | None = None
    created_at: str | None = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Item":
        data = dict(row)
        data["match_found"] = bool(data["match_found"])
        return cls(**data)

    def to_dict(self) -> dict:
        """Öffentliche Repräsentation für API-Antworten. secret_feature dient
        ausschließlich der späteren serverseitigen Verifizierung und darf
        niemals über eine API-Antwort nach außen gehen -- deshalb hier
        zentral ausgeschlossen, statt sich auf jede aufrufende Route zu
        verlassen."""
        data = asdict(self)
        data.pop("secret_feature", None)
        return data
