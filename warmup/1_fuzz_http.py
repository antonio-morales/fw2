import os
import random
import string
import time

import urllib3


def random_bytes(size: int = 64) -> bytes:
    return os.urandom(size)


def random_string(length: int = 16) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def random_headers(num: int = 5) -> dict[str, str]:
    headers = {}
    for _ in range(num):
        key = random_string(random.randint(4, 12))
        value = random_bytes(random.randint(8, 32)).decode("latin1", errors="ignore")
        headers[key] = value
    return headers


def random_body(size: int = 64) -> bytes:
    return random_bytes(size)


def fuzz_loop(iterations: int = 1000, delay: float = 0.1) -> None:
    for i in range(iterations):
        headers = random_headers(random.randint(2, 8))
        body = random_body(random.randint(16, 128))
        method = random.choice(["GET", "POST", "PUT", "DELETE", "PATCH"])
        try:
            response = urllib3.request(
                method,
                "http://localhost:80",
                headers=headers,
                body=body if method in ["POST", "PUT", "PATCH"] else None,
                timeout=2,
                retries=False,
            )
            status = response.status
            print(f"[{i}] {method} {status} Headers: {headers}")
            if 500 <= status < 600:
                print(f"!!! Server issue detected: {status}")
        except ValueError:
            pass
        except Exception as e:
            print(f"[{i}] Exception: {e}")
        time.sleep(delay)


if __name__ == "__main__":
    fuzz_loop()
