import requests
import random
import string

URL = "https://localhost:80"

def main():
  while True:
   request_type = random.randint(1,2)
   characters = string.ascii_letters + string.digits
   string_length = random.randint(1,128)
   request_body = ''.join(random.choice(characters) for _ in range(string_length))
   header_count = random.randint(0, 16)
   headers = {}
   # TODO: Add headers
   if request_type == 1:
     requests.get(URL, request_body)
   elif request_type == 2:
     requests.post(URL, request_body)
   elif request_type == 3:
     request.put(URL, request_body)

if __name__ == "__main__":
  main()
