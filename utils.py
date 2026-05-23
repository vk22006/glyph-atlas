"""
GlyphAtlas — Utility helpers.
"""
import unicodedata


# ── Unicode helpers ───────────────────────────────────────────────────────────

def is_non_latin(char: str) -> bool:
    """Return True if `char` is NOT a basic Latin / ASCII printable character."""
    if not char:
        return False
    cp = ord(char)
    # Keep ASCII printable (0x20–0x7E) and common whitespace as-is
    if 0x20 <= cp <= 0x7E:
        return False
    return True


def get_codepoints(text: str) -> list[int]:
    """Return list of Unicode codepoints for all NON-LATIN characters in text."""
    return [ord(ch) for ch in text if is_non_latin(ch)]


def format_c_array(codepoints: list[int]) -> str:
    """Format codepoints as a C-style int array."""
    if not codepoints:
        return "int codepoints[] = {};"
    hex_vals = ", ".join(f"0x{cp:04x}" for cp in codepoints)
    return f"int codepoints[] = {{\n    {hex_vals}\n}};"


def format_cpp_vector(codepoints: list[int]) -> str:
    """Format codepoints as a C++ std::vector<int>."""
    if not codepoints:
        return "std::vector<int> codepoints = {};"
    hex_vals = ", ".join(f"0x{cp:04x}" for cp in codepoints)
    return f"std::vector<int> codepoints = {{\n    {hex_vals}\n}};"


def format_json(codepoints: list[int]) -> str:
    """Format codepoints as JSON array of hex strings."""
    if not codepoints:
        return "[]"
    items = ", ".join(f'"0x{cp:04x}"' for cp in codepoints)
    return f"[\n    {items}\n]"


def format_space_separated(codepoints: list[int]) -> str:
    """Format codepoints as space-separated hex values."""
    return " ".join(f"0x{cp:04x}" for cp in codepoints) if codepoints else ""


def format_unicode_escape(codepoints: list[int]) -> str:
    """Format codepoints as Unicode escape sequences."""
    return " ".join(f"U+{cp:04X}" for cp in codepoints) if codepoints else ""


def count_utf8_bytes(text: str) -> int:
    """Return UTF-8 byte count for non-latin characters only."""
    result = 0
    for ch in text:
        if is_non_latin(ch):
            result += len(ch.encode("utf-8"))
    return result


def get_common_usage(codepoints: list[int]) -> str:
    """Guess general script/usage of the codepoints."""
    if not codepoints:
        return "N/A"
    cats = set()
    for cp in codepoints:
        try:
            name = unicodedata.name(chr(cp), "")
            if "CJK" in name:
                cats.add("CJK")
            elif "ARABIC" in name:
                cats.add("Arabic")
            elif "CYRILLIC" in name:
                cats.add("Cyrillic")
            elif "GREEK" in name:
                cats.add("Greek")
            elif "HIRAGANA" in name or "KATAKANA" in name:
                cats.add("Japanese")
            elif "HANGUL" in name:
                cats.add("Korean")
            elif "DEVANAGARI" in name:
                cats.add("Devanagari")
            else:
                cats.add("General")
        except Exception:
            cats.add("General")
    return " / ".join(sorted(cats)) if cats else "General"


def format_count_statement(codepoints: list[int]) -> str:
    return f"int count = {len(codepoints)};"
