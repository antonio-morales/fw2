"""Warm-up helpers for crafting creative fuzzing inputs.

This module borrows ideas from the workshop exercises in the repository and
wraps them into a single helper: `creative_fuzzy_inputs`.  The helper generates
inputs that mix booking-form records, Moment.js format strings, and
Markdown/HTML fragments so you can quickly seed a fuzzer with material that
resembles the motivating examples from the exercises.
"""
from __future__ import annotations

import random
import socket
import string
import time
from typing import Callable, List, Sequence


# The base line from exercise1/corpus/input.txt split into fields we can mutate.
_BOOKING_BASE_FIELDS: Sequence[str] = (
    "Antonio",
    "Morales",
    "antonio-morales@github.com",
    "single",
    "1",
    "2025-05-21T21:48",
    "2025 05 23",
    "false",
    "",
)

# A collection of Moment.js specifiers that show up in the workshop deck.
_MOMENT_DIRECTIVES: Sequence[str] = (
    "YYYY",
    "YY",
    "Q",
    "M",
    "MM",
    "MMM",
    "MMMM",
    "D",
    "DD",
    "Do",
    "DDD",
    "DDDD",
    "H",
    "HH",
    "h",
    "hh",
    "a",
    "A",
    "m",
    "mm",
    "s",
    "ss",
    "SSS",
    "Z",
    "ZZ",
    "X",
    "x",
)

# Snippets inspired by the markdown/HTML interplay from exercise3.
_MARKDOWN_SNIPPETS: Sequence[str] = (
    "# Heading \n",
    "*bold*",
    "_italic_",
    "`inline-code`",
    "[link](javascript:alert('x'))",
    "<script src='data:x'></script>",
    "<img src=x onerror=alert(1)>",
    "<div class=\"cta\" data-label='promo'>",
    "<a href=\"/book?date=%%DATE%%\">Book</a>",
    "| col1 | col2 |\n| --- | --- |",
)

_LITERAL_TOKENS: Sequence[str] = (
    "booking",
    "{user}",
    "TZ",
    "room42",
    "edge-case",
    "\u2028",  # line separator often mishandled
    "'quote",
    '"double-quote',
)

_HTTP_METHODS: Sequence[str] = (
    "GET",
    "POST",
    "PUT",
    "DELETE",
    "PATCH",
    "OPTIONS",
    "TRACE",
    "CONNECT",
    "PROPFIND",
    "MKCOL",
)

_HTTP_VERSIONS: Sequence[str] = (
    "HTTP/1.1",
    "HTTP/1.0",
    "HTTP/0.9",
    "HTTP/2",
    "HTP/1.1",
    "HTTP/1.1 FUZZ",
)

_HTTP_HEADER_NAMES: Sequence[str] = (
    "User-Agent",
    "Accept",
    "Accept-Encoding",
    "Accept-Language",
    "Content-Type",
    "Cache-Control",
    "Pragma",
    "Upgrade",
    "Referer",
    "Origin",
    "X-Requested-With",
    "X-Forwarded-For",
    "X-Forwarded-Proto",
    "If-None-Match",
    "If-Modified-Since",
    "Range",
    "Cookie",
    "Authorization",
    "Forwarded",
    "TE",
    "DNT",
    "Via",
)

_HEADER_VALUE_TOKENS: Sequence[str] = (
    "gzip, deflate",
    "br",
    "identity",
    "chunked",
    "keep-alive",
    "max-age=0",
    "no-cache",
    "0",
    "application/json",
    "text/html; charset=utf-8",
    "multipart/form-data; boundary=----fuzz",
    "Basic ZmRzOnRlc3Q=",
    "%0d%0acrash",
)

_PATH_TOKENS: Sequence[str] = (
    "",
    "api",
    "v1",
    "v2",
    "booking",
    "admin",
    "../../etc/passwd",
    "%2e%2e",
    "healthz",
    "assets",
    "%%PAYLOAD%%",
    "{id}",
    "~user",
    "\\u0000",
)

_QUERY_KEYS: Sequence[str] = (
    "id",
    "date",
    "token",
    "redirect",
    "format",
    "chunk",
    "range",
    "debug",
    "session",
)

_BODY_METHODS = {"POST", "PUT", "PATCH", "PROPFIND", "MKCOL"}

_HEADER_CHARS = string.ascii_letters + string.digits + "-_/.,;=:%[]"


Mutator = Callable[[random.Random], str]


