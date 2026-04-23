# homework: pypng fuzz

atheris + the provided `fuzzer.py` against the workshop's modified
pypng (`png.py`, version `0.20250521.0`). the harness catches
`EOFError`, `FormatError`, `zlib.error`, `AttributeError` — anything
else escapes as a crash.

## finding: indexerror in `_deinterlace` on truncated interlaced idat

`_deinterlace` walks the 7 adam7 passes and indexes into the
decompressed idat buffer to read each pass's filter byte + scanline:

```python
filter_type = raw[source_offset]
source_offset += 1
scanline = raw[source_offset : source_offset + row_size]
```

there is no length check. if an interlaced png (`IHDR.interlace=1`)
ships an idat chunk whose decompressed payload is shorter than the
adam7 layout requires, `raw[source_offset]` runs off the end and
raises `IndexError: bytearray index out of range`.

`IndexError` is not in the harness' caught list, so it propagates to
libfuzzer and the fuzzer reports a crash.

## smallest poc (65 bytes): `poc.png`

- signature
- `IHDR`: width=2, height=2, bitdepth=8, colour=0 (greyscale), interlace=1
- `IDAT`: zlib-compressed empty payload
- `IEND`

because the workshop's `png.py` removed the crc check inside
`Reader.chunk()`, the chunks can carry `\0\0\0\0` for the crc field
and still parse.

trace from the harness:

```
Uncaught Python exception:
IndexError: bytearray index out of range
  File "fuzzer.py", line 33, in TestOneInput
    info_json_out(sink, inp)
  File "fuzzer.py", line 23, in info_json_out
    list(rows)
  File "png.py", line 1148, in rows_from_interlace
    values = self._deinterlace(bs)
  File "png.py", line 877, in _deinterlace
    filter_type = raw[source_offset]
```

also confirmed against upstream pypng `0.0.21` — same crash, so this
is a real bug in the library, not an artefact of the workshop's
modifications.

## secondary finding: oom via huge interlaced dimensions (`poc_oom.png`)

`_deinterlace` pre-allocates the full output buffer before it reads
any data:

```python
vpi = self.width * self.planes * self.height
if self.bitdepth > 8:
    a = array("H", [0] * vpi)
else:
    a = bytearray([0] * vpi)
```

an `IHDR` with width 32, height ~16.7 million, bitdepth 16, rgb,
interlace 1 asks for ~3 gb before any validation — libfuzzer flags
it as oom. atheris found this one on its own during a 3-minute run
with the pngsuite seed corpus + chunk-type dictionary; `poc_oom.png`
is the artefact it wrote.

## note: the `IFUZZ` trap is dead code

inside `Reader.read()` the workshop added

```python
if type == b"IFUZZ":
    arr = [0, 1, 2]
    _ = arr[3]
    break
```

but chunk types come from `struct.unpack("!I4s", ...)` so `type` is
always exactly 4 bytes. `b"IFUZZ"` is 5 bytes, so the comparison is
permanently false and the intended `IndexError` never fires. the
fuzzer still finds a real bug above.

## files

- `poc.png` — 65 bytes, triggers the primary `IndexError`
- `poc_oom.png` — 595 bytes, triggers the memory blow-up (this is the
  artifact libfuzzer wrote during the run)
- `png.dict` — libfuzzer dictionary of png chunk type tokens used
  during the run
- the fuzzer harness itself is unchanged from the workshop's
  `Homework/pypng/code/fuzzer.py`

## how to reproduce

```
cd Homework/pypng
uv venv && source .venv/bin/activate
uv pip install atheris beautifulsoup4 html5lib
# (on macOS: atheris needs libfuzzer from brew's llvm; set
#  CLANG_BIN=/opt/homebrew/opt/llvm/bin/clang before pip install)

cd code
python fuzzer.py ../../val/poc.png        # primary: IndexError
python fuzzer.py ../../val/poc_oom.png    # secondary: OOM
```

to repro the organic find, extract the pngsuite images as a seed
corpus and run with the included dictionary:

```
python -c "import pngsuite; [open(f'seeds/{n}.png','wb').write(getattr(pngsuite,n)) \
  for n in dir(pngsuite) if not n.startswith('_') \
  and isinstance(getattr(pngsuite,n), bytes) \
  and getattr(pngsuite,n).startswith(b'\\x89PNG')]"
python fuzzer.py seeds/ -dict=../../val/png.dict -max_total_time=180
```
