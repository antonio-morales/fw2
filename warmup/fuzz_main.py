
import requests
import random
import string

URL = "http://localhost:80"

def random_string(min_length=1, max_length=100):
    length = random.randint(min_length, max_length)
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choices(chars, k=length))

def random_headers():
    headers = {}
    for _ in range(random.randint(1, 5)):
        key = random_string(3, 10)
        value = random_string(3, 20)
        headers[key] = value
    return headers

def random_params():
    params = {}
    for _ in range(random.randint(0, 5)):
        key = random_string(3, 10)
        value = random_string(1, 20)
        params[key] = value
    return params

def random_data():
    # Randomly choose between text, JSON, or binary
    choice = random.choice(['text', 'json', 'binary'])
    if choice == 'text':
        return random_string(1, 200)
    elif choice == 'json':
        # Simple random JSON
        return '{"' + random_string(3,10) + '": "' + random_string(3,20) + '"}'
    else:
        return bytes(random.getrandbits(8) for _ in range(random.randint(1, 100)))

METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]

for i in range(100):
    method = random.choice(METHODS)
    headers = random_headers()
    params = random_params() if random.random() < 0.5 else None
    data = random_data() if method in ["POST", "PUT", "PATCH"] and random.random() < 0.7 else None
    try:
        response = requests.request(method, URL, headers=headers, params=params, data=data)
        print(f"[{i}] {method} {URL} -> {response.status_code}")
        print(f"Headers: {headers}")
        if params:
            print(f"Params: {params}")
        if data:
            print(f"Data: {data if isinstance(data, str) else '<binary>'}")
        print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"[{i}] {method} {URL} -> Exception: {e}")
