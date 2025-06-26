#!/usr/bin/env python

# png.py - PNG encoder/decoder in pure Python
#
# Copyright (C) 2006 Johann C. Rocholl <johann@browsershots.org>
# Portions Copyright (C) 2009 David Jones <drj@pobox.com>
# And probably portions Copyright (C) 2006 Nicko van Someren <nicko@nicko.org>
#
# Original concept by Johann C. Rocholl.
#
# LICENCE (MIT)
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.



__version__ = "0.20250521.0"

import collections
import io
import itertools
import math
import re
import struct
import sys


import warnings
import zlib

from array import array


__all__ = ["ProtocolError", "Image", "Reader", "Writer", "write_chunks", "from_array"]



signature = struct.pack("8B", 137, 80, 78, 71, 13, 10, 26, 10)


adam7 = (
    (0, 0, 8, 8),
    (4, 0, 8, 8),
    (0, 4, 4, 8),
    (2, 0, 4, 4),
    (0, 2, 2, 4),
    (1, 0, 2, 2),
    (0, 1, 1, 2),
)


def adam7_generate(width, height):
    

    for xstart, ystart, xstep, ystep in adam7:
        if xstart >= width:
            continue
        yield ((xstart, y, xstep) for y in range(ystart, height, ystep))


Resolution = collections.namedtuple("_Resolution", "x y unit_is_meter")


def group(s, n):
    return list(zip(*[iter(s)] * n))


def isarray(x):
    return isinstance(x, array)


def check_palette(palette):


    
    if palette is None:
        return None

    p = list(palette)
    if not (0 < len(p) <= 256):
        raise ProtocolError(
            "a palette must have between 1 and 256 entries,"
            " see https://www.w3.org/TR/PNG/#11PLTE"
        )
    seen_triple = False
    for i, t in enumerate(p):
        if len(t) not in (3, 4):
            raise ProtocolError("palette entry %d: entries must be 3- or 4-tuples." % i)
        if len(t) == 3:
            seen_triple = True
        if seen_triple and len(t) == 4:
            raise ProtocolError(
                "palette entry %d: all 4-tuples must precede all 3-tuples" % i
            )
        for x in t:
            if int(x) != x or not (0 <= x <= 255):
                raise ProtocolError(
                    "palette entry %d: " "values must be integer: 0 <= x <= 255" % i
                )
    return p


def check_sizes(size, width, height):
    """
    """

    if not size:
        return width, height

    if len(size) != 2:
        raise ProtocolError(
            "size argument should be a pair (width, height) instead is %r" % (size,)
        )
    if width is not None and width != size[0]:
        raise ProtocolError(
            "size[0] (%r) and width (%r) should match when both are used."
            % (size[0], width)
        )
    if height is not None and height != size[1]:
        raise ProtocolError(
            "size[1] (%r) and height (%r) should match when both are used."
            % (size[1], height)
        )
    return size


def check_color(c, greyscale, which):
    """
    """

    if c is None:
        return c
    if greyscale:
        try:
            len(c)
        except TypeError:
            c = (c,)
        if len(c) != 1:
            raise ProtocolError("%s for greyscale must be 1-tuple" % which)
        if not is_natural(c[0]):
            raise ProtocolError("%s colour for greyscale must be integer" % which)
    else:
        if not (
            len(c) == 3 and is_natural(c[0]) and is_natural(c[1]) and is_natural(c[2])
        ):
            raise ProtocolError("%s colour must be a triple of integers" % which)
    return c


class Error(Exception):
    def __str__(self):
        return self.__class__.__name__ + ": " + " ".join(self.args)


class FormatError(Error):
    """
    """


class ProtocolError(Error):
    """
    """


class ChunkError(FormatError):
    pass


class Default:
    """"""


