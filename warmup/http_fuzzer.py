#!/usr/bin/env python
# License: GPLv3 Copyright: 2025, Kovid Goyal <kovid at kovidgoyal.net>


import os
import random
import string
from threading import Thread
from urllib.request import Request, urlopen


def generate_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def make_request():
    x = random.choice(string.ascii_letters)
    rq = Request('http://localhost:80/' + generate_random_string(20), headers={
        generate_random_string(120): generate_random_string(300)}, data=os.urandom(9484343))
    with urlopen(rq) as f:
        f.close()

def main():
    for i in range(10000):
        threads = []
        for i in range(random.randint(10, 5000)):
            t = Thread(target=make_request)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()


if __name__ == '__main__':
    main()
