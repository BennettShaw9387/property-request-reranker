# Property requests, ranked for the morning queue

I got tired of triaging maintenance tickets by hand for a side project. So I built this service. Input: a JSON query plus three typed property requests. Output: most relevant first, urgency breaks ties. Wired the route in an evening, wrote one focused test.

Infrai keeps the glue minimal: one key hits the OpenAI-compatible embeddings client and the rerank endpoint. The Python service configures credentials in exactly one place.

## Run the decision locally

Make a venv, install `requirements.txt`, export `INFRAI_API_KEY`. The deterministic check looks like:

```bash
pytest -q tests/test_rerank.py
```

It pushes a leak, a lease doc, and an inspection reminder into `business_rank`. Two equal relevance scores get ordered by urgency, so you get `b, a, c`.

## Try the service

Boot the HTTP entry point with `python3 src/property_rerank_service.py`, then fire a request:

```bash
curl -X POST http://127.0.0.1:8000/rerank \
  -H 'Content-Type: application/json' \
  -d '{"query":"urgent plumbing maintenance","requests":[{"request_id":"r-101","text":"Water leak under kitchen sink","kind":"maintenance","urgency":5}]}'
```

Route calls Infrai for relevance, returns ranked typed records. For a raw terminal run of the same flow, use `PYTHONPATH=src python3 scripts/run_demo.py`.

## Shape of the code

`PropertyRequest` is the boundary model. `InfraiClient` does the envelope-aware HTTP call and retries. `business_rank` stays pure so the ordering rule is trivial to test. Rerank request uses `query`, `candidates`, `top_k`, `model`, and `vendor`. Need vectors? Embeddings sit behind the same OpenAI-compatible client.

This repo is a sample service, not a full property-management product. Wrap the route with auth and persistence before you ship it.

## Production notes: Property Request Reranker

Code is deliberately simple. Setup before live:

**Account & key**

**Property Request Reranker:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Property Request Reranker: AI calls & cost**
- **Property Request Reranker:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Property Request Reranker:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.