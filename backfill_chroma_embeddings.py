"""
Einmal-Skript: indiziert alle bereits bestehenden Items nachträglich in Chroma.
Nötig, weil der Vektor-Index erst nach diesem Feature eingeführt wurde --
alte Items wurden beim Anlegen noch nicht embedded. Gefahrlos mehrfach
ausführbar (index_item() ist idempotent, siehe services/vector_store_service.py).
"""
from services.items_repository import get_all_items
from services.vector_store_service import index_item


def backfill():
    items = get_all_items()
    for item in items:
        index_item(item)
    print(f"✅ {len(items)} Items nachträglich in Chroma indiziert.")


if __name__ == "__main__":
    backfill()
