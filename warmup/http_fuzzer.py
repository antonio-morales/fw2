#!/usr/bin/env python3
"""
Simple HTTP Fuzzer — Fuzzing Workshop Warmup
Sends fuzz-generated HTTP requests to a target and flags interesting responses.
"""

import sys
import string
import random
import urllib.request
import urllib.error
import urllib.parse
import argparse

# Interesting payloads to mutate from
SEED_PATHS = ["/", "/index", "/admin", "/search", "/api/v1/users"]
SEED_PARAMS = {"q": "hello", "id": "1", "name": "test", "page": "1"}
INTERESTING_CHARS = list("\"'<>;{}[]|\\^`\x00\x0a\x0d\xff")
METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD", "TRACE"]

def mutate_string(s: str, data: bytes) -> str:
    """Lightly mutate a string using fuzz bytes as a seed."""
    if not data:
        return s
    chars = list(s) if s else list("x")
    for b in data[:8]:
        op = b % 4
        pos = b % len(chars) if chars else 0
        if op == 0 and chars:
            chars[pos] = chr(b % 128)
        elif op == 1:
            chars.insert(pos, random.choice(INTERESTING_CHARS))
        elif op == 2 and len(chars) > 1:
            chars.pop(pos)
        else:
            chars.append(chr(b % 128))
    return "".join(chars)


def build_request(target: str, data: bytes) -> tuple[str, str, dict, bytes | None]:
    """Derive an HTTP request from fuzz data."""
    if len(data) < 4:
        return target + "/", "GET", {}, None

    method = METHODS[data[0] % len(METHODS)]

    seed_path = SEED_PATHS[data[1] % len(SEED_PATHS)]
    path = mutate_string(seed_path, data[2:10])
    url = target.rstrip("/") + "/" + path.lstrip("/")

    # Optionally append a fuzzed query string
    if data[2] % 2 == 0:
        param_key = list(SEED_PARAMS.keys())[data[3] % len(SEED_PARAMS)]
        param_val = mutate_string(SEED_PARAMS[param_key], data[4:12])
        url += "?" + urllib.parse.urlencode({param_key: param_val})

    headers = {"User-Agent": "fw4-warmup-fuzzer/1.0"}

    body = None
    if method in ("POST", "PUT", "PATCH") and len(data) > 12:
        body = data[12:]
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        headers["Content-Length"] = str(len(body))

    return url, method, headers, body


def send_request(url: str, method: str, headers: dict, body: bytes | None, timeout: int) -> tuple[int, int]:
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, len(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, 0
    except Exception:
        return 0, 0


def is_interesting(status: int) -> bool:
    return status in (500, 502, 503) or status == 0


def fuzz_random(target: str, iterations: int, timeout: int, seed: int | None) -> None:
    rng = random.Random(seed)
    found: list[tuple[str, str, int]] = []

    print(f"[*] Target : {target}")
    print(f"[*] Iterations: {iterations}  seed={seed}")
    print()

    for i in range(iterations):
        data = bytes(rng.getrandbits(8) for _ in range(32))
        url, method, headers, body = build_request(target, data)
        status, length = send_request(url, method, headers, body, timeout)

        marker = "!" if is_interesting(status) else " "
        print(f"[{marker}] #{i+1:4d}  {method:7s}  {status}  {length:6d}b  {url}")

        if is_interesting(status):
            found.append((method, url, status))

    print()
    if found:
        print(f"[!] {len(found)} interesting response(s):")
        for method, url, status in found:
            print(f"    {status}  {method}  {url}")
    else:
        print("[*] No server errors found.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple HTTP fuzzer — fw4 warmup")
    parser.add_argument("target", help="Base URL to fuzz (e.g. http://localhost:8080)")
    parser.add_argument("-n", "--iterations", type=int, default=50,
                        help="Number of requests to send (default: 50)")
    parser.add_argument("-t", "--timeout", type=int, default=5,
                        help="Request timeout in seconds (default: 5)")
    parser.add_argument("-s", "--seed", type=int, default=None,
                        help="Random seed for reproducibility")
    args = parser.parse_args()

    fuzz_random(args.target, args.iterations, args.timeout, args.seed)


if __name__ == "__main__":
    main()
