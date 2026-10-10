"""Read a code from a sticker photo with Tesseract.

OCR is a helper, not the source of truth: the user always confirms or fixes
the result before it is saved.
"""
import io
import re

import pytesseract
from PIL import Image, ImageOps

from app.season import Season

MAX_CANDIDATES = 5


def prepare(data: bytes) -> Image.Image:
    """Upright, grayscale, high-contrast, and a size Tesseract reads well."""
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("L")
    longest = max(img.size)
    if longest > 2400:
        img.thumbnail((2400, 2400))
    elif longest < 1200:
        scale = 1200 / longest
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    return ImageOps.autocontrast(img, cutoff=1)


def read_text(data: bytes) -> str:
    img = prepare(data)
    # psm 6 = a block of text, psm 11 = scattered text; stickers can look like either.
    # The inverted pass catches light text on a dark color band (like the property name).
    passes = [(img, 6), (img, 11), (ImageOps.invert(img), 3)]
    return "\n".join(pytesseract.image_to_string(image, config=f"--psm {psm}") for image, psm in passes)


def find_code_candidates(text: str, season: Season) -> list[str]:
    """Strings in the OCR text that match the season's code pattern, best guesses first."""
    # Property names and piece numbers are printed near the code; drop them so they aren't mistaken for it.
    text = text.upper()
    for piece in season.pieces.values():
        name = r"[\s.&]*".join(re.escape(word) for word in re.findall(r"[A-Z]+", piece.name.upper()))
        text = re.sub(name, " ", text)
    text = re.sub(r"(?<![A-Z0-9])9\d\d(?![A-Z0-9])", " ", text)

    found: list[str] = []
    for line in text.splitlines():
        # A code may be printed in groups ("ABCD 1234 EFGH"), so try the whole run and each piece of it.
        for run in re.finditer(r"[A-Z0-9]+(?:[ \-][A-Z0-9]+)*", line):
            options = [run.group()] + run.group().replace("-", " ").split()
            for option in options:
                candidate = re.sub(r"[ \-]", "", option)
                if season.is_valid_code(candidate) and candidate not in found:
                    found.append(candidate)

    def score(code: str) -> tuple:
        mixed = any(c.isdigit() for c in code) and any(c.isalpha() for c in code)
        return (not mixed, -len(code))

    return sorted(found, key=score)[:MAX_CANDIDATES]


def find_piece(text: str, season: Season) -> int | None:
    """A piece number (e.g. 921) or a property name printed on the sticker."""
    for match in re.finditer(r"(?<!\d)(9\d\d)(?!\d)", text):
        if int(match.group(1)) in season.pieces:
            return int(match.group(1))
    flat = re.sub(r"[^a-z]", "", text.lower())
    # Longest names first, so "Pennsylvania Railroad" wins over "Pennsylvania Avenue" fragments.
    for piece in sorted(season.pieces.values(), key=lambda p: -len(p.name)):
        if re.sub(r"[^a-z]", "", piece.name.lower()) in flat:
            return piece.number
    return None
