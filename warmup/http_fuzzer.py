from http.client import HTTPConnection

import numpy as np

def random_string():
    rng = np.random.default_rng()
    string = "".join(rng.choice(list("abcdefghi")+[" ", ".", ","]))
    return string

conn = HTTPConnection("http://localhost:80")
conn.request("PUT", "/", body=random_string())
