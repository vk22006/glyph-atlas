#include "unicode_core.hpp"

#include <format>
#include <set>
#include <string>

namespace glyph_atlas::core {

std::vector<uint32_t> decode_utf8(std::string_view text) {
    std::vector<uint32_t> codepoints;
    const size_t len = text.size();
    size_t i = 0;

    while (i < len) {
        const auto b0 = static_cast<unsigned char>(text[i]);
        if (b0 < 0x80) {
            // 1-byte ASCII (0x00 - 0x7F)
            codepoints.push_back(b0);
            i += 1;
        } else if ((b0 & 0xE0) == 0xC0) {
            // 2-byte sequence (0xC2..0xDF)
            if (i + 1 < len) {
                const auto b1 = static_cast<unsigned char>(text[i + 1]);
                if ((b1 & 0xC0) == 0x80 && (b0 >= 0xC2)) { // reject overlong 0xC0, 0xC1
                    uint32_t cp = ((b0 & 0x1F) << 6) | (b1 & 0x3F);
                    codepoints.push_back(cp);
                    i += 2;
                    continue;
                }
            }
            // Invalid byte, advance 1
            i += 1;
        } else if ((b0 & 0xF0) == 0xE0) {
            // 3-byte sequence (0xE0..0xEF)
            if (i + 2 < len) {
                const auto b1 = static_cast<unsigned char>(text[i + 1]);
                const auto b2 = static_cast<unsigned char>(text[i + 2]);
                if ((b1 & 0xC0) == 0x80 && (b2 & 0xC0) == 0x80) {
                    uint32_t cp = ((b0 & 0x0F) << 12) | ((b1 & 0x3F) << 6) | (b2 & 0x3F);
                    // Reject overlong (cp < 0x0800) and UTF-16 surrogates (0xD800..0xDFFF)
                    if (cp >= 0x0800 && (cp < 0xD800 || cp > 0xDFFF)) {
                        codepoints.push_back(cp);
                        i += 3;
                        continue;
                    }
                }
            }
            i += 1;
        } else if ((b0 & 0xF8) == 0xF0) {
            // 4-byte sequence (0xF0..0xF4)
            if (i + 3 < len) {
                const auto b1 = static_cast<unsigned char>(text[i + 1]);
                const auto b2 = static_cast<unsigned char>(text[i + 2]);
                const auto b3 = static_cast<unsigned char>(text[i + 3]);
                if ((b1 & 0xC0) == 0x80 && (b2 & 0xC0) == 0x80 && (b3 & 0xC0) == 0x80) {
                    uint32_t cp = ((b0 & 0x07) << 18) | ((b1 & 0x3F) << 12) | ((b2 & 0x3F) << 6) | (b3 & 0x3F);
                    // Reject overlong (cp < 0x10000) and out-of-range (> 0x10FFFF)
                    if (cp >= 0x10000 && cp <= 0x10FFFF) {
                        codepoints.push_back(cp);
                        i += 4;
                        continue;
                    }
                }
            }
            i += 1;
        } else {
            // Invalid byte
            i += 1;
        }
    }
    return codepoints;
}

std::string encode_utf8(uint32_t cp) {
    std::string out;
    if (cp <= 0x7F) {
        out.push_back(static_cast<char>(cp));
    } else if (cp <= 0x7FF) {
        out.push_back(static_cast<char>(0xC0 | ((cp >> 6) & 0x1F)));
        out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
    } else if (cp <= 0xFFFF) {
        out.push_back(static_cast<char>(0xE0 | ((cp >> 12) & 0x0F)));
        out.push_back(static_cast<char>(0x80 | ((cp >> 6) & 0x3F)));
        out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
    } else if (cp <= 0x10FFFF) {
        out.push_back(static_cast<char>(0xF0 | ((cp >> 18) & 0x07)));
        out.push_back(static_cast<char>(0x80 | ((cp >> 12) & 0x3F)));
        out.push_back(static_cast<char>(0x80 | ((cp >> 6) & 0x3F)));
        out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
    }
    return out;
}

std::string encode_utf8(const std::vector<uint32_t>& codepoints) {
    std::string out;
    for (uint32_t cp : codepoints) {
        out += encode_utf8(cp);
    }
    return out;
}

bool is_non_latin(uint32_t cp) noexcept {
    // Basic Latin / ASCII (0x00 to 0x7F) are Latin
    return cp > 0x7F;
}

bool is_whitespace(uint32_t cp) noexcept {
    return (cp == ' ' || cp == '\t' || cp == '\n' || cp == '\r' || cp == '\v' || cp == '\f');
}

size_t utf8_byte_length(uint32_t cp) noexcept {
    if (cp <= 0x7F) return 1;
    if (cp <= 0x7FF) return 2;
    if (cp <= 0xFFFF) return 3;
    if (cp <= 0x10FFFF) return 4;
    return 0;
}

std::vector<uint32_t> get_codepoints(std::string_view text, bool include_latin) {
    const std::vector<uint32_t> all = decode_utf8(text);
    std::vector<uint32_t> result;
    result.reserve(all.size());

    for (uint32_t cp : all) {
        if (include_latin) {
            // Include non-whitespace characters
            if (!is_whitespace(cp) && (cp >= 0x21 || cp > 0x7F)) {
                result.push_back(cp);
            }
        } else {
            if (is_non_latin(cp)) {
                result.push_back(cp);
            }
        }
    }
    return result;
}

std::string format_hex(uint32_t cp, bool prefix, bool uppercase) {
    std::string digits = uppercase ? std::format("{:04X}", cp) : std::format("{:04x}", cp);
    return prefix ? ("0x" + digits) : digits;
}

std::string format_c_array(const std::vector<uint32_t>& codepoints, bool prefix, bool uppercase) {
    if (codepoints.empty()) {
        return "int codepoints[] = {};";
    }
    std::string hex_vals;
    for (size_t i = 0; i < codepoints.size(); ++i) {
        if (i > 0) {
            hex_vals += ", ";
        }
        hex_vals += format_hex(codepoints[i], prefix, uppercase);
    }
    return "int codepoints[] = {\n    " + hex_vals + "\n};";
}

std::string format_cpp_vector(const std::vector<uint32_t>& codepoints, bool prefix, bool uppercase) {
    if (codepoints.empty()) {
        return "std::vector<int> codepoints = {};";
    }
    std::string hex_vals;
    for (size_t i = 0; i < codepoints.size(); ++i) {
        if (i > 0) {
            hex_vals += ", ";
        }
        hex_vals += format_hex(codepoints[i], prefix, uppercase);
    }
    return "std::vector<int> codepoints = {\n    " + hex_vals + "\n};";
}

std::string format_json(const std::vector<uint32_t>& codepoints, bool prefix, bool uppercase) {
    if (codepoints.empty()) {
        return "[]";
    }
    std::string items;
    for (size_t i = 0; i < codepoints.size(); ++i) {
        if (i > 0) {
            items += ", ";
        }
        items += "\"" + format_hex(codepoints[i], prefix, uppercase) + "\"";
    }
    return "[\n    " + items + "\n]";
}

std::string format_space_separated(const std::vector<uint32_t>& codepoints, bool prefix, bool uppercase) {
    if (codepoints.empty()) {
        return "";
    }
    std::string res;
    for (size_t i = 0; i < codepoints.size(); ++i) {
        if (i > 0) {
            res += " ";
        }
        res += format_hex(codepoints[i], prefix, uppercase);
    }
    return res;
}

std::string format_unicode_escape(const std::vector<uint32_t>& codepoints, bool uppercase) {
    if (codepoints.empty()) {
        return "";
    }
    std::string res;
    for (size_t i = 0; i < codepoints.size(); ++i) {
        if (i > 0) {
            res += " ";
        }
        std::string hex_part = uppercase ? std::format("{:04X}", codepoints[i]) : std::format("{:04x}", codepoints[i]);
        res += "U+" + hex_part;
    }
    return res;
}

std::string format_count_statement(const std::vector<uint32_t>& codepoints) {
    return std::format("int count = {};", codepoints.size());
}

size_t count_utf8_bytes(const std::vector<uint32_t>& codepoints) {
    size_t total = 0;
    for (uint32_t cp : codepoints) {
        total += utf8_byte_length(cp);
    }
    return total;
}

size_t count_utf8_bytes(std::string_view text, bool include_latin) {
    const auto cps = get_codepoints(text, include_latin);
    return count_utf8_bytes(cps);
}

std::string classify_script(uint32_t cp) {
    // Arabic
    if ((cp >= 0x0600 && cp <= 0x06FF) ||
        (cp >= 0x0750 && cp <= 0x077F) ||
        (cp >= 0x0870 && cp <= 0x08FF) ||
        (cp >= 0xFB50 && cp <= 0xFDFF) ||
        (cp >= 0xFE70 && cp <= 0xFEFF) ||
        (cp >= 0x10EC0 && cp <= 0x10EFF)) {
        return "Arabic";
    }

    // Tamil
    if ((cp >= 0x0B80 && cp <= 0x0BFF) ||
        (cp >= 0x11FC0 && cp <= 0x11FFF)) {
        return "Tamil";
    }

    // Greek
    if ((cp >= 0x0370 && cp <= 0x03FF) ||
        (cp >= 0x1F00 && cp <= 0x1FFF)) {
        return "Greek";
    }

    // Cyrillic
    if ((cp >= 0x0400 && cp <= 0x052F) ||
        (cp >= 0x2DE0 && cp <= 0x2DFF) ||
        (cp >= 0xA640 && cp <= 0xA69F) ||
        (cp >= 0x1C80 && cp <= 0x1C8F) ||
        (cp >= 0x1E030 && cp <= 0x1E08F)) {
        return "Cyrillic";
    }

    // CJK (Ideographs, Japanese Kana, Korean Hangul, Bopomofo, CJK Radicals, CJK Punctuation)
    if ((cp >= 0x4E00 && cp <= 0x9FFF) ||
        (cp >= 0x3400 && cp <= 0x4DBF) ||
        (cp >= 0x20000 && cp <= 0x2EBEF) ||
        (cp >= 0x30000 && cp <= 0x323AF) ||
        (cp >= 0x2E80 && cp <= 0x2FD5) ||
        (cp >= 0x3000 && cp <= 0x303F) ||
        (cp >= 0xF900 && cp <= 0xFAFF) ||
        (cp >= 0x2F800 && cp <= 0x2FA1F) ||
        (cp >= 0x3040 && cp <= 0x30FF) ||
        (cp >= 0x3100 && cp <= 0x312F) ||
        (cp >= 0x31A0 && cp <= 0x31BF) ||
        (cp >= 0x31F0 && cp <= 0x31FF) ||
        (cp >= 0xAC00 && cp <= 0xD7AF) ||
        (cp >= 0x1100 && cp <= 0x11FF) ||
        (cp >= 0x3130 && cp <= 0x318F)) {
        return "CJK";
    }

    return "General";
}

std::string get_common_usage(const std::vector<uint32_t>& codepoints) {
    if (codepoints.empty()) {
        return "N/A";
    }
    std::set<std::string> cats;
    for (uint32_t cp : codepoints) {
        cats.insert(classify_script(cp));
    }
    if (cats.empty()) {
        return "General";
    }
    std::string result;
    for (const auto& cat : cats) {
        if (!result.empty()) {
            result += " / ";
        }
        result += cat;
    }
    return result;
}

} // namespace glyph_atlas::core
