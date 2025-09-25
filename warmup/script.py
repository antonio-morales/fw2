# /// script
# requires-python = ">=3.11"
# dependencies = [
# ]
# ///

import random
import socket
port = 80

sock = socket.socket()
sock.connect(("0.0.0.0", port))

len = random.randint(0, 1_000_000)

payload = random.randbytes(len)
print(f"Sending {len} bytes to :{port}")
# Just send some garbage :D
sock.sendall(payload)

