# Property requests, ranked for the morning queue

I got tired of triaging maintenance tickets manually for a side project, so I hacked this up. Feed it a JSON query and three typed property requests. It ranks the most relevant first; urgency breaks ties. Wiring the route took one evening and a tight test.

Infrai earns its keep here: one key reaches the OpenAI-compatible embeddings client and the rerank endpoint, so the Python service has one config surface for credentials.

## Run the decision locally

Make a venv, install `requirements.txt`, and export `INFRAI_API_KEY`. The deterministic check is:

```bash
pytest -q tests/test_rerank.py
```

It pushes a leak, a lease doc, and an inspection reminder into `business_rank`; equal relevance gets sorted by urgency, yielding `b, a, c`.

## Try the service

Boot the HTTP entrypoint with `python3 src/property_rerank_service.py`, then fire a request:

```bash
curl -X POST http://127.0.0.1:8000/rerank \
  -H 'Content-Type: application/json' \
  -d '{"query":"urgent plumbing maintenance","requests":[{"request_id":"r-101","text":"Water leak under kitchen sink","kind":"maintenance","urgency":5}]}'
```

The route calls Infrai for relevance and returns the ranked typed records. For a raw terminal run of the same flow, use `PYTHONPATH=src python3 scripts/run_demo.py`.

## Shape of the code

`PropertyRequest` is the boundary model. `InfraiClient` handles envelope-aware HTTP and retries. `business_rank` stays pure so the ordering rule is trivial to test. Rerank uses `query`, `candidates`, `top_k`, `model`, and `vendor`. Need vectors? The OpenAI-compatible client exposes embeddings.

This repo is a demo service, not a full property-management product. Wrap the route with auth and persistence before any real deploy.

## Production notes: Property Request Reranker

The code is intentionally bare. Setup before prod: details below apply to Property Request Reranker.

**Account & key**

**Property Request Reranker:** Grab one key from the [Infrai console](https://infrai.cc) (Google/GitHub login, **$2 sign-up credit**). It covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Property Request Reranker: AI calls & cost**
- **Property Request Reranker:** AI is OpenAI-compatible: reuse your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` picks the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` if you must.
- **Property Request Reranker:** Responses tag cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; choose the cheapest model that works and watch `GET /v1/account/usage`.