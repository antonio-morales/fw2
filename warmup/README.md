# warmup-fuzz

Concurrent fuzzer targeting `localhost:80`.

- 10 raw TCP connections that send random bytes
- 10 HTTP requests via HTTPX with random methods, headers, and bodies

## Install

```bash
python -m pip install -e .
```

## Usage

```bash
fuzz
```

Optional flags will be added later.