def creative_fuzzy_inputs(
    count: int = 32,
    *,
    seed: int | None = None,
    as_bytes: bool = True,
) -> List[str | bytes]:
    """Return a batch of mutated inputs inspired by the workshop exercises.

    Args:
        count: How many payloads to produce.
        seed: Optional deterministic seed for the RNG.
        as_bytes: When True (default), encode each payload as UTF-8 bytes.

    Returns:
        A list containing either strings or bytes depending on *as_bytes*.
    """

    rng = random.Random(seed)
    strategies: Sequence[Mutator] = (
        _mutate_booking_record,
        _moment_format_string,
        _markdown_fragment,
        _hybrid_payload,
    )

    payloads: List[str | bytes] = []
    for _ in range(max(0, count)):
        payload = rng.choice(strategies)(rng)
        if as_bytes:
            payloads.append(payload.encode("utf-8", errors="ignore"))
        else:
            payloads.append(payload)
    return payloads


def _mutate_booking_record(rng: random.Random) -> str:
    fields = list(_BOOKING_BASE_FIELDS)

    # Introduce small field-level perturbations.
    for idx, value in enumerate(fields):
        if not value:
            continue
        action = rng.random()
        if action < 0.2:
            fields[idx] = value.upper()
        elif action < 0.4:
            fields[idx] = value[::-1]
        elif action < 0.6:
            glitch = rng.choice(("", "'", '"', "\\"))
            fields[idx] = value + glitch * rng.randint(1, 3)
        elif action < 0.8:
            fields[idx] = value.replace("-", rng.choice(("/", " ", "_")))
        else:
            fields[idx] = _shuffle_subcomponents(value, rng)

    if rng.random() < 0.35:
        rng.shuffle(fields)

    separator = rng.choice((";", ",", "|", "::", "\t"))
    trailer = rng.choice(("", separator, "\n"))
    if rng.random() < 0.25:
        fields.insert(rng.randrange(len(fields) + 1), "")
    return separator.join(fields) + trailer


def _moment_format_string(rng: random.Random) -> str:
    parts: List[str] = []
    length = rng.randint(3, 10)
    for _ in range(length):
        if rng.random() < 0.3:
            literal = rng.choice(_LITERAL_TOKENS)
            parts.append(f"[{literal}]")
        else:
            directive = rng.choice(_MOMENT_DIRECTIVES)
            if rng.random() < 0.15:
                directive = directive.lower()
            if rng.random() < 0.2:
                directive = directive + rng.choice(("::::", "'", '"'))
            parts.append(directive)
    return rng.choice((" ", "-", "|", "")).join(parts)


def _markdown_fragment(rng: random.Random) -> str:
    segments: List[str] = []
    for _ in range(rng.randint(2, 6)):
        seg = rng.choice(_MARKDOWN_SNIPPETS)
        if "%%DATE%%" in seg:
            seg = seg.replace("%%DATE%%", rng.choice(_MOMENT_DIRECTIVES))
        if rng.random() < 0.4:
            seg += rng.choice(("\n", "\r\n"))
        segments.append(seg)

    if rng.random() < 0.3:
        balancer = rng.choice(("**", "__", "~~"))
        segments = [balancer + segments[0]] + segments[1:] + [balancer]

    if rng.random() < 0.2:
        segments.insert(0, "<!-- fuzz: \u2622 -->\n")
    return "".join(segments)


def _hybrid_payload(rng: random.Random) -> str:
    # Splice pieces from the other strategies to build layered inputs.
    booking = _mutate_booking_record(rng)
    fmt = _moment_format_string(rng)
    markdown = _markdown_fragment(rng)
    pieces = (
        f"FORM={booking}",
        f"FMT={fmt}",
        "BODY=\n" + markdown,
    )
    glue = rng.choice(("\u0000", "\u0001", "\n---\n", "\x1f"))
    return glue.join(pieces)


def _shuffle_subcomponents(value: str, rng: random.Random) -> str:
    chunks = value.replace("T", " ").replace("-", " ").replace(":", " ").split()
    if len(chunks) < 2:
        return value
    rng.shuffle(chunks)
    punct = rng.choice(("-", "/", "::", ""))
    return punct.join(chunks)


