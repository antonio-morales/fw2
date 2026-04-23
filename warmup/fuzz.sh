#! /usr/bin/env bash

while :
do  
    # take 10 random bytes and send them in body
	cat /dev/urandom | head -c 10 | curl -X POST -d @- "http:127.0.0.1:80"
done
