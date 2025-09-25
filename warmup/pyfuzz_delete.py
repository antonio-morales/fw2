import socket, random, string
from concurrent.futures import ThreadPoolExecutor

paths = [
    "/", "/admin", "/user/123", "/user", "/settings", "/dashboard",
    "/api/data", "/api/admin", "/profile", "/logout", "/user?id=1", "/user?id=9999"
]

# Or scrape the page to find things that look like element or user IDs and
# guess RESTful UPDATE/DELETE paths

methods = ["POST", "DELETE"]

def new_request():
    method = random.choice(methods)
    path = random.choice(paths)
    payload = ''.join(random.choices(string.printable, k=random.randint(1,2048)))
    req = (
        f"{method} {path} HTTP/1.1\r\n"
        f"Host:localhost\r\n"
        f"Content-Length:{len(payload)}\r\n"
        f"\r\n"
        f"{payload if method == 'POST' else ''}"
    )
    try:
        s = socket.create_connection(("localhost",80),2)
        s.send(req.encode())
        s.close()
    except: pass

with ThreadPoolExecutor(max_workers=500) as executor:
    for _ in range(500):
        executor.submit(new_request)
