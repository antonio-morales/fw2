import requests
import random
import string

TARGET = "http://localhost:80"

def random_string(n):
    return ''.join(random.choices(string.printable, k=n))

payloads = [
    "/",
    "/admin",
    "/" + "A" * 100,
    random_string(20),
]

for path in payloads:
    try:
        r = requests.get(TARGET + path, timeout=2)
        print(f"{path!r:30} -> {r.status_code}")
    except Exception as e:
        print(f"{path!r:30} -> ERROR: {e}")
