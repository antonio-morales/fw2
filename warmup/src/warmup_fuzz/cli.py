from __future__ import annotations

import asyncio
import os
import random
import string
from typing import Dict, List, Tuple

import httpx


DEFAULT_HOST: str = "127.0.0.1"
DEFAULT_PORT: int = 80
TCP_CONNECTIONS: int = 10
HTTP_CONNECTIONS: int = 10


def _random_token(min_len: int = 3, max_len: int = 12) -> str:
    length: int = random.randint(min_len, max_len)
    alphabet: str = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def _random_headers(num: int | None = None) -> Dict[str, str]:
    count: int = num if num is not None else random.randint(2, 8)
    headers: Dict[str, str] = {}
    for _ in range(count):
        key: str = f"X-{_random_token(4, 10)}"
        # Ensure no duplicates accidentally overwrite; regenerate if needed
        while key in headers:
            key = f"X-{_random_token(4, 10)}"
        value: str = _random_token(0, 24)
        headers[key] = value
    # Add a few common headers to make requests look more realistic
    headers.setdefault("User-Agent", f"warmup-fuzz/{_random_token(3,6)}")
    headers.setdefault("Accept", "*/*")
    return headers


def _random_path() -> str:
    num_segments: int = random.randint(1, 4)
    segments: List[str] = [_random_token(1, 10) for _ in range(num_segments)]
    return "/" + "/".join(segments)


def _random_query_params() -> Dict[str, str]:
    count: int = random.randint(0, 5)
    return {f"q{idx}": _random_token(0, 16) for idx in range(count)}


def _random_body(max_bytes: int = 16_384) -> bytes:
    size: int = random.randint(0, max_bytes)
    return os.urandom(size)


async def _tcp_random_writer(host: str, port: int, idx: int) -> Tuple[int, Exception | None]:
    pre_sleep: float = random.uniform(0.0, 0.5)
    await asyncio.sleep(pre_sleep)
    total_bytes: int = 0
    try:
        reader, writer = await asyncio.open_connection(host=host, port=port)
        # Send a random amount of data in chunks to keep the socket open a bit
        target_bytes: int = random.randint(1_024, 512_000)
        chunk_size: int = random.choice([256, 512, 1024, 4096, 8192])
        while total_bytes < target_bytes:
            to_send: int = min(chunk_size, target_bytes - total_bytes)
            writer.write(os.urandom(to_send))
            await writer.drain()
            total_bytes += to_send
            # Random tiny delay between chunks
            if random.random() < 0.3:
                await asyncio.sleep(random.uniform(0.0, 0.05))
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass
        return total_bytes, None
    except Exception as exc:  # noqa: BLE001
        return total_bytes, exc


async def _http_random_request(client: httpx.AsyncClient, host: str, port: int, idx: int) -> Tuple[int, int | None, Exception | None]:
    pre_sleep: float = random.uniform(0.0, 0.5)
    await asyncio.sleep(pre_sleep)
    methods: List[str] = [
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "PATCH",
        "HEAD",
        "OPTIONS",
        "TRACE",
    ]
    method: str = random.choice(methods)
    path: str = _random_path()
    params: Dict[str, str] = _random_query_params()
    headers: Dict[str, str] = _random_headers()
    body: bytes = _random_body()
    url: str = f"http://{host}:{port}{path}"
    try:
        resp = await client.request(method=method, url=url, params=params, headers=headers, content=body)
        # Force read content to complete the exchange, but ignore bytes
        _ = resp.status_code
        return len(body), resp.status_code, None
    except Exception as exc:  # noqa: BLE001
        return len(body), None, exc


async def _async_main(host: str, port: int) -> int:
    # Launch TCP writers
    tcp_tasks = [asyncio.create_task(_tcp_random_writer(host, port, i)) for i in range(TCP_CONNECTIONS)]

    # Prepare HTTP client with explicit limits matching desired concurrency
    limits = httpx.Limits(max_connections=HTTP_CONNECTIONS, max_keepalive_connections=HTTP_CONNECTIONS)
    transport = httpx.AsyncHTTPTransport(retries=0)
    async with httpx.AsyncClient(limits=limits, transport=transport, http2=False, timeout=5.0) as client:
        http_tasks = [asyncio.create_task(_http_random_request(client, host, port, i)) for i in range(HTTP_CONNECTIONS)]

        # Run all tasks concurrently
        tcp_results, http_results = await asyncio.gather(
            asyncio.gather(*tcp_tasks, return_exceptions=True),
            asyncio.gather(*http_tasks, return_exceptions=True),
        )

    # Optionally print a brief summary
    tcp_ok = sum(1 for r in tcp_results if isinstance(r, tuple) and r[1] is None)
    http_ok = sum(1 for r in http_results if isinstance(r, tuple) and r[2] is None)
    print(f"TCP writers completed: {tcp_ok}/{TCP_CONNECTIONS}")
    print(f"HTTP requests completed: {http_ok}/{HTTP_CONNECTIONS}")
    return 0


def main() -> None:
    # Simple, fixed target as requested: localhost:80
    exit_code: int = asyncio.run(_async_main(DEFAULT_HOST, DEFAULT_PORT))
    raise SystemExit(exit_code)



