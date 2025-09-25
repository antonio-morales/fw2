#!/usr/bin/env bash

for i in $(seq 1 10000); do
  url="http://localhost:80/?value=$RANDOM"
  curl -q -s "$url"
done
