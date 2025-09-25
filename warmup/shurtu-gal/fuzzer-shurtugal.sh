#!/bin/bash

RANDOM=$(head -c 75 /dev/urandom | base64 | tr -dc 'A-Za-z0-9-_.~' | cut -c1-100)
echo "Sending input: $RANDOM"

# POST to localhost only (explicit 127.0.0.1). timeout=5s, show status code.
curl --max-time 5 -sS -X POST -H "Content-Type: text/plain" --data "$RANDOM" "http://127.0.0.1:3000" -w "\nHTTP_STATUS:%{http_code}\n"
