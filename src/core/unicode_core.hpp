#pragma once

#include <cstdint>
#include <cstddef>
#include <string>
#include <string_view>
#include <vector>

namespace glyph_atlas::core {

/**
 * Configuration options for formatting Unicode codepoints.
 */
struct FormatOptions {
    bool include_latin = false;
    bool prefix = true;        // e.g. "0x"
    bool uppercase = false;     // uppercase hex digits (0x4F60 vs 0x4f60)
};

/**
 * Decodes a UTF-8 encoded string into Unicode codepoints (scalar values).
 * Validates against overlong encodings, out-of-bounds codepoints, and UTF-16 surrogates.
 */
std::vector<uint32_t> decode_utf8(std::string_view text);

/**
 * Encodes a single Unicode codepoint into UTF-8.
 */
std::string encode_utf8(uint32_t cp);

/**
 * Encodes a list of Unicode codepoints into a UTF-8 string.
 */
std::string encode_utf8(const std::vector<uint32_t>& codepoints);

/**
 * Checks if a Unicode codepoint is non-Latin.
 * All Basic Latin / ASCII characters (0x00 to 0x7F) return false.
 */
bool is_non_latin(uint32_t cp) noexcept;

/**
 * Checks if an ASCII whitespace character (space, tab, newline, CR, FF, VT).
 */
bool is_whitespace(uint32_t cp) noexcept;

/**
 * Returns the UTF-8 byte length for a given codepoint.
 */
size_t utf8_byte_length(uint32_t cp) noexcept;

/**
 * Extracts codepoints from text using the given Latin-inclusion setting.
 * When include_latin is false: excludes all Basic Latin / ASCII (0x00-0x7F) characters.
 * When include_latin is true: includes all characters except basic whitespace.
 */
std::vector<uint32_t> get_codepoints(std::string_view text, bool include_latin = false);

/**
 * Formats a single codepoint as hexadecimal string (e.g. "0x4f60", "0x4F60", "4f60").
 * Zero-pads to at least 4 digits for BMP characters, expands for supplementary plane.
 */
std::string format_hex(uint32_t cp, bool prefix = true, bool uppercase = false);

/**
 * Formats codepoints as a C-style array:
 * "int codepoints[] = {\n    0x4f60, 0x597d\n};" or "int codepoints[] = {};"
 */
std::string format_c_array(const std::vector<uint32_t>& codepoints, bool prefix = true, bool uppercase = false);

/**
 * Formats codepoints as a C++ std::vector<int>:
 * "std::vector<int> codepoints = {\n    0x4f60, 0x597d\n};" or "std::vector<int> codepoints = {};"
 */
std::string format_cpp_vector(const std::vector<uint32_t>& codepoints, bool prefix = true, bool uppercase = false);

/**
 * Formats codepoints as a JSON array of hex strings:
 * "[\n    \"0x4f60\", \"0x597d\"\n]" or "[]"
 */
std::string format_json(const std::vector<uint32_t>& codepoints, bool prefix = true, bool uppercase = false);

/**
 * Formats codepoints as space-separated hex values:
 * "0x4f60 0x597d" or ""
 */
std::string format_space_separated(const std::vector<uint32_t>& codepoints, bool prefix = true, bool uppercase = false);

/**
 * Formats codepoints as Unicode escape sequences:
 * "U+4f60 U+597d" or ""
 */
std::string format_unicode_escape(const std::vector<uint32_t>& codepoints, bool uppercase = false);

/**
 * Formats the count statement:
 * "int count = N;"
 */
std::string format_count_statement(const std::vector<uint32_t>& codepoints);

/**
 * Returns the UTF-8 byte count for selected codepoints.
 */
size_t count_utf8_bytes(const std::vector<uint32_t>& codepoints);

/**
 * Returns the UTF-8 byte count for text filtered according to include_latin.
 */
size_t count_utf8_bytes(std::string_view text, bool include_latin = false);

/**
 * Classifies the script of a single codepoint (e.g. CJK, Arabic, Cyrillic, Greek, Tamil, General).
 */
std::string classify_script(uint32_t cp);

/**
 * Analyzes common usage/script across a set of codepoints.
 * Returns sorted unique script names joined by " / ", or "N/A" if empty.
 */
std::string get_common_usage(const std::vector<uint32_t>& codepoints);

} // namespace glyph_atlas::core
