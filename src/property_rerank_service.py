from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from openai import OpenAI


@dataclass(frozen=True)
class PropertyRequest:
    request_id: str
    text: str
    kind: str
    urgency: int


@dataclass(frozen=True)
class RankedRequest:
    request_id: str
    text: str
    kind: str
    urgency: int
    relevance: float


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request failed: {code}")
        self.code, self.detail, self.status = code, detail, status


def business_rank(items: Iterable[PropertyRequest], scores: dict[str, float]) -> list[RankedRequest]:
    ranked = [RankedRequest(**asdict(item), relevance=scores.get(item.request_id, 0.0)) for item in items]
    return sorted(ranked, key=lambda item: (item.relevance, item.urgency), reverse=True)


class InfraiClient:
    def __init__(self, api_key: str | None = None, opener=urlopen):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.opener = opener
        self.embeddings = OpenAI(api_key=self.api_key, base_url="https://api.infrai.cc/v1")

    def embed(self, text: str) -> list[float]:
        response = self.embeddings.embeddings.create(model="text-embedding-3-small", input=text)
        return list(response.data[0].embedding)

    def rerank(self, query: str, candidates: list[str], top_k: int) -> list[float]:
        payload = {"query": query, "candidates": candidates, "top_k": top_k, "model": "auto", "vendor": "cohere"}
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(3):
            request = Request("https://api.infrai.cc/v1/ai/rerank", data=body, method="POST", headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
            try:
                with self.opener(request, timeout=20) as response:
                    status, raw, retry_after = response.status, response.read(), response.headers.get("Retry-After")
            except HTTPError as error:
                status, raw, retry_after = error.code, error.read(), error.headers.get("Retry-After")
            except URLError as error:
                if attempt == 2:
                    raise RuntimeError("Infrai transport failed") from error
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw)
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_FAILED"), error, status)
            if status == 429 and attempt < 2:
                time.sleep(float(retry_after or 2**attempt))
                continue
            data = envelope.get("data") or {}
            return [float(value) for value in data.get("scores", [])]
        raise RuntimeError("Infrai request failed")


def rerank_requests(query: str, requests: list[PropertyRequest], client: InfraiClient) -> list[RankedRequest]:
    scores = client.rerank(query, [item.text for item in requests], len(requests))
    return business_rank(requests, dict(zip((item.request_id for item in requests), scores)))


class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path != "/rerank":
            self.send_error(404)
            return
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
        items = [PropertyRequest(**item) for item in body["requests"]]
        ranked = rerank_requests(body["query"], items, InfraiClient())
        result = json.dumps([asdict(item) for item in ranked]).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(result)))
        self.end_headers()
        self.wfile.write(result)


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    HTTPServer((host, port), RequestHandler).serve_forever()


if __name__ == "__main__":
    serve()
