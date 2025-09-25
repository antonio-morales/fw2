import socket
import random
import string
import time

def random_data():
    # Choose a random length between 1 and 1024 for each call
    rand_length = random.randint(1, 1024)
    return ''.join(random.choices(string.printable, k=rand_length)).encode('utf-8')

def fuzz_localhost(port=80, iterations=100):
    for i in range(iterations):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect(('127.0.0.1', port))
            data = random_data()
            print(f"Sending: {data}")
            s.sendall(data)
            try:
                response = s.recv(4096)
                print(f"Received: {response}")
            except socket.timeout:
                print("No response (timeout)")
            s.close()
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(0.1)

if __name__ == "__main__":
    fuzz_localhost()