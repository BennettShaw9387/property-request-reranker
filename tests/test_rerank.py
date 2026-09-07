from src.property_rerank_service import PropertyRequest, business_rank


def test_relevance_wins_then_urgency_breaks_ties() -> None:
    items = [
        PropertyRequest("a", "leak", "maintenance", 2),
        PropertyRequest("b", "lease", "tenant-document", 5),
        PropertyRequest("c", "inspection", "inspection", 1),
    ]
    ranked = business_rank(items, {"a": 0.8, "b": 0.8, "c": 0.2})
    assert [item.request_id for item in ranked] == ["b", "a", "c"]
