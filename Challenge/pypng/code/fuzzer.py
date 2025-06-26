#!/usr/bin/env python3
import json
import io
import atheris
import zlib

with atheris.instrument_imports():
  import png
  import sys


def info_json_out(out, inp):
    """To the writable file `out` write a JSON record for
    each image found on the readable file `inp`.
    """
    while True:
        r = png.Reader(file=inp)
        try:
            w, h, rows, info = r.read()
        except EOFError:
            break

        list(rows)

        json.dump(info, out, sort_keys=True, indent="  ")
        out.write("\n")


def TestOneInput(data: bytes) -> None:
    inp = io.BytesIO(data)
    sink = io.StringIO()
    try:
        info_json_out(sink, inp)
    except (EOFError, png.FormatError, zlib.error, AttributeError):
        pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()

