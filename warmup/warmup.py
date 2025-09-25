import requests
import random
import string

def fuzz():
    # Generate random path and query
    path = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    query = ''.join(random.choices(string.ascii_letters + string.digits, k=5))
    url = f"http://localhost:80/{path}?q={query}"

    try:
        response = requests.get(url)
        print(f"URL: {url} - Status: {response.status_code}")
    except Exception as e:
        print(f"URL: {url} - Error: {e}")

if __name__ == "__main__":
    for _ in range(1000):  # Number of requests to send
        fuzz()
