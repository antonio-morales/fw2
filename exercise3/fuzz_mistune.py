#!/usr/bin/env python3

from bs4 import BeautifulSoup

import atheris

with atheris.instrument_imports():
  import mistune
  import sys

def TestOneInput(data):
    s = atheris.FuzzedDataProvider(data).ConsumeUnicode(len(data))
    html = mistune.Markdown()(s)

    # DOM parsing with BeautifulSoup/html5lib
    soup = BeautifulSoup(html, "html5lib")

    for tag in soup.find_all(True):
        for attr, val in tag.attrs.items():
            if isinstance(val, list):
                val = " ".join(val)
            if val and '"' in val:
                raise AssertionError(
                    f"Unescaped quote in <{tag.name} {attr}=\"{val}\"> "
                    f"for payload {repr(s)}"
                )

def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()

if __name__ == "__main__":
    main()
