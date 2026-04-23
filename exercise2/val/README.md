# exercise 2

ReDoS in moment 2.15.1 when you call format() under a locale that has
separate format/standalone months. 'be' (belarusian) is one of those.

the regex is in moment.js line 833:

```js
MONTHS_IN_FORMAT = /D[oD]?(\[[^\[\]]*\]|\s+)+MMMM?/;
```

whenever the format string has MMM or MMMM, moment calls
`locale.months(m, format)` which runs this regex against the whole format
string to decide whether to use the format or standalone month list.

the `(\[[^\[\]]*\]|\s+)+` part is the problem. if the format has a D, then
a bunch of spaces, and no MMM/MMMM after those spaces, the engine tries
every way to split the spaces between the `+` repetitions before finally
giving up. classic catastrophic backtracking.

## repro

```js
const moment = require('moment');
moment.locale('be');
moment().format('MMMMD' + ' '.repeat(34));
```

on node 18.19.1 / moment 2.15.1:

```
25 spaces ->   242 ms
28 spaces ->   382 ms
30 spaces ->  1533 ms
32 spaces ->  6134 ms
34 spaces -> 24808 ms
```

doubles every extra space. 40+ spaces hangs for minutes.

## why locale matters

under `en`, `this._months` is a plain array so the shortcut in localeMonths
returns early and the regex never runs. locales like `be` have a
`{format, standalone}` object, which is what makes MONTHS_IN_FORMAT get
tested.

## fix idea

rewrite the inner group so the two branches don't overlap. e.g. replace
`(\[[^\[\]]*\]|\s+)+` with `(?:\[[^\[\]]*\]|\s)+` so whitespace only
matches one char per repetition and there's nothing to backtrack.
