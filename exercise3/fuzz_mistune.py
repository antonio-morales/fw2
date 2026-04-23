#!/usr/bin/env python3

import re
from html.parser import HTMLParser

from bs4 import BeautifulSoup

import atheris

with atheris.instrument_imports():
  import mistune
  import sys


_RAW_ATTR_PATTERN = re.compile(r'''([^\s=/>]+)\s*=\s*(["'])(.*?)\2''')
_QUOTE_ENTITY_PATTERN = re.compile(r'&(quot|#34|#x0*22);', re.IGNORECASE)


class RawHTMLQuoteChecker(HTMLParser):
    """Detect raw attribute quoting issues without flagging escaped entities."""

    def __init__(self):
        super().__init__()
        self.issues = []

    def handle_starttag(self, tag, attrs):
        self._check_attrs(tag, attrs)

    def handle_startendtag(self, tag, attrs):
        self._check_attrs(tag, attrs)

    def _check_attrs(self, tag, attrs):
        raw_tag = self.get_starttag_text() or ""
        raw_attrs = {}
        for name, delimiter, raw_value in _RAW_ATTR_PATTERN.findall(raw_tag):
            raw_attrs[name] = (delimiter, raw_value)

        for attr, val in attrs:
            if isinstance(val, list):
                val = " ".join(val)
            if not val or '"' not in val:
                continue

            raw_attr = raw_attrs.get(attr)
            if raw_attr is None:
                self.issues.append((tag, attr, val, raw_tag))
                continue

            delimiter, raw_val = raw_attr
            if delimiter == '"' and not _QUOTE_ENTITY_PATTERN.search(raw_val):
                self.issues.append((tag, attr, val, raw_tag))


def find_unescaped_quote_issues(html):
    """Return raw HTML attribute quote issues that are not entity-escaped."""
    checker = RawHTMLQuoteChecker()
    checker.feed(html)
    checker.close()
    return checker.issues


def TestOneInput(data):
    s = atheris.FuzzedDataProvider(data).ConsumeUnicode(len(data))
    html = mistune.Markdown()(s)

    # DOM parsing with BeautifulSoup/html5lib
    soup = BeautifulSoup(html, "html5lib")

    # Force DOM parsing to exercise the HTML parser, but check the raw HTML for
    # quoting issues so entity-escaped quotes like &quot; do not trigger false
    # positives after decoding.
    soup.find_all(True)

    issues = find_unescaped_quote_issues(html)
    if issues:
        tag, attr, val, raw_tag = issues[0]
        raise AssertionError(
            f"Unescaped quote in raw tag {raw_tag!r} via <{tag} {attr}={val!r}> "
            f"for payload {repr(s)}"
        )


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()

if __name__ == "__main__":
    main()
