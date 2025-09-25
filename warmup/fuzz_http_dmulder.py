import sys
import atheris
import requests

BASE_URL = "http://localhost:80"

def TestOneInput(data: bytes) -> None:
    s = data.decode(errors="ignore")
    try:
        requests.get(f"{BASE_URL}/{s}", timeout=1)
        requests.post(BASE_URL, data=s.encode(), timeout=1)
    except requests.RequestException:
        pass

def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()

if __name__ == "__main__":
    main()
