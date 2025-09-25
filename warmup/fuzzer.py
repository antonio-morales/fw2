import socket
import random
import string

HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]

def get_random_payload():
    chars = string.ascii_letters + string.digits
    body = "".join(random.choices(chars, k=32))
    method = random.choice(HTTP_METHODS)
    return f"{method} /{body} HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n".encode()

def fuzz():
    while True:
        payload = get_random_payload()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.connect(("127.0.0.1", 80))
            s.sendall(payload)
            data = s.recv(1024)

if __name__ == "__main__":
    fuzz()