def fuzz_http_server(
    host: str,
    port: int,
    *,
    rounds: int = 1024,
    seed: int | None = None,
    timeout: float = 0.5,
    delay: float = 0.0,
    persistent: bool = False,
    verbose: bool = False,
) -> dict[str, int]:
    """Spray mutated HTTP requests at *host*:*port* in an attempt to crash it."""

    rng = random.Random(seed)
    stats = {"attempts": 0, "sent": 0, "errors": 0}
    sock: socket.socket | None = None

    try:
        for attempt in range(max(0, rounds)):
            payload, cutoff, linger = _build_http_request(rng)
            stats["attempts"] += 1

            try:
                if sock is None:
                    sock = socket.create_connection((host, port), timeout=timeout)
                    sock.settimeout(timeout)

                _stream_request(sock, payload, cutoff, rng)
                stats["sent"] += 1

                if linger:
                    _drain_socket(sock, rng, timeout)

                if not persistent or rng.random() < 0.25:
                    sock.close()
                    sock = None

            except OSError as exc:
                stats["errors"] += 1
                if verbose:
                    print(f"[{attempt:05d}] transport failure: {exc}")
                if sock is not None:
                    try:
                        sock.close()
                    except OSError:
                        pass
                    sock = None

            if delay:
                time.sleep(max(0.0, delay))

    finally:
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass

    return stats


def _build_http_request(rng: random.Random) -> tuple[bytes, int, bool]:
    method = rng.choice(_HTTP_METHODS)
    if rng.random() < 0.35:
        method = _mutate_token(method, rng)

    path = _fuzz_path(rng)
    version = rng.choice(_HTTP_VERSIONS)
    request_line = f"{method} {path} {version}\r\n"

    headers: List[tuple[str, str]] = []
    if rng.random() < 0.85:
        headers.append(("Host", _fuzz_host(rng)))

    for _ in range(rng.randint(0, 8)):
        name = _mutate_token(rng.choice(_HTTP_HEADER_NAMES), rng)
        headers.append((name, _fuzz_header_value(rng)))
        if rng.random() < 0.15:
            headers.append((name, _fuzz_header_value(rng)))

    include_body = method in _BODY_METHODS or rng.random() < 0.35
    body = _build_body_payload(rng) if include_body else b""
    use_chunked = include_body and rng.random() < 0.25

    transmitted = body
    if use_chunked:
        headers.append(("Transfer-Encoding", rng.choice(("chunked", "Chunked", "gzip, chunked"))))
        transmitted = _encode_chunked_body(body, rng)

    declare_length = include_body and (not use_chunked or rng.random() < 0.5)
    if declare_length:
        declared = len(transmitted)
        if rng.random() < 0.6:
            declared = max(0, declared + rng.randint(-min(declared, 32), 64))
        headers.append(("Content-Length", str(declared)))

    if rng.random() < 0.4:
        headers.append(("Connection", rng.choice(("keep-alive", "close", "upgrade", "keepalive, timeout=5"))))
    if rng.random() < 0.2:
        headers.append(("Expect", rng.choice(("100-continue", "fail", "100-Continue"))))

    header_block = "".join(f"{name}: {value}\r\n" for name, value in headers)
    terminator = "\r\n"
    if rng.random() < 0.2:
        terminator = rng.choice(("\n", "\r", "", "\r\n\r"))

    head = (request_line + header_block + terminator).encode("latin-1", "ignore")
    request = head + transmitted

    cutoff = len(request)
    if transmitted and rng.random() < 0.6:
        cutoff = len(head) + rng.randint(0, len(transmitted))
    elif rng.random() < 0.1 and cutoff:
        cutoff = rng.randint(1, cutoff)

    linger = rng.random() < 0.5
    return request, max(1, cutoff), linger


def _stream_request(sock: socket.socket, payload: bytes, cutoff: int, rng: random.Random) -> None:
    limit = max(1, min(len(payload), cutoff))
    index = 0
    while index < limit:
        chunk = rng.randint(1, min(limit - index, 512))
        segment = bytearray(payload[index : index + chunk])
        if segment and rng.random() < 0.18:
            pos = rng.randrange(len(segment))
            segment[pos] ^= rng.randrange(1, 256)
        sock.sendall(bytes(segment))
        index += chunk
        if rng.random() < 0.3:
            time.sleep(rng.random() * 0.02)

    if limit < len(payload) and rng.random() < 0.5:
        try:
            sock.shutdown(socket.SHUT_WR)
        except OSError:
            pass

    if rng.random() < 0.2:
        junk = bytes(rng.randrange(256) for _ in range(rng.randint(1, 12)))
        sock.sendall(junk)


def _drain_socket(sock: socket.socket, rng: random.Random, timeout: float) -> None:
    deadline = time.time() + max(0.0, timeout)
    while time.time() < deadline:
        try:
            data = sock.recv(1024)
        except socket.timeout:
            break
        except OSError:
            break
        if not data or rng.random() < 0.35:
            break


def _mutate_token(token: str, rng: random.Random) -> str:
    if rng.random() < 0.3:
        token = token.lower()
    if rng.random() < 0.25:
        token = token + rng.choice(("+", "FUZZ", "*", " "))
    if rng.random() < 0.2 and token:
        idx = rng.randrange(len(token))
        token = token[:idx] + rng.choice(("-", "_", ":")) + token[idx:]
    return token


