while true; do cat /dev/urandom | socat STDIO TCP4:localhost:80; done
