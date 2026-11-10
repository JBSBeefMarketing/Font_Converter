"""Convert CFF-flavored OpenType fonts (.otf) to TrueType (.ttf).

Used by the web page (via Pyodide) and runnable from the command line:

    pip install fonttools
    python convert.py MyFont.otf [MoreFonts.otf ...]
"""

import io
import sys
import zipfile
from pathlib import Path

from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable

# Max distance (font units) between the original cubic curves and the
# quadratic approximation. 1.0 is visually lossless for typical 1000-2048 UPM fonts.
MAX_ERR = 1.0


class ConversionError(Exception):
    pass


def _glyphs_to_quadratic(glyph_set, max_err, progress=None):
    quad_glyphs = {}
    names = list(glyph_set.keys())
    for i, name in enumerate(names):
        tt_pen = TTGlyphPen(glyph_set)
        # CFF contours run counter-clockwise, TrueType clockwise.
        glyph_set[name].draw(Cu2QuPen(tt_pen, max_err, reverse_direction=True))
        quad_glyphs[name] = tt_pen.glyph()
        if progress and i % 25 == 0:
            progress(i / len(names))
    return quad_glyphs


def otf_to_ttf(font, max_err=MAX_ERR, progress=None):
    if font.sfntVersion != "OTTO" or "CFF " not in font:
        if "CFF2" in font:
            raise ConversionError("Variable (CFF2) fonts are not supported.")
        if "glyf" in font:
            raise ConversionError("This font is already TrueType; just rename it to .ttf.")
        raise ConversionError("Not a CFF-based OpenType font.")

    glyph_order = font.getGlyphOrder()

    font["loca"] = newTable("loca")
    font["glyf"] = glyf = newTable("glyf")
    glyf.glyphOrder = glyph_order
    glyf.glyphs = _glyphs_to_quadratic(font.getGlyphSet(), max_err, progress)
    del font["CFF "]
    if "VORG" in font:
        del font["VORG"]
    glyf.compile(font)

    # TrueType requires left side bearing == xMin.
    hmtx = font["hmtx"]
    for name, glyph in glyf.glyphs.items():
        if hasattr(glyph, "xMin"):
            hmtx[name] = (hmtx[name][0], glyph.xMin)

    font["maxp"] = maxp = newTable("maxp")
    maxp.tableVersion = 0x00010000
    maxp.maxZones = 1
    maxp.maxTwilightPoints = 0
    maxp.maxStorage = 0
    maxp.maxFunctionDefs = 0
    maxp.maxInstructionDefs = 0
    maxp.maxStackElements = 0
    maxp.maxSizeOfInstructions = 0
    maxp.maxComponentElements = 0
    maxp.compile(font)

    post = font["post"]
    post.formatType = 2.0
    post.extraNames = []
    post.mapping = {}
    post.glyphOrder = glyph_order
    try:
        post.compile(font)
    except OverflowError:
        post.formatType = 3.0

    font["head"].glyphDataFormat = 0
    font.sfntVersion = "\x00\x01\x00\x00"


def convert_bytes(data, progress=None):
    """Take .otf file bytes, return .ttf file bytes."""
    try:
        font = TTFont(io.BytesIO(bytes(data)))
    except Exception as e:
        raise ConversionError(f"Could not read font file ({e}).")
    otf_to_ttf(font, progress=progress)
    out = io.BytesIO()
    font.save(out)
    return out.getvalue()


def zip_files(names, blobs):
    """Bundle several converted fonts into one .zip (used by the web page)."""
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for name, blob in zip(names, blobs):
            z.writestr(name, bytes(blob))
    return out.getvalue()


def main(paths):
    if not paths:
        print(__doc__)
        return 1
    failed = 0
    for p in map(Path, paths):
        try:
            p.with_suffix(".ttf").write_bytes(convert_bytes(p.read_bytes()))
            print(f"{p} -> {p.with_suffix('.ttf')}")
        except (ConversionError, OSError) as e:
            print(f"{p}: {e}", file=sys.stderr)
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