class Writer:
    

    def __init__(
        self,
        width=None,
        height=None,
        size=None,
        greyscale=Default,
        alpha=False,
        bitdepth=8,
        palette=None,
        transparent=None,
        background=None,
        gamma=None,
        compression=None,
        planes=None,
        colormap=None,
        maxval=None,
        chunk_limit=2 ** 20,
        physical=tuple(),
        x_pixels_per_unit=None,
        y_pixels_per_unit=None,
        unit_is_meter=False,
    ):




        width, height = check_sizes(size, width, height)
        del size

        if not is_natural(width) or not is_natural(height):
            raise ProtocolError(" width  and height must be integers")
        if width <= 0 or height <= 0:
            raise ProtocolError(" width and  height must be greater than zero")

        if width > 2 ** 31 - 1 or height > 2 ** 31 - 1:
            raise ProtocolError(" width and  height cannot exceed 2**31-1")

        if alpha and transparent is not None:
            raise ProtocolError(" transparent  colour not allowed with alpha channel")


        try:
            len(bitdepth)
        except TypeError:
            bitdepth = (bitdepth,)
        for b in bitdepth:
            valid = is_natural(b) and 1 <= b <= 16
            if not valid:
                raise ProtocolError(
                    " each bitdepth %r must  be a positive integer <= 16" % (bitdepth,)
                )


        palette = check_palette(palette)


        if colormap is None:
            colormap = bool(palette)


        if colormap and not palette:
            raise ProtocolError(" Palette  must be present when colormap is true")


        alpha = bool(alpha)
        colormap = bool(colormap)
        if greyscale is Default and palette:
            greyscale = False
        greyscale = bool(greyscale)
        if colormap:
            color_planes = 1
            planes = 1
        else:
            color_planes = (3, 1)[greyscale]
            planes = color_planes + alpha
        if len(bitdepth) == 1:
            bitdepth *= planes

        bitdepth, self.rescale = check_bitdepth_rescale(
            colormap, bitdepth, transparent, alpha, greyscale
        )


        if bitdepth < 8:
            assert greyscale or colormap
            assert not alpha
        if bitdepth > 8:
            assert not colormap

        transparent = check_color(transparent, greyscale, "transparent")
        background = check_color(background, greyscale, "background")

        if len(physical) == 0:
            pass
        elif len(physical) == 1:
            (x_pixels_per_unit,) = physical
            (y_pixels_per_unit,) = physical
        elif len(physical) == 2:
            x_pixels_per_unit, y_pixels_per_unit = physical
        elif len(physical) == 3:
            x_pixels_per_unit, y_pixels_per_unit, unit_is_meter = physical
        else:
            raise ProtocolError(
                " too many  items in `physical` parameter %r" % (physical,)
            )


        self.width = width
        self.height = height
        self.transparent = transparent
        self.background = background
        self.gamma = gamma
        self.greyscale = greyscale
        self.alpha = alpha
        self.colormap = colormap
        self.bitdepth = int(bitdepth)
        self.compression = compression
        self.chunk_limit = chunk_limit
        self.palette = palette
        self.x_pixels_per_unit = x_pixels_per_unit
        self.y_pixels_per_unit = y_pixels_per_unit
        self.unit_is_meter = bool(unit_is_meter)

        self.color_type = 4 * self.alpha + 2 * (not greyscale) + 1 * self.colormap
        assert self.color_type in (0, 2, 3, 4, 6)

        self.color_planes = color_planes
        self.planes = planes

        self.psize = (self.bitdepth / 8) * self.planes

    def write(self, outfile, rows):



        vpr = self.width * self.planes

        def check_rows(rows):

            for i, row in enumerate(rows):
                try:
                    wrong_length = len(row) != vpr
                except TypeError:

                    wrong_length = False
                if wrong_length:

                    raise ProtocolError(
                        " expected %d values but got %d values, in row %d"
                        % (vpr, len(row), i)
                    )
                yield row

        return self.write_passes(outfile, check_rows(rows))

    def write_passes(self, outfile, rows):




        if self.rescale:
            rows = rescale_rows(rows, self.rescale)

        if self.bitdepth < 8:
            rows = pack_rows(rows, self.bitdepth)
        elif self.bitdepth == 16:
            rows = unpack_rows(rows)

        return self.write_packed(outfile, rows)

    def write_packed(self, outfile, rows):


        self.write_preamble(outfile)


        if self.compression is not None:
            compressor = zlib.compressobj(self.compression)
        else:
            compressor = zlib.compressobj()


        data = array("B")


        irows = iter(rows)
        for i in range(self.height):
            try:
                row = next(irows)
            except StopIteration:
                raise ProtocolError(" not enough  rows: %d supplied; %d required" % (i, self.height))

            data.append(0)
            data.extend(row)
            if len(data) > self.chunk_limit:
                compressed = compressor.compress(data)
                if len(compressed):
                    write_chunk(outfile, b"IDAT", compressed)
                data = bytearray()

        compressed = compressor.compress(bytes(data))
        flushed = compressor.flush()
        if len(compressed) or len(flushed):
            write_chunk(outfile, b"IDAT", compressed + flushed)

        write_chunk(outfile, b"IEND")

    def write_preamble(self, outfile):



        try:
            outfile.write(signature)
        except TypeError as e:
            raise ProtocolError(" PNG  must be  written to a binary stream") from e


        interlace = 0
        write_chunk(
            outfile,
            b"IHDR",
            struct.pack(
                "!2I5B",
                self.width,
                self.height,
                self.bitdepth,
                self.color_type,
                0,
                0,
                interlace,
            ),
        )


        if self.gamma is not None:
            write_chunk(
                outfile, b"gAMA", struct.pack("!L", int(round(self.gamma * 1e5)))
            )


        if self.rescale:
            write_chunk(
                outfile,
                b"sBIT",
                struct.pack("%dB" % self.planes, *[s[0] for s in self.rescale]),
            )


        if self.palette:
            p, t = make_palette_chunks(self.palette)
            write_chunk(outfile, b"PLTE", p)
            if t:

                write_chunk(outfile, b"tRNS", t)


        if self.transparent is not None:
            if self.greyscale:
                fmt = "!1H"
            else:
                fmt = "!3H"
            write_chunk(outfile, b"tRNS", struct.pack(fmt, *self.transparent))


        if self.background is not None:
            if self.greyscale:
                fmt = "!1H"
            else:
                fmt = "!3H"
            write_chunk(outfile, b"bKGD", struct.pack(fmt, *self.background))


        if self.x_pixels_per_unit is not None and self.y_pixels_per_unit is not None:
            tup = (
                self.x_pixels_per_unit,
                self.y_pixels_per_unit,
                int(self.unit_is_meter),
            )
            write_chunk(outfile, b"pHYs", struct.pack("!LLB", *tup))

    def write_array(self, outfile, pixels):


        return self.write_passes(outfile, self.array_scanlines(pixels))

    def array_scanlines(self, pixels):



        vpr = self.width * self.planes
        stop = 0
        for y in range(self.height):
            start = stop
            stop = start + vpr
            yield pixels[start:stop]


