#!/bin/bash
LEN="$(awk -v min=0 -v max=1000000 'BEGIN{srand(); print int(min+rand()*(max-min+1))}')"
dd if=/dev/urandom "bs=$LEN" count=1 | nc -v localhost 80
