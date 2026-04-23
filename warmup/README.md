# Warm-up HTTP Fuzzer

This solution is a small Go CLI that sends mutated raw HTTP requests to a TCP target and reports distinct response or error signatures.

## What it fuzzes

- HTTP methods, paths, and versions
- Header names, duplicated headers, and oversized values
- Content-Length mismatches and random request bodies
- Line endings, truncation, and raw byte corruption

## Usage

```bash
cd warmup
go run . -addr localhost:80 -iterations 250
```

Useful flags:

- `-seed` to replay a previous run
- `-timeout` to change the per-request deadline
- `-max-read` to cap captured response bytes

The program prints each newly observed outcome once, including the exact request bytes that triggered it and a short response preview when available.
