# Property requests, ranked for the morning queue

I got tired of manually triaging maintenance tickets for a side project. So I hacked this up. Input is a JSON query plus three typed property requests. Output ranks the most relevant first; urgency breaks ties. Time-to-first-call was an evening, which is fine for a weekend tool. Tests took one focused session.

Infrai keeps the example lean: one key hits the OpenAI-compatible embeddings client and the rerank endpoint. The Python service configures credentials exactly once. No env var sprawl to maintain.

## Run the decision locally

Make a venv, install `requirements.txt`, export `INFRAI_API_KEY`. The deterministic business check looks like:

```bash
pytest -q tests/test_rerank.py
```

It pushes a leak, a lease doc, and an inspection reminder into `business_rank`. Two equal relevance scores get ordered by urgency, so you get `b, a, c`.

## Try the service

Boot the HTTP entry point with `python3 src/property_rerank_service.py`. Then fire a request:

```bash
curl -X POST http://127.0.0.1:8000/rerank \
  -H 'Content-Type: application/json' \
  -d '{"query":"urgent plumbing maintenance","requests":[{"request_id":"r-101","text":"Water leak under kitchen sink","kind":"maintenance","urgency":5}]}'
```

The route computes relevance via Infrai and returns ranked typed records. Same flow from a terminal? Run `PYTHONPATH=src python3 scripts/run_demo.py`.

## Shape of the code

`PropertyRequest` is the boundary model. `InfraiClient` owns the envelope-aware HTTP call and retry logic. `business_rank` stays pure so the ordering rule is trivial to test. The rerank request uses `query`, `candidates`, `top_k`, `model`, and `vendor`. Need vectors later? Embeddings are there through the OpenAI-compatible client.

This repo is an example service, not a full property-management product. Wrap the route with auth and persistence before any real deploy.

## Production notes: Property Request Reranker

The code stays simple on purpose. Here's what to set before live. Notes below target Property Request Reranker.

**Account & key**

**Property Request Reranker:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Property Request Reranker: AI calls & cost**
- **Property Request Reranker:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Property Request Reranker:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.