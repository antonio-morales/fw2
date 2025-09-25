#!/bin/bash


URL="http://127.0.0.1:8000"
REQS=100000
SIZE=1024

for i in $(seq 1 $REQS); do
  PAYLOAD=$(head -c $SIZE /dev/urandom | base64 | tr -d '\n')

  if (( RANDOM % 2 )); then
    curl -s -o /dev/null -w "[$i] GET %s -> %{http_code}\n" \
      "$URL/$PAYLOAD"
  else
    curl -s -o /dev/null -w "[$i] POST -> %{http_code}\n" \
      -X POST -d "$PAYLOAD" "$URL"
  fi
done