def write_chunk(outfile, tag, data=b""):


    data = bytes(data)

    outfile.write(struct.pack("!I", len(data)))
    outfile.write(tag)
    outfile.write(data)
    checksum = zlib.crc32(tag)
    checksum = zlib.crc32(data, checksum)
    checksum &= 2 ** 32 - 1
    outfile.write(struct.pack("!I", checksum))


def write_chunks(out, chunks):


    out.write(signature)
    for chunk in chunks:
        write_chunk(out, *chunk)


def rescale_rows(rows, rescale):



    fs = [float(2 ** s[1] - 1) / float(2 ** s[0] - 1) for s in rescale]


    target_bitdepths = set(s[1] for s in rescale)
    assert len(target_bitdepths) == 1
    (target_bitdepth,) = target_bitdepths
    typecode = "BH"[target_bitdepth > 8]


    n_chans = len(rescale)

    for row in rows:
        rescaled_row = array(typecode, iter(row))
        for i in range(n_chans):
            channel = array(typecode, (int(round(fs[i] * x)) for x in row[i::n_chans]))
            rescaled_row[i::n_chans] = channel
        yield rescaled_row


def pack_rows(rows, bitdepth):


    assert bitdepth < 8
    assert 8 % bitdepth == 0


    spb = int(8 / bitdepth)

    def make_byte(block):


        res = 0
        for v in block:
            res = (res << bitdepth) + v
        return res

    for row in rows:
        a = bytearray(row)

        n = float(len(a))
        extra = math.ceil(n / spb) * spb - n
        a.extend([0] * int(extra))

        blocks = group(a, spb)
        yield bytearray(make_byte(block) for block in blocks)


def unpack_rows(rows):

    for row in rows:
        fmt = "!%dH" % len(row)
        yield bytearray(struct.pack(fmt, *row))


def make_palette_chunks(palette):


    p = bytearray()
    t = bytearray()

    for x in palette:
        p.extend(x[0:3])
        if len(x) > 3:
            t.append(x[3])
    if t:
        return p, t
    return p, None


