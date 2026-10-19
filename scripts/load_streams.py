"""Synthetic concurrent SSE load with percentile reporting.

Runs against a declared environment. Use a test account with enough quota.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
import uuid
from collections import Counter

import httpx


async def one_stream(
    client: httpx.AsyncClient, base: str, index: int, headers: dict[str, str]
) -> dict:
    payload = {
        "client_message_id": str(uuid.uuid4()),
        "conversation_id": f"load-{index}",
        "mode": "conversation",
        "message": "Mensagem sintética de carga.",
        "locale": "pt-BR",
        "timezone": "UTC",
        "context": {"records": []},
    }
    started = time.perf_counter()
    first = None
    text_chars = 0
    try:
        async with client.stream(
            "POST",
            f"{base}/v1/ai/responses",
            headers={**headers, "Idempotency-Key": f"load-{uuid.uuid4()}"},
            json=payload,
        ) as response:
            if response.status_code != 200:
                await response.aread()
                return {"status": response.status_code, "ttfb": None, "total": None, "chars": 0}
            event = ""
            async for line in response.aiter_lines():
                if line.startswith("event: "):
                    event = line[7:]
                elif line.startswith("data: ") and event == "text_delta":
                    if first is None:
                        first = time.perf_counter() - started
                    text_chars += len(json.loads(line[6:]).get("text", ""))
                if event == "completed":
                    break
        return {
            "status": 200,
            "ttfb": first,
            "total": time.perf_counter() - started,
            "chars": text_chars,
        }
    except Exception:
        return {"status": 0, "ttfb": None, "total": None, "chars": 0}


def percentile(values: list[float], factor: float) -> float:
    """Nearest-rank percentile."""
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, round(factor * (len(ordered) - 1)))
    return ordered[index]


async def run(args) -> None:
    async with httpx.AsyncClient(base_url=args.identity, timeout=30) as client:
        login = await client.post(
            "/v1/auth/login",
            json={
                "email": args.email,
                "password": args.password,
                "device_id": str(uuid.uuid4()),
                "platform": "android",
            },
        )
        login.raise_for_status()
        tokens = login.json()
        headers = {
            "Authorization": f"Bearer {tokens['access_token']}",
            "X-Session-Source": tokens["source"],
        }
        if args.purchase_token:
            purchase = await client.post(
                "/v1/billing/purchases/verify",
                headers=headers,
                json={"product_id": args.product_id, "purchase_token": args.purchase_token},
            )
            print("purchase", purchase.status_code)
    targets = [value.strip().rstrip("/") for value in args.conversation.split(",") if value.strip()]
    async with httpx.AsyncClient(timeout=180) as client:
        started = time.perf_counter()
        results = await asyncio.gather(
            *(
                one_stream(client, targets[index % len(targets)], index, headers)
                for index in range(args.streams)
            )
        )
        elapsed = time.perf_counter() - started
    status_counts = Counter(item["status"] for item in results)
    ok = [item for item in results if item["status"] == 200]
    ttfb = [item["ttfb"] for item in ok if item["ttfb"] is not None]
    total = [item["total"] for item in ok if item["total"] is not None]
    print(
        json.dumps(
            {
                "streams": args.streams,
                "targets": targets,
                "ok": len(ok),
                "errors": len(results) - len(ok),
                "status_counts": dict(status_counts),
                "wall_seconds": round(elapsed, 2),
                "throughput_per_second": round(len(ok) / elapsed, 2),
                "ttfb_p50": round(percentile(ttfb, 0.5), 3),
                "ttfb_p95": round(percentile(ttfb, 0.95), 3),
                "ttfb_p99": round(percentile(ttfb, 0.99), 3),
                "total_p50": round(percentile(total, 0.5), 3),
                "total_p95": round(percentile(total, 0.95), 3),
                "chars_mean": round(statistics.mean(item["chars"] for item in ok) if ok else 0, 1),
            },
            ensure_ascii=False,
        )
    )


def main() -> None:
    """Parse options and run the scenario."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--streams", type=int, default=100)
    parser.add_argument("--identity", default="http://localhost:8001")
    parser.add_argument("--conversation", default="http://localhost:8010")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--purchase-token", default="")
    parser.add_argument("--product-id", default="diary_pro_monthly")
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
