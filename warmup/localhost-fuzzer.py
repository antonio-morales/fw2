#!/usr/bin/env python3

import requests

def main():
    url = "http://localhost:80"

    response = requests.get(url)
    print(f"Status code: {response.status_code}")
    print(f"Response body: {response.text}")

    with open("/dev/urandom", "rb") as f:
        random_data = f.read(1024)

    response = requests.post(url, data=random_data)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")


if __name__ == "__main__":
    main()
