# Font Converter: OTF → TTF

Converts OpenType (`.otf`) fonts to TrueType (`.ttf`).

**Use it here:** https://jbsbeefmarketing.github.io/Font_Converter/

1. Drag a `.otf` file onto the page (or click to choose one). You can drop several at once.
2. Wait for the progress bar.
3. Click **Download**. Several fonts come back as one `.zip`.

Fonts are converted in your browser and never uploaded anywhere. Works in Chrome and Edge.

## Notes

- Converts CFF-based OpenType fonts, which is what nearly all `.otf` files are. Variable (CFF2) fonts are not supported.
- Curves are converted from cubic to quadratic with at most 1 font unit of error, which isn't visible at any size.
- Hinting is not carried over. This doesn't matter for print, design tools, or modern screens.

## How it works

The page runs [fontTools](https://github.com/fonttools/fonttools) (Python) in the browser via [Pyodide](https://pyodide.org). The conversion code is in [`convert.py`](convert.py). It also works from the command line:

```
pip install fonttools
python convert.py MyFont.otf
```
