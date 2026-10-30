"""Read a code from a sticker photo with Tesseract.

OCR is a helper, not the source of truth: the user always confirms or fixes
the result before it is saved.

A 2026 sticker looks like this (black text on a light-blue security pattern):

    ELECTRIC COMPANY
    #928, NEED 927/928
    $5,000$ BEST BUY TECH SHOPPING SPREE*
    Scan/Enter code in McD app by 11/22/26 ...
    7KDQ4MVH9BXT3L
    *Must opt in to Rewards & register ...

The "NEED" list names every piece in the set, so a bare 9xx number is not
evidence of which piece this is; only "#928" and the property name are.
"""
import io
import re
from collections import Counter
from difflib import SequenceMatcher

import pytesseract
from PIL import Image, ImageOps

from app.season import Season

MAX_CANDIDATES = 5
# Phone photos are ~4000px and the sticker is often a small part of the frame, so keep
# plenty of detail. Tesseract sometimes skips a line at one size and reads it at another.
SIZES = (3200, 2400)

# Characters Tesseract confuses with ones that are actually printed. Only applied
# when the season says which characters codes use, and only to fill in missing ones.
LOOK_ALIKES = {
    "O": "Q0D", "0": "QD", "I": "1", "|": "1", "!": "1", "S": "5", "$": "5", "§": "5", "2": "Z",
    "A": "4", "U": "V", "Y": "V", "C": "G", ")": "J", "]": "J", "}": "J",
}


def prepare(data: bytes, max_side: int = SIZES[0]) -> Image.Image:
    """Upright, high-contrast, and a size Tesseract reads well.

    Uses the blue channel instead of plain grayscale: the sticker's light-blue
    security pattern turns almost white there, while the black text stays black.
    """
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB").getchannel("B")
    longest = max(img.size)
    if longest > max_side:
        img.thumbnail((max_side, max_side))
    elif longest < 1200:
        scale = 1200 / longest
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    return ImageOps.autocontrast(img, cutoff=1)


def read_text(data: bytes, season: Season | None = None) -> str:
    texts = []
    for size in SIZES:
        texts.append(_read_image(prepare(data, size), season))
        if not (season and season.code_alphabet) or _printed_codes(texts[-1], season):
            break
    return "\n".join(texts)


def _read_image(img: Image.Image, season: Season | None) -> str:
    texts, code_lines = [], []
    # psm 3 = automatic layout, psm 11 = scattered text; each one catches lines the other misses.
    for psm in (3, 11):
        lines = _lines(pytesseract.image_to_data(img, config=f"--psm {psm}", output_type=pytesseract.Output.DICT))
        texts.append("\n".join(text for text, _ in lines))
        if season and season.code_alphabet:
            code_lines += [box for text, box in lines if _could_be_code(text, season)
                           and not any(_same_line(box, seen) for seen in code_lines)]
    for box in code_lines:
        texts += _reread_code_line(img, box, season.code_alphabet)
    return "\n".join(texts)


def _lines(words: dict) -> list[tuple[str, tuple[int, int, int, int]]]:
    """Tesseract's words grouped back into lines, each with its bounding box."""
    lines: dict[tuple, list[int]] = {}
    for i, word in enumerate(words["text"]):
        if word.strip():
            lines.setdefault((words["block_num"][i], words["par_num"][i], words["line_num"][i]), []).append(i)
    result = []
    for ids in lines.values():
        left = min(words["left"][i] for i in ids)
        top = min(words["top"][i] for i in ids)
        right = max(words["left"][i] + words["width"][i] for i in ids)
        bottom = max(words["top"][i] + words["height"][i] for i in ids)
        result.append((" ".join(words["text"][i] for i in ids), (left, top, right, bottom)))
    return result


def _could_be_code(text: str, season: Season) -> bool:
    letters = re.sub(r"[^A-Za-z0-9]", "", text)
    if re.search(r"[a-z]{3}|[#/,]|NEED", text):  # ordinary words, or the "#921, NEED ..." line
        return False
    return abs(len(letters) - season.code_length) <= 4


