import socket
import random
import string

HOST = 'localhost'
PORT = 80

# Generate a random string of length n
def random_string(n=32):
    return ''.join(random.choices(string.printable, k=n))

# Create a simple HTTP request with fuzzed data
def fuzz_request():
    method = random.choice(['GET', 'POST', 'PUT', 'DELETE', 'HEAD'])
    path = '/' + random_string(random.randint(1, 10))
    headers = [
        f"Host: {HOST}",
        f"User-Agent: {random_string(8)}",
        f"X-Fuzz: {random_string(16)}"
    ]
    body = random_string(random.randint(0, 64))
    request = f"{method} {path} HTTP/1.1\r\n" + '\r\n'.join(headers) + "\r\n\r\n" + body
    return request.encode('utf-8')

# Send fuzzed requests to the server
def main():
    for i in range(10):  # Send 10 fuzzed requests
        req = fuzz_request()
        try:
            with socket.create_connection((HOST, PORT), timeout=2) as s:
                s.sendall(req)
                try:
                    resp = s.recv(4096)
                    print(f"Response {i+1}: {resp[:100]!r}")
                except socket.timeout:
                    print(f"Response {i+1}: timed out")
        except Exception as e:
            print(f"Request {i+1} failed: {e}")

if __name__ == "__main__":
    main()