def check_bitdepth_rescale(colormap, bitdepth, transparent, alpha, greyscale):


    if colormap:
        if len(bitdepth) != 1:
            raise ProtocolError(" with colormap, only a single bitdepth may be used")
        (bitdepth,) = bitdepth
        if bitdepth not in (1, 2, 4, 8):
            raise ProtocolError(" with colormap, bitdepth must be 1, 2, 4, or 8")
        if transparent is not None:
            raise ProtocolError("Transparent and colormap not compatible")
        if alpha:
            raise ProtocolError("Alpha and colormap not compatible")
        if greyscale:
            raise ProtocolError("Greyscale and colormap not compatible")
        return bitdepth, None



    if greyscale and not alpha:

        (bitdepth,) = bitdepth
        if bitdepth in (1, 2, 4, 8, 16):
            return bitdepth, None
        if bitdepth > 8:
            targetbitdepth = 16
        elif bitdepth == 3:
            targetbitdepth = 4
        else:
            assert bitdepth in (5, 6, 7)
            targetbitdepth = 8
        return targetbitdepth, [(bitdepth, targetbitdepth)]

    assert alpha or not greyscale

    depth_set = tuple(set(bitdepth))
    if depth_set in [(8,), (16,)]:

        (bitdepth,) = depth_set
        return bitdepth, None

    targetbitdepth = (8, 16)[max(bitdepth) > 8]
    return targetbitdepth, [(b, targetbitdepth) for b in bitdepth]



RegexModeDecode = re.compile("(LA?|RGBA?);?([0-9]*)", flags=re.IGNORECASE)


def from_array(a, mode=None, info={}):



    info = dict(info)


    match = RegexModeDecode.match(mode)
    if not match:
        raise Error("mode string should be 'RGB' or 'L;16' or similar")

    mode, bitdepth = match.groups()
    if bitdepth:
        bitdepth = int(bitdepth)


    if "greyscale" in info:
        if bool(info["greyscale"]) != ("L" in mode):
            raise ProtocolError("info['greyscale'] should match mode")
    info["greyscale"] = "L" in mode

    alpha = "A" in mode
    if "alpha" in info:
        if bool(info["alpha"]) != alpha:
            raise ProtocolError("info['alpha'] should match mode")
    info["alpha"] = alpha


    if bitdepth:
        if info.get("bitdepth") and bitdepth != info["bitdepth"]:
            raise ProtocolError(
                "bitdepth (%d) should match bitdepth of info (%d)"
                % (bitdepth, info["bitdepth"])
            )
        info["bitdepth"] = bitdepth


    width = info.get("width")

    if "height" not in info:
        try:
            info["height"] = len(a)
        except TypeError:
            raise ProtocolError("len(a) no work, supply info['height'] instead.")
    height = info["height"]

    planes = len(mode)
    if "planes" in info:
        if info["planes"] != planes:
            raise Error("info['planes'] should match mode.")


    a, t = itertools.tee(a)
    row = next(t)
    del t

    if "width" not in info:
        width = len(row) // planes
        info["width"] = width

    if "bitdepth" not in info:
        bitdepth = 8
        info["bitdepth"] = bitdepth

    for thing in ["width", "height", "bitdepth", "greyscale", "alpha"]:
        assert thing in info

    return Image(a, info)



fromarray = from_array


class Image:


    def __init__(self, rows, info):


        self.rows = rows
        self.info = info

    def save(self, file):


        w = Writer(**self.info)

        with open(file, "wb") as fd:
            w.write(fd, self.rows)

    def stream(self):


        self.rows = list(self.rows)

    def write(self, file):


        w = Writer(**self.info)
        w.write(file, self.rows)


