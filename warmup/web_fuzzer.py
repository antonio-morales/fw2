#!/usr/bin/env python3
"""Simple web fuzzer.

Usage examples:
  python3 web_fuzzer.py --url "http://localhost:8080/FUZZ"
  python3 web_fuzzer.py --url "http://localhost:8080/search?q=FUZZ" --method GET
  python3 web_fuzzer.py --url "http://localhost:8080/FUZZ" --wordlist warmup/payloads.txt

The string FUZZ in --url is replaced by each payload.
"""

from __future__ import annotations

import argparse
import urllib.error
import urllib.request


DEFAULT_PAYLOADS = [
    "admin",
    "login",
    "test",
    "backup",
    "debug",
    "..%2f..%2fetc%2fpasswd",
    "' OR '1'='1",
    "<script>alert(1)</script>",
    "%27%20OR%201%3D1--",
]


def load_payloads(wordlist_path: str | None) -> list[str]:
    if not wordlist_path:
        return DEFAULT_PAYLOADS

    payloads: list[str] = []
    with open(wordlist_path, "r", encoding="utf-8") as f:
        for line in f:
            candidate = line.strip()
            if candidate and not candidate.startswith("#"):
                payloads.append(candidate)

    return payloads or DEFAULT_PAYLOADS


def send_request(url: str, method: str, timeout: float) -> tuple[int | None, int, str]:
    request = urllib.request.Request(url=url, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            status = response.status
            return status, len(body), "ok"
    except urllib.error.HTTPError as e:
        try:
            body = e.read()
            body_length = len(body)
        except Exception:
            body_length = 0
        return e.code, body_length, f"http_error: {e.reason}"
    except urllib.error.URLError as e:
        return None, 0, f"url_error: {e.reason}"
    except Exception as e:
        return None, 0, f"error: {e}"


def fuzz(target_template: str, payloads: list[str], method: str, timeout: float) -> None:
    print(f"[*] Starting fuzz on template: {target_template}")
    print(f"[*] Payload count: {len(payloads)}")
    print("-" * 80)
    print(f"{'status':<8} {'size':<8} {'payload':<30} note")
    print("-" * 80)

    for payload in payloads:
        url = target_template.replace("FUZZ", payload)
        status, size, note = send_request(url=url, method=method, timeout=timeout)
        status_text = str(status) if status is not None else "ERR"
        print(f"{status_text:<8} {size:<8} {payload[:30]:<30} {note}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simple web fuzzer")
    parser.add_argument(
        "--url",
        required=True,
        help="Target URL template containing FUZZ placeholder",
    )
    parser.add_argument(
        "--method",
        default="GET",
        choices=["GET", "HEAD"],
        help="HTTP method (default: GET)",
    )
    parser.add_argument(
        "--wordlist",
        default=None,
        help="Optional wordlist file (one payload per line)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=3.0,
        help="Request timeout in seconds (default: 3.0)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if "FUZZ" not in args.url:
        raise SystemExit("--url must include FUZZ placeholder")

    payloads = load_payloads(args.wordlist)
    fuzz(target_template=args.url, payloads=payloads, method=args.method, timeout=args.timeout)


if __name__ == "__main__":
    main()
