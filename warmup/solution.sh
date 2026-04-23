#!/bin/sh

head -c 1M /dev/urandom | curl -X POST --data-binary @- https://localhost:80