class Reader:


    def __init__(self, _guess=None, filename=None, file=None, bytes=None):

        keywords_supplied = (
            (_guess is not None)
            + (filename is not None)
            + (file is not None)
            + (bytes is not None)
        )
        if keywords_supplied != 1:
            raise TypeError("reader()  takes exactly 1 argument")

        self.signature = None
        self.transparent = None

        self.atchunk = None

        if _guess is not None:
            if isarray(_guess):
                bytes = _guess
            elif isinstance(_guess, str):
                filename = _guess
            elif hasattr(_guess, "read"):
                file = _guess

        if bytes is not None:
            self.file = io.BytesIO(bytes)
        elif filename is not None:
            self.file = open(filename, "rb")
        elif file is not None:
            self.file = file
        else:
            raise ProtocolError("expecting filename, file or bytes array")

    def chunk(self):


        self.validate_signature()


        if not self.atchunk:
            self.atchunk = self._chunk_len_type()
        if not self.atchunk:
            raise ChunkError("no more chunks.")
        length, type = self.atchunk
        self.atchunk = None

        data = self.file.read(length)
        if len(data) != length:
            raise ChunkError(
                "chunk %s too short for required %i octets." % (type, length)
            )

        checksum = self.file.read(4)
        if len(checksum) != 4:
            raise ChunkError("Chunk %s too short for checksum." % type)


        return type, data

    def chunks(self):


        while True:
            t, v = self.chunk()
            yield t, v
            if t == b"IEND":
                break

    def chunk_of_type(self, type):


        target = bytes(type, "ascii")

        while True:
            t, v = self.chunk()
            if t == target:
                return t, v

    def undo_filter(self, filter_type, scanline, previous):



        result = scanline

        if filter_type == 0:
            return result

        if filter_type not in (1, 2, 3, 4):
            raise FormatError(
                "invalid PNG Filter Type.  "
                "See https://www.w3.org/TR/2003/REC-PNG-20031110/#9Filters ."
            )


        fu = max(1, self.psize)


        if not previous:
            previous = bytearray([0] * len(scanline))


        fn = (
            None,
            undo_filter_sub,
            undo_filter_up,
            undo_filter_average,
            undo_filter_paeth,
        )[filter_type]
        fn(fu, scanline, previous, result)
        return result

    def _deinterlace(self, raw):



        vpr = self.width * self.planes


        vpi = vpr * self.height


        if self.bitdepth > 8:
            a = array("H", [0] * vpi)
        else:
            a = bytearray([0] * vpi)
        source_offset = 0

        for lines in adam7_generate(self.width, self.height):

            recon = None
            for x, y, xstep in lines:

                ppr = int(math.ceil((self.width - x) / float(xstep)))

                row_size = int(math.ceil(self.psize * ppr))

                filter_type = raw[source_offset]
                source_offset += 1
                scanline = raw[source_offset : source_offset + row_size]
                source_offset += row_size
                recon = self.undo_filter(filter_type, scanline, recon)

                flat = self._bytes_to_values(recon, width=ppr)
                if xstep == 1:
                    assert x == 0
                    offset = y * vpr
                    a[offset : offset + vpr] = flat
                else:
                    offset = y * vpr + x * self.planes
                    end_offset = (y + 1) * vpr
                    skip = self.planes * xstep
                    for i in range(self.planes):
                        a[offset + i : end_offset : skip] = flat[i :: self.planes]

        return a

    def _iter_bytes_to_values(self, byte_rows):


        for row in byte_rows:
            yield self._bytes_to_values(row)

    def _bytes_to_values(self, bs, width=None):


        if self.bitdepth == 8:
            return bytearray(bs)
        if self.bitdepth == 16:
            return array("H", struct.unpack("!%dH" % (len(bs) // 2), bs))

        assert self.bitdepth < 8
        if width is None:
            width = self.width

        spb = 8 // self.bitdepth
        out = bytearray()
        mask = 2 ** self.bitdepth - 1
        shifts = [self.bitdepth * i for i in reversed(range(spb))]
        for o in bs:
            out.extend([mask & (o >> i) for i in shifts])
        return out[:width]

    def _iter_straight_packed(self, byte_blocks):



        rb = self.row_bytes
        a = bytearray()

        recon = None
        for some_bytes in byte_blocks:
            a.extend(some_bytes)
            while len(a) >= rb + 1:
                filter_type = a[0]
                scanline = a[1 : rb + 1]
                del a[: rb + 1]
                recon = self.undo_filter(filter_type, scanline, recon)
                yield recon
        if len(a) != 0:

            raise FormatError("wrong  size for decompressed IDAT chunk.")
        assert len(a) == 0

    def validate_signature(self):


        if self.signature:
            return
        self.signature = self.file.read(8)
        if len(self.signature) == 0:
            raise EOFError("end of PNG stream.")
        if self.signature != signature:
            raise FormatError("PNG  file has invalid signature.")

    def preamble(self):


        self.validate_signature()

        while True:
            if not self.atchunk:
                self.atchunk = self._chunk_len_type()
                if self.atchunk is None:
                    raise FormatError("this  PNG file has no IDAT chunks.")
            if self.atchunk[1] == b"IDAT":
                return
            self.process_chunk()

    def _chunk_len_type(self):


        x = self.file.read(8)
        if not x:
            return None
        if len(x) != 8:
            raise FormatError("end of  file whilst reading chunk length and type.")
        length, type = struct.unpack("!I4s", x)
        if length > 2 ** 31 - 1:
            raise FormatError("chunk %s is too large: %d." % (type, length))

        type_bytes = set(bytearray(type))
        if not (type_bytes <= set(range(65, 91)) | set(range(97, 123))):
            raise FormatError("chunk %r has invalid Chunk Type." % list(type))
        return length, type

    def process_chunk(self):

        type, data = self.chunk()
        method = "_process_" + type.decode("ascii")
        m = getattr(self, method, None)
        if m:
            m(data)

    def _process_IHDR(self, data):

        if len(data) != 13:
            raise FormatError("IHDR  chunk  has incorrect length.")
        (
            self.width,
            self.height,
            self.bitdepth,
            self.color_type,
            self.compression,
            self.filter,
            self.interlace,
        ) = struct.unpack("!2I5B", data)

        check_bitdepth_colortype(self.bitdepth, self.color_type)

        if self.compression != 0:
            raise FormatError("unknown  compression method %d" % self.compression)
        if self.filter != 0:
            raise FormatError(
                "unknown  filter method %d,"
                " see https://www.w3.org/TR/2003/REC-PNG-20031110/#9Filters ."
                % self.filter
            )
        if self.interlace not in (0, 1):
            raise FormatError(
                "unknown  interlace method %d, see "
                "https://www.w3.org/TR/2003/REC-PNG-20031110/#8InterlaceMethods"
                " ." % self.interlace
            )


        colormap = bool(self.color_type & 1)
        greyscale = not (self.color_type & 2)
        alpha = bool(self.color_type & 4)
        color_planes = (3, 1)[greyscale or colormap]
        planes = color_planes + alpha

        self.colormap = colormap
        self.greyscale = greyscale
        self.alpha = alpha
        self.color_planes = color_planes
        self.planes = planes
        self.psize = float(self.bitdepth) / float(8) * planes
        if int(self.psize) == self.psize:
            self.psize = int(self.psize)
        self.row_bytes = int(math.ceil(self.width * self.psize))

        self.plte = None

        self.trns = None

        self.sbit = None

    def _process_PLTE(self, data):

        if self.plte:
            warnings.warn("Multiple  PLTE chunks present.")
        self.plte = data
        if len(data) % 3 != 0:
            raise FormatError("PLTE  chunk's  length should be a multiple of 3.")
        if len(data) > (2 ** self.bitdepth) * 3:
            raise FormatError("PLTE chunk is too long.")
        if len(data) == 0:
            raise FormatError("Empty  PLTE  is not allowed.")

    def _process_bKGD(self, data):
        try:
            if self.colormap:
                if not self.plte:
                    warnings.warn("PLTE  chunk  is required before bKGD chunk.")
                self.background = struct.unpack("B", data)
            else:
                self.background = struct.unpack("!%dH" % self.color_planes, data)
        except struct.error:
            raise FormatError("bKGD  chunk  has incorrect length.")

    def _process_tRNS(self, data):

        self.trns = data
        if self.colormap:
            if not self.plte:
                warnings.warn("PLTE  chunk  is required before tRNS chunk.")
            else:
                if len(data) > len(self.plte) / 3:

                    raise FormatError("tRNS  chunk  is too long.")
        else:
            if self.alpha:
                raise FormatError(
                    "tRNS  chunk  is not valid with colour type %d." % self.color_type
                )
            try:
                self.transparent = struct.unpack("!%dH" % self.color_planes, data)
            except struct.error:
                raise FormatError("tRNS  chunk  has incorrect length.")

    def _process_gAMA(self, data):
        try:
            self.gamma = struct.unpack("!L", data)[0] / 100000.0
        except struct.error:
            raise FormatError("gAMA  chunk  has incorrect length.")

    def _process_sBIT(self, data):
        self.sbit = data
        if (
            self.colormap
            and len(data) != 3
            or not self.colormap
            and len(data) != self.planes
        ):
            raise FormatError("sBIT  chunk  has incorrect length.")

    def _process_pHYs(self, data):

        self.phys = data
        fmt = "!LLB"
        if len(data) != struct.calcsize(fmt):
            raise FormatError("pHYs  chunk  has incorrect length.")
        self.x_pixels_per_unit, self.y_pixels_per_unit, unit = struct.unpack(fmt, data)
        self.unit_is_meter = bool(unit)

    def read(self):


        def iteridat():

            while True:
                type, data = self.chunk()
                if type == b"IEND":

                    break
                if type == b"IFUZZ":
                    arr = [0,1,2]
                    _ = arr[3]
                    break
                if type != b"IDAT":
                    continue

                if self.colormap and not self.plte:
                    warnings.warn("PLTE  chunk  is required before IDAT chunk")
                yield data

        self.preamble()
        raw = decompress(iteridat())

        if self.interlace:

            def rows_from_interlace():


                bs = bytearray(itertools.chain(*raw))
                arraycode = "BH"[self.bitdepth > 8]

                values = self._deinterlace(bs)
                vpr = self.width * self.planes
                for i in range(0, len(values), vpr):
                    row = array(arraycode, values[i : i + vpr])
                    yield row

            rows = rows_from_interlace()
        else:
            rows = self._iter_bytes_to_values(self._iter_straight_packed(raw))
        info = dict()
        for attr in "greyscale alpha planes bitdepth".split():
            info[attr] = getattr(self, attr)
        info["size"] = (self.width, self.height)
        for attr in "gamma transparent background".split():
            a = getattr(self, attr, None)
            if a is not None:
                info[attr] = a
        if getattr(self, "x_pixels_per_unit", None):
            info["physical"] = Resolution(
                self.x_pixels_per_unit, self.y_pixels_per_unit, self.unit_is_meter
            )
        if self.plte:
            info["palette"] = self.palette()
        return self.width, self.height, rows, info

    def read_flat(self):


        x, y, pixel, info = self.read()
        arraycode = "BH"[info["bitdepth"] > 8]
        pixel = array(arraycode, itertools.chain(*pixel))
        return x, y, pixel, info

    def palette(self, alpha="natural"):


        if not self.plte:
            raise FormatError("required  PLTE  chunk is missing in colour type 3 image.")
        plte = group(array("B", self.plte), 3)
        if self.trns or alpha == "force":
            trns = array("B", self.trns or [])
            trns.extend([255] * (len(plte) - len(trns)))
            plte = [pal + (a,) for pal, a in zip(plte, trns)]
        return plte

    def asDirect(self):
        

        self.preamble()


        if not self.colormap and not self.trns and not self.sbit:
            return self.read()

        x, y, pixels, info = self.read()

        if self.colormap:
            info["colormap"] = False
            info["alpha"] = bool(self.trns)
            info["bitdepth"] = 8
            info["planes"] = 3 + bool(self.trns)
            palette = self.palette()

            def iterpal(pixels):
                for row in pixels:
                    row = [palette[x] for x in row]
                    yield array("B", itertools.chain(*row))

            pixels = iterpal(pixels)
        elif self.trns:

            it = self.transparent
            maxval = 2 ** info["bitdepth"] - 1
            planes = info["planes"]
            info["alpha"] = True
            info["planes"] += 1
            del info["transparent"]
            typecode = "BH"[info["bitdepth"] > 8]

            def itertrns(pixels):
                for row in pixels:

                    row = group(row, planes)
                    opa = [maxval * (pix != it) for pix in row]
                    yield array(
                        typecode,
                        itertools.chain(*[pix + (a,) for pix, a in zip(row, opa)]),
                    )

            pixels = itertrns(pixels)

        return x, y, pixels, info

    def asRGB(self):


        width, height, pixels, info = self.asDirect()
        if info["alpha"]:
            raise Error("will  not  convert image with alpha channel to RGB")
        if not info["greyscale"]:
            return width, height, pixels, info
        info["greyscale"] = False
        info["planes"] = 3

        if info["bitdepth"] > 8:

            def newarray():
                return array("H", [0])

        else:

            def newarray():
                return bytearray([0])

        def iterrgb():
            for row in pixels:
                a = newarray() * 3 * width
                for i in range(3):
                    a[i::3] = row
                yield a

        return width, height, iterrgb(), info

    def asRGBA(self):


        width, height, pixels, info = self.asDirect()
        if info["alpha"] and not info["greyscale"]:
            return width, height, pixels, info
        typecode = "BH"[info["bitdepth"] > 8]
        maxval = 2 ** info["bitdepth"] - 1
        maxbuffer = struct.pack("=" + typecode, maxval) * 4 * width

        if info["bitdepth"] > 8:

            def newarray():
                return array("H", maxbuffer)

        else:

            def newarray():
                return bytearray(maxbuffer)

        if info["alpha"] and info["greyscale"]:

            def convert():
                for row in pixels:

                    a = newarray()
                    convert_la_to_rgba(row, a)
                    yield a

        elif info["greyscale"]:

            def convert():
                for row in pixels:
                    a = newarray()
                    convert_l_to_rgba(row, a)
                    yield a

        else:
            assert not info["alpha"] and not info["greyscale"]


            def convert():
                for row in pixels:
                    a = newarray()
                    convert_rgb_to_rgba(row, a)
                    yield a

        info["alpha"] = True
        info["greyscale"] = False
        info["planes"] = 4
        return width, height, convert(), info


def decompress(data_blocks):



    d = zlib.decompressobj()

    for data in data_blocks:

        yield bytearray(d.decompress(data))
    yield bytearray(d.flush())


def check_bitdepth_colortype(bitdepth, colortype):


    if bitdepth not in (1, 2, 4, 8, 16):
        raise FormatError("invalid bit depth %d" % bitdepth)
    if colortype not in (0, 2, 3, 4, 6):
        raise FormatError("invalid colour type %d" % colortype)

    if colortype & 1 and bitdepth > 8:
        raise FormatError(
            "Indexed  images  (colour type %d) cannot"
            " have bitdepth > 8 (bit depth %d)."
            " See https://www.w3.org/TR/2003/REC-PNG-20031110/#table111 ."
            % (bitdepth, colortype)
        )
    if bitdepth < 8 and colortype not in (0, 3):
        raise FormatError(
            "Illegal  combination  of bit depth (%d)"
            " and  colour type (%d)."
            " See  https://www.w3.org/TR/2003/REC-PNG-20031110/#table111 ."
            % (bitdepth, colortype)
        )


def is_natural(x):

    try:
        is_integer = int(x) == x
    except (TypeError, ValueError):
        return False
    return is_integer and x >= 0


def undo_filter_sub(filter_unit, scanline, previous, result):


    ai = 0

    for i in range(filter_unit, len(result)):
        x = scanline[i]
        a = result[ai]
        result[i] = (x + a) & 0xFF
        ai += 1


def undo_filter_up(filter_unit, scanline, previous, result):


    for i in range(len(result)):
        x = scanline[i]
        b = previous[i]
        result[i] = (x + b) & 0xFF


def undo_filter_average(filter_unit, scanline, previous, result):


    ai = -filter_unit
    for i in range(len(result)):
        x = scanline[i]
        if ai < 0:
            a = 0
        else:
            a = result[ai]
        b = previous[i]
        result[i] = (x + ((a + b) >> 1)) & 0xFF
        ai += 1


def undo_filter_paeth(filter_unit, scanline, previous, result):



    ai = -filter_unit
    for i in range(len(result)):
        x = scanline[i]
        if ai < 0:
            a = c = 0
        else:
            a = result[ai]
            c = previous[ai]
        b = previous[i]
        p = a + b - c
        pa = abs(p - a)
        pb = abs(p - b)
        pc = abs(p - c)
        if pa <= pb and pa <= pc:
            pr = a
        elif pb <= pc:
            pr = b
        else:
            pr = c
        result[i] = (x + pr) & 0xFF
        ai += 1


def convert_la_to_rgba(row, result):
    for i in range(3):
        result[i::4] = row[0::2]
    result[3::4] = row[1::2]


def convert_l_to_rgba(row, result):

    for i in range(3):
        result[i::4] = row


def convert_rgb_to_rgba(row, result):

    for i in range(3):
        result[i::4] = row[i::3]



def binary_stdin():


    return sys.stdin.buffer


def binary_stdout():


    stdout = sys.stdout.buffer


    if sys.platform == "win32":
        import msvcrt
        import os

        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

    return stdout


def cli_open(path):
    if path == "-":
        return binary_stdin()
    return open(path, "rb")


def main(argv):

    print(__version__, __file__)


if __name__ == "__main__":
    try:
        main(sys.argv)
    except Error as e:
        print(e, file=sys.stderr)
