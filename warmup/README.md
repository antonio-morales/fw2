# Warmup: HTTP Fuzzer (Rust + TypeScript)

Two implementations of an async HTTP fuzzer targeting localhost. Both share an
identical CLI so you can compare the two side-by-side.

| impl | lang | concurrency model |
|------|------|-------------------|
| `fuzzer-rs/` | Rust | reqwest + tokio `buffer_unordered` |
| `fuzzer-ts/` | TypeScript | Node native fetch + Promise.all workers |

## Quick start — TypeScript (no compile step)

```bash
# 1. start a localhost target
cd warmup/fuzzer-ts
npm install
node --import=tsx src/target.ts   # listens on 127.0.0.1:8080

# 2. in another terminal, run the fuzzer
node --import=tsx src/cli.ts \
  -u http://127.0.0.1:8080/FUZZ \
  -w ../wordlists/paths-small.txt \
  --hide-status 404
```

## Quick start — Rust

```bash
cd warmup/fuzzer-rs
cargo run --release -- \
  -u http://127.0.0.1:8080/FUZZ \
  -w ../wordlists/paths-small.txt \
  --hide-status 404
```

## CLI reference (same for both)

```
-u, --url          URL template; FUZZ is the substitution marker
-w, --wordlist     newline-delimited wordlist
-X, --method       HTTP method (default GET)
-c, --concurrency  in-flight requests (default 50)
-t, --timeout      per-request timeout in seconds (default 5)
    --hide-status  comma-separated status codes to suppress
    --body         JSON body template (FUZZ substituted)
-H, --header       extra header, repeatable ("Name: Value")
```

## How it works

1. Load wordlist, strip comments/blanks.
2. Spawn N concurrent workers; each picks from a shared cursor.
3. Substitute `FUZZ` in the URL (and optionally the body).
4. Print status, response size, latency, and the word for every response
   not in the hide list.
5. Print a summary line (total, shown, elapsed, req/s).

## Scope

Localhost-only by design — this is a learning fuzzer, not a red-team tool.
