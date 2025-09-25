# /// script
# dependencies = ["httpx"]
# ///
# Run with `uv run huzz.py`.
import random
import time
from urllib.parse import quote_plus

import httpx

base_url = "http://localhost:80/"
sess = httpx.Client(timeout=5)

methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]


def make_request():
    method = random.choice(methods)
    body = None
    if method in ["POST", "PUT", "PATCH"]:
        body = random.randbytes(random.randint(0, 1024))
    url = base_url
    if random.random() < 0.5:
        url += quote_plus(random.randbytes(random.randint(1, 50)))
    # TODO: add headers, query params, etc.

    resp = sess.request(method, url, data=body)
    resp.raise_for_status()


t0 = time.time()


while True:
    try:
        make_request()
    except Exception as e:
        print("***", e)

    if time.time() - t0 > 10:
        break