def _fuzz_host(rng: random.Random) -> str:
    if rng.random() < 0.2:
        return "[" + ":".join(f"{rng.randint(0, 0xffff):x}" for _ in range(8)) + "]"

    labels = []
    for _ in range(rng.randint(1, 4)):
        length = rng.randint(1, 12)
        label = "".join(rng.choice(string.ascii_lowercase + string.digits + "-") for _ in range(length))
        labels.append(label or "a")
    host = ".".join(labels)
    if rng.random() < 0.4:
        host += f":{rng.randint(0, 65535)}"
    return host


def _fuzz_path(rng: random.Random) -> str:
    segments: List[str] = []
    for _ in range(rng.randint(1, 6)):
        segment = rng.choice(_PATH_TOKENS)
        if "%%PAYLOAD%%" in segment:
            payload = creative_fuzzy_inputs(1, seed=rng.randrange(1 << 32), as_bytes=False)[0]
            if isinstance(payload, bytes):
                payload = payload.decode("latin-1", "ignore")
            segment = segment.replace("%%PAYLOAD%%", payload.strip().replace("/", "%2F") or "fuzz")
        if rng.random() < 0.25:
            segment = segment.upper()
        if rng.random() < 0.2:
            segment = segment + rng.choice((";", "%00", "?", "//"))
        segments.append(segment)

    base = "/" + "/".join(segments)
    if rng.random() < 0.3:
        base = base.replace("//", "/")

    query = _fuzz_query(rng) if rng.random() < 0.6 else ""
    if rng.random() < 0.15:
        base += rng.choice(("#fragment", "#../../", "#%0d%0a"))
    return base + query


def _fuzz_query(rng: random.Random) -> str:
    pairs: List[str] = []
    for _ in range(rng.randint(1, 4)):
        key = rng.choice(_QUERY_KEYS)
        if rng.random() < 0.3:
            key += rng.choice(("_", "-", "%0d%0a"))
        value = "".join(rng.choice(string.ascii_letters + string.digits + "%._-") for _ in range(rng.randint(0, 12)))
        if rng.random() < 0.25:
            value += rng.choice(("%00", "../../", "`"))
        pairs.append(f"{key}={value}")
    return "?" + rng.choice(("&", ";", "&&", "&;")).join(pairs)


def _fuzz_header_value(rng: random.Random) -> str:
    roll = rng.random()
    if roll < 0.3:
        return rng.choice(_HEADER_VALUE_TOKENS)
    if roll < 0.6:
        length = rng.randint(0, 48)
        return "".join(rng.choice(_HEADER_CHARS) for _ in range(length))
    payload = creative_fuzzy_inputs(1, seed=rng.randrange(1 << 32), as_bytes=False)[0]
    if isinstance(payload, bytes):
        payload = payload.decode("latin-1", "ignore")
    return payload[:128]


def _build_body_payload(rng: random.Random) -> bytes:
    if rng.random() < 0.4:
        length = rng.randint(0, 1024)
        return bytes(rng.randrange(256) for _ in range(length))

    parts = creative_fuzzy_inputs(rng.randint(1, 3), seed=rng.randrange(1 << 32))
    blob = b"\r\n".join(part if isinstance(part, bytes) else str(part).encode("utf-8", "ignore") for part in parts)
    if rng.random() < 0.3:
        blob += bytes(rng.randrange(256) for _ in range(rng.randint(0, 32)))
    return blob


def _encode_chunked_body(body: bytes, rng: random.Random) -> bytes:
    if not body:
        return b"0\r\n\r\n"

    chunked = bytearray()
    view = memoryview(body)
    position = 0
    while position < len(view):
        size = rng.randint(1, min(16, len(view) - position))
        chunked.extend(f"{size:x}\r\n".encode("ascii"))
        chunked.extend(view[position : position + size])
        chunked.extend(b"\r\n")
        position += size
        if rng.random() < 0.2:
            junk_size = rng.randint(0, 8)
            chunked.extend(f"{junk_size:x}\r\n".encode("ascii"))
            chunked.extend(b"X" * junk_size)
            chunked.extend(b"\r\n")
    chunked.extend(b"0\r\n\r\n")
    if rng.random() < 0.3:
        drop = rng.randint(0, len(chunked) - 1)
        return bytes(chunked[:-drop]) if drop else bytes(chunked)
    return bytes(chunked)


__all__ = ["creative_fuzzy_inputs", "fuzz_http_server"]
