from http.client import HTTPConnection
import random

def random_string(length):
    number = '0123456789'
    alpha = 'abcdefghijklmnopqrstuvwxyz'
    id = ''
    for _ in range(0,length,2):
        id += random.choice(number)
        id += random.choice(alpha)
    return id

conn = HTTPConnection('localhost')
while True:
    conn.request("GET", f"/{random_string(random.randint(1,1000))}")
    response = conn.getresponse()
    print(response.status, response.reason)
