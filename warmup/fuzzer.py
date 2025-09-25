# Simple HTTP fuzzer
# dfandrich

import random
import requests


TARGET_URL = 'http://localhost:8000/'
FUZZ_URL = TARGET_URL + '{DATA}'
FUZZ_MAX_LEN = 20


def fuzz(iterations=100):
    for _ in range(iterations):
        requests.get(url=FUZZ_URL.format(DATA=random.randbytes(random.randint(1, FUZZ_MAX_LEN)).decode('ISO-8859-1')))

if __name__ == '__main__':
    fuzz()
