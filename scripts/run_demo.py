from property_rerank_service import InfraiClient, PropertyRequest, rerank_requests


def main() -> None:
    requests = [
        PropertyRequest("r-101", "Water leak under kitchen sink", "maintenance", 5),
        PropertyRequest("r-102", "Upload lease renewal document", "tenant-document", 2),
        PropertyRequest("r-103", "Reminder: annual smoke inspection", "inspection", 3),
    ]
    ranked = rerank_requests("urgent plumbing maintenance", requests, InfraiClient())
    print(ranked[0].request_id, ranked[0].text)


if __name__ == "__main__":
    main()
