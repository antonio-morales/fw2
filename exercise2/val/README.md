# exercise 2 — findings

found a ReDoS in `moment().format()` via the `MONTHS_IN_FORMAT` regex when
the locale has separate `format`/`standalone` months (like `be`).

## root cause

`moment.js` line 833:

```js
MONTHS_IN_FORMAT = /D[oD]?(\[[^\[\]]*\]|\s+)+MMMM?/;
```

when the format string contains `MMM` or `MMMM`, moment calls
`locale.months(m, format)` → `MONTHS_IN_FORMAT.test(format)` on the full
format string.

the `(\[[^\[\]]*\]|\s+)+` group matches either a bracketed literal or
whitespace. if the format has a `D`, a run of spaces after it, and no `MMM`
to satisfy the trailing `MMMM?`, the regex engine tries every partition of
those spaces across the `+` quantifier. that's **2^N** attempts before it
gives up — catastrophic backtracking.

## repro

```js
const moment = require('moment');
moment.locale('be');
moment().format('MMMMD' + ' '.repeat(32));
```

measured locally (moment 2.15.1, node 18.19.1 as pinned by the workshop):

| whitespace run | time      |
| -------------- | --------- |
| 25             |    242 ms |
| 28             |    382 ms |
| 30             |   1533 ms |
| 32             |   6134 ms |
| 34             |  24808 ms |

doubles roughly every +1 space. extending to 40+ spaces pins a single CPU
for minutes — a ReDoS.

## why the locale matters

if `moment.locale(...)` is left at `en`, `this._months` is an array, so the
shortcut path in `localeMonths` fires and `MONTHS_IN_FORMAT` is never
tested. `be` (and any locale with format/standalone split) exposes it.

## fix idea

replace `(\[[^\[\]]*\]|\s+)+` with two non-overlapping classes that can't
backtrack into each other, e.g. `(?:\[[^\[\]]*\]|\s)+` (single-char
whitespace with no inner `+`). this was addressed upstream in later
moment releases.