def _same_line(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    return abs((a[1] + a[3]) - (b[1] + b[3])) < (a[3] - a[1])


def _reread_code_line(img: Image.Image, box: tuple[int, int, int, int], alphabet: str) -> list[str]:
    """Read one line again, allowing only the characters codes are printed with.

    Tesseract then picks the closest real character itself (a mono-font J it
    would otherwise call "I" comes back as J), which beats guessing afterwards.
    Each crop and contrast misses a character on some photos, so read a few
    variants and let them vote.
    """
    left, top, right, bottom = box
    height = bottom - top
    readings = []
    for pad_x, pad_y in ((height // 4, height // 4), (height, height // 2)):
        line = img.crop((max(left - pad_x, 0), max(top - pad_y, 0),
                         min(right + pad_x, img.width), min(bottom + pad_y, img.height)))
        line = line.resize((max(round(line.width * 64 / line.height), 1), 64), Image.LANCZOS)
        for variant in (line, line.point(lambda v: 255 if v > 128 else 0)):
            variant = ImageOps.expand(variant, border=20, fill=255)
            readings.append(pytesseract.image_to_string(
                variant, config=f"--psm 7 -c tessedit_char_whitelist={alphabet}").strip())
    return readings


# --- The code ---------------------------------------------------------------

def _fix_look_alikes(text: str, alphabet: str) -> str | None:
    """Swap misread characters for printed ones; None if something can't be fixed."""
    fixed = []
    for ch in text.upper():
        if ch in alphabet:
            fixed.append(ch)
            continue
        swap = next((c for c in LOOK_ALIKES.get(ch, "") if c in alphabet), None)
        if swap is None:
            return None
        fixed.append(swap)
    return "".join(fixed)


def _printed_codes(text: str, season: Season) -> Counter:
    """Exact-length codes in the season's alphabet, scored across lines and passes.

    A reading that needed look-alike fixes counts for less than one that didn't.
    """
    found: Counter = Counter()
    for line in text.splitlines():
        # The code may be split by stray spaces ("R79) 7BZL5NXGDV"), so try runs of neighbouring words.
        words = line.split()
        for i in range(len(words)):
            for j in range(i + 1, min(i + 5, len(words)) + 1):
                joined = re.sub(r"^[^A-Za-z0-9)\]}|$§]+|[^A-Za-z0-9)\]}|$§]+$", "", "".join(words[i:j]))
                if len(joined) != season.code_length:
                    continue
                code = _fix_look_alikes(joined, season.code_alphabet)
                if code:
                    found[code] += 1 if code == joined else 0.4
    return found


def _pattern_codes(text: str, season: Season) -> list[str]:
    """Anything matching the season's code pattern, for when the printed format isn't known or not found."""
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

    return sorted(found, key=score)


def find_code_candidates(text: str, season: Season) -> list[str]:
    """Strings in the OCR text that look like the code, best guesses first."""
    found: list[str] = []
    if season.code_length and season.code_alphabet:
        printed = _printed_codes(text, season)
        found = [code for code in sorted(printed, key=lambda c: -printed[c]) if season.is_valid_code(code)]
    for code in _pattern_codes(text, season):
        if code not in found:
            found.append(code)
    return found[:MAX_CANDIDATES]


# --- The piece --------------------------------------------------------------

def _letters(text: str) -> str:
    return re.sub(r"[^a-z]", "", text.lower())


def _name_scores(text: str, season: Season) -> dict[int, float]:
    """How closely any line matches each property name (1.0 = exact), tolerant of misread letters."""
    lines = [_letters(line) for line in text.splitlines()]
    # Names often wrap ("ELECTRIC" / "COMPANY"), so also try each line joined with the next.
    lines += [a + b for a, b in zip(lines, lines[1:])]
    lines = [line for line in lines if len(line) >= 4]
    scores = {}
    for piece in season.pieces.values():
        name = _letters(piece.name)
        best = 0.0
        for line in lines:
            if name in line:
                best = 1.0
                break
            if abs(len(line) - len(name)) <= max(3, len(name) // 3):
                best = max(best, SequenceMatcher(None, name, line).ratio())
        scores[piece.number] = best
    return scores


def find_piece(text: str, season: Season) -> int | None:
    """The piece on the sticker, from its "#921" number and property name."""
    upper = text.upper()
    # "#921, NEED ..." -- also when the "#" is misread or missing but "NEED" follows.
    own = Counter(int(n) for pair in re.findall(r"#\s*(9\d\d)(?!\d)|(?<!\d)(9\d\d)[,.]?\s*NEED", upper)
                  for n in pair if n)

    # The NEED list tells us the color set, which narrows down everything else.
    needed = {int(n) for m in re.finditer(r"NEED[\s:]*([\d/|lI\s]+)", upper) for n in re.findall(r"9\d\d", m.group(1))}
    allowed = {n for n in needed if n in season.pieces} or set(season.pieces)

    names = _name_scores(text, season)
    best, best_score = None, 0.0
    for number in allowed:
        name = names[number] if names[number] >= 0.75 else 0.0
        # A clear property name outweighs one misread digit; the two together are best.
        score = 4 * name + 1.5 * min(own[number], 2)
        if score > best_score:
            best, best_score = number, score
    return best
