#!/usr/bin/env node
import { readFile } from "node:fs/promises";
import { performance } from "node:perf_hooks";

type Args = {
  url: string;
  wordlist: string;
  method: string;
  concurrency: number;
  timeoutMs: number;
  hideStatus: Set<number>;
  body?: string;
  headers: Record<string, string>;
};

function parseArgs(argv: string[]): Args {
  const a: Args = {
    url: "",
    wordlist: "",
    method: "GET",
    concurrency: 50,
    timeoutMs: 5000,
    hideStatus: new Set(),
    headers: {},
  };
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i];
    const v = argv[i + 1];
    switch (k) {
      case "-u": case "--url":        a.url = v; i++; break;
      case "-w": case "--wordlist":   a.wordlist = v; i++; break;
      case "-X": case "--method":     a.method = v.toUpperCase(); i++; break;
      case "-c": case "--concurrency": a.concurrency = Number(v); i++; break;
      case "-t": case "--timeout":    a.timeoutMs = Number(v) * 1000; i++; break;
      case "--hide-status":
        v.split(",").map((s) => s.trim()).filter(Boolean)
          .forEach((s) => a.hideStatus.add(Number(s)));
        i++; break;
      case "--body": a.body = v; i++; break;
      case "-H": case "--header": {
        const idx = v.indexOf(":");
        if (idx > 0) a.headers[v.slice(0, idx).trim()] = v.slice(idx + 1).trim();
        i++; break;
      }
      case "-h": case "--help": printHelp(); process.exit(0);
    }
  }
  if (!a.url || !a.wordlist) { printHelp(); process.exit(1); }
  if (!a.url.includes("FUZZ") && !(a.body?.includes("FUZZ"))) {
    console.error("error: url or body must contain the FUZZ marker");
    process.exit(1);
  }
  return a;
}

function printHelp() {
  console.log(`fuzzer-ts — async HTTP fuzzer
usage: fuzzer-ts -u <url-with-FUZZ> -w <wordlist> [options]
  -X, --method <GET>        HTTP method
  -c, --concurrency <50>    in-flight requests
  -t, --timeout <5>         per-request timeout (seconds)
  --hide-status 404,403     hide these status codes
  --body '{"q":"FUZZ"}'     body template (FUZZ substituted)
  -H, --header 'K: V'       extra header (repeatable)`);
}

async function loadWords(path: string): Promise<string[]> {
  const raw = await readFile(path, "utf8");
  return raw
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter((l) => l.length > 0 && !l.startsWith("#"));
}

async function worker(
  args: Args,
  queue: string[],
  cursor: { i: number },
  onResult: (word: string, status: number | null, bytes: number, ms: number) => void
): Promise<void> {
  while (true) {
    const idx = cursor.i++;
    if (idx >= queue.length) return;
    const word = queue[idx];
    const url = args.url.replace(/FUZZ/g, word);
    const body = args.body ? args.body.replace(/FUZZ/g, word) : undefined;
    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), args.timeoutMs);
    const t0 = performance.now();
    try {
      const headers: Record<string, string> = { ...args.headers };
      if (body) headers["content-type"] ??= "application/json";
      const resp = await fetch(url, { method: args.method, headers, body, signal: ctl.signal });
      const buf = await resp.arrayBuffer();
      onResult(word, resp.status, buf.byteLength, performance.now() - t0);
    } catch {
      onResult(word, null, 0, performance.now() - t0);
    } finally {
      clearTimeout(timer);
    }
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const words = await loadWords(args.wordlist);
  console.log(`fuzzer-ts → ${args.method} ${args.url} (${words.length} words, conc=${args.concurrency})`);

  let shown = 0, done = 0;
  const t0 = performance.now();
  const cursor = { i: 0 };

  const onResult = (word: string, status: number | null, bytes: number, ms: number) => {
    done++;
    if (status === null || args.hideStatus.has(status)) return;
    shown++;
    const p = (s: string | number, n: number) => String(s).padStart(n);
    console.log(`  ${p(status, 3)}  ${p(bytes, 7)}B  ${p(ms.toFixed(0), 4)}ms  ${word}`);
  };

  const workers = Array.from(
    { length: Math.min(args.concurrency, words.length) },
    () => worker(args, words, cursor, onResult)
  );
  await Promise.all(workers);

  const elapsed = (performance.now() - t0) / 1000;
  const rps = elapsed > 0 ? done / elapsed : 0;
  console.log(`\ndone → ${done}/${words.length} requests, ${shown} shown, ${elapsed.toFixed(1)}s, ${rps.toFixed(1)} req/s`);
}

main().catch((e) => { console.error(e); process.exit(1); });
