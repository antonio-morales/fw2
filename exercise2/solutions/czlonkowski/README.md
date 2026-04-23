# Exercise 2 — ReDoS in moment 2.15.1 (`be` locale)

## Finding

Jazzer.js reports a timeout (>5s per input) when `moment().format()` is called
with a crafted format string while `moment.locale('be')` is active.

```
ALARM: working on the last Unit for 6 seconds
       and the timeout value is 5 (use -timeout=N to change)
SUMMARY: libFuzzer: timeout
```

## Root cause

In moment 2.15.1, the Belarusian locale's `months` function tests the format
string with this regex:

```js
months: function (m, format) {
    if (/D[oD]?(\[[^\[\]]*\]|\s+)+MMMM?/.test(format)) {
        return this._months['format'][m.month()];
    } else {
        return this._months['standalone'][m.month()];
    }
}
```

`(\[[^\[\]]*\]|\s+)+` is a classic catastrophic-backtracking pattern: two
alternatives that overlap on whitespace-adjacent input, wrapped in a `+`
quantifier. A format string starting with `Do` followed by a long run of
whitespace that never reaches `MMMM?` forces the regex engine to explore an
exponential number of ways to group the spaces before declaring no match.

Reference: GHSA-wc69-rhjr-hc9g / CVE-2017-18214.

## Proof of concept

`redos-poc.bin` (134 bytes) is the minimized crashing input Jazzer produced.
Readable portion:

```
MMMM                oDo\320\021KDoQg\000DoQ              Do ...<whitespace>... MMM\377M@MM
```

## Reproduce

From `exercise2/`:

```
npx jazzer fuzzer --includes moment -- -timeout=2 -rss_limit_mb=4096 \
  solutions/czlonkowski/redos-poc.bin
```

Expected: libFuzzer `ALARM` / `timeout` after a few seconds on that single
input.

## Fuzzing stats

- Seed: random (ReDoS reproduces with multiple seeds; coverage-guided search
  finds it after ~900k exec on this machine, roughly 90 seconds).
- Critical flags: `--includes moment` (without it, moment's internals are not
  instrumented, coverage stays at 3, and the fuzzer never explores the
  vulnerable regex path). `-timeout=2` so libFuzzer surfaces slowdowns as
  findings instead of running each input for up to 1200 s.
