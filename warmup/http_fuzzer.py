import random
import string
import requests
import threading

# Simple HTTP fuzzer for localhost:80

def random_path(length=8):
    return '/' + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def random_query(length=10):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def fuzz_http(num_tests=100):
    def send_request(i):
        path = random_path(random.randint(1, 20))
        query = random_query(random.randint(1, 20))
        url = f"http://localhost:80{path}?q={query}"
        headers = {}
        for _ in range(random.randint(1, 5)):
            key = ''.join(random.choices(string.ascii_letters, k=random.randint(4, 12)))
            value = ''.join(random.choices(string.printable, k=random.randint(4, 20)))
            headers[key] = value
        try:
            response = requests.get(url, headers=headers, timeout=2)
            print(f"Test {i+1}: {url} | Status: {response.status_code} | Length: {len(response.content)} | Headers: {headers}")
        except Exception as e:
            print(f"Test {i+1}: {url} | Exception: {e} | Headers: {headers}")

    threads = []
    for i in range(num_tests):
        t = threading.Thread(target=send_request, args=(i,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

if __name__ == "__main__":
    fuzz_http()

