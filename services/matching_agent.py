import json
from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from services.vector_store_service import find_similar_candidates
from services.items_repository import get_item_by_id
from services.prompt_service import build_found_prompt, build_lost_prompt

# Startwerte -- der Schwellwert wird beim End-to-End-Test mit echten
# Embeddings kalibriert (siehe lernnotizen.md), nicht blind geraten.
SIMILARITY_THRESHOLD = 0.55
INITIAL_K = 5
WIDENED_K = 10
MAX_ATTEMPTS = 2

_chat_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.5, timeout=15.0).bind(
    response_format={"type": "json_object"}
)


class MatchingState(TypedDict):
    item_type: str
    opposite_type: str
    category: str
    title: str
    description: str
    corrected_location: str
    current_location: str | None
    k: int
    require_category: bool
    attempt: int
    candidates: list[dict]
    result: dict


def _retrieve_node(state: MatchingState) -> dict:
    candidates = find_similar_candidates(
        opposite_type=state["opposite_type"],
        category=state["category"],
        title=state["title"],
        description=state["description"],
        k=state["k"],
        require_category=state["require_category"],
    )
    return {"candidates": candidates}


def _decide_after_retrieve(state: MatchingState) -> str:
    """
    Rein algorithmische Bewertung (kein zusätzlicher KI-Aufruf) -- Chromas
    Ähnlichkeits-Score liefert dieses Signal kostenlos mit. Eigenständig für
    UNSEREN Anwendungsfall entwickelte Retry-Strategie (siehe lernnotizen.md),
    nicht 1:1 aus generischem Dokumenten-RAG übernommen:
      1. Versuch schwach -> breiter suchen (mehr Kandidaten, k erhöhen)
      2. immer noch schwach -> Kategorie-Filter fallen lassen (falsche
         Kategorie gewählt?)
      danach: mit dem Besten weitermachen -- feste Obergrenze gegen
      Endlosschleifen.
    """
    best_similarity = max((c["similarity"] for c in state["candidates"]), default=0.0)
    if best_similarity >= SIMILARITY_THRESHOLD:
        return "finalize"
    if state["attempt"] >= MAX_ATTEMPTS:
        return "finalize"
    return "refine"


def _refine_node(state: MatchingState) -> dict:
    attempt = state["attempt"] + 1
    if attempt == 1:
        return {"attempt": attempt, "k": WIDENED_K}
    return {"attempt": attempt, "require_category": False}


def _finalize_node(state: MatchingState) -> dict:
    other_items_list = []
    for candidate in state["candidates"]:
        item = get_item_by_id(candidate["item_id"])
        if item:
            other_items_list.append({
                "id": item.id,
                "title": item.title,
                "description": item.description,
                "location": item.corrected_location or item.location,
            })

    if state["item_type"] == "found":
        system_message, prompt = build_found_prompt(
            category=state["category"],
            title=state["title"],
            description=state["description"],
            corrected_location=state["corrected_location"],
            current_location=state["current_location"],
            other_items_list=other_items_list,
        )
    else:
        system_message, prompt = build_lost_prompt(
            category=state["category"],
            title=state["title"],
            description=state["description"],
            corrected_location=state["corrected_location"],
            other_items_list=other_items_list,
        )

    response = _chat_model.invoke([
        SystemMessage(content=system_message),
        HumanMessage(content=prompt),
    ])
    parsed = json.loads(response.content)
    # Kandidaten-IDs mitgeben, damit api/items_routes.py weiterhin die
    # Output-Validierung aus dem Prompt-Injection-Schutz (Schicht 3)
    # durchführen kann -- matched_item_id wird dort nur akzeptiert, wenn sie
    # tatsächlich unter DIESEN angebotenen Kandidaten war.
    parsed["_offered_candidate_ids"] = [c["id"] for c in other_items_list]
    return {"result": parsed}


def _build_graph():
    graph = StateGraph(MatchingState)
    graph.add_node("retrieve", _retrieve_node)
    graph.add_node("refine", _refine_node)
    graph.add_node("finalize", _finalize_node)

    graph.add_edge(START, "retrieve")
    graph.add_conditional_edges("retrieve", _decide_after_retrieve, {"finalize": "finalize", "refine": "refine"})
    graph.add_edge("refine", "retrieve")
    graph.add_edge("finalize", END)

    return graph.compile()


_compiled_graph = _build_graph()


def run_matching(item_type: str, category: str, title: str, description: str,
                  corrected_location: str, current_location: str | None = None) -> dict:
    """
    Öffentlicher Einstiegspunkt -- ersetzt den bisherigen direkten
    build_found_prompt()/build_lost_prompt() + openai_client-Aufruf in
    api/items_routes.py mit dem agentischen Retrieve->Grade->(Refine)->
    Finalize-Ablauf. Gibt dieselbe Dict-Form zurück wie zuvor (summary,
    match_found, matched_item_id, match_probability, corrected_description)
    plus _offered_candidate_ids für die Output-Validierung.
    """
    opposite_type = "lost" if item_type == "found" else "found"
    initial_state: MatchingState = {
        "item_type": item_type,
        "opposite_type": opposite_type,
        "category": category,
        "title": title,
        "description": description,
        "corrected_location": corrected_location,
        "current_location": current_location,
        "k": INITIAL_K,
        "require_category": True,
        "attempt": 0,
        "candidates": [],
        "result": {},
    }
    final_state = _compiled_graph.invoke(initial_state)
    return final_state["result"]
