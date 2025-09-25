"""Warmup fuzzer."""

import random
import socket

IP = "127.0.0.1"
PORT = 80

s = socket.socket()
s = socket.connect(IP, PORT)

while True:
    num_bytes = random.randint(0, 100_000)
    payload = random.randbytes(num_bytes)
    sock.sendall(payload)
