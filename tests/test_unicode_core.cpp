#include "unicode_core.hpp"

#include <iostream>
#include <string>
#include <vector>
#include <cstdlib>

using namespace glyph_atlas::core;

static int g_failed = 0;
static int g_passed = 0;

#define TEST_ASSERT(cond, msg) \
    do { \
        if (!(cond)) { \
            std::cerr << "FAIL: " << msg << " (" << __FILE__ << ":" << __LINE__ << ")\n"; \
            g_failed++; \
        } else { \
            g_passed++; \
        } \
    } while (0)

#define TEST_ASSERT_EQ(actual, expected, msg) \
    do { \
        if ((actual) != (expected)) { \
            std::cerr << "FAIL: " << msg << "\n  Actual:   \"" << (actual) << "\"\n  Expected: \"" << (expected) << "\" (" << __FILE__ << ":" << __LINE__ << ")\n"; \
            g_failed++; \
        } else { \
            g_passed++; \
        } \
    } while (0)

void test_empty_input() {
    auto cps = get_codepoints("", false);
    TEST_ASSERT(cps.empty(), "Empty input non-latin");

    auto cps_latin = get_codepoints("", true);
    TEST_ASSERT(cps_latin.empty(), "Empty input latin");

    TEST_ASSERT_EQ(format_c_array(cps), "int codepoints[] = {};", "Empty C array");
    TEST_ASSERT_EQ(format_cpp_vector(cps), "std::vector<int> codepoints = {};", "Empty C++ vector");
    TEST_ASSERT_EQ(format_json(cps), "[]", "Empty JSON");
    TEST_ASSERT_EQ(format_space_separated(cps), "", "Empty space separated");
    TEST_ASSERT_EQ(format_unicode_escape(cps), "", "Empty Unicode escape");
    TEST_ASSERT_EQ(format_count_statement(cps), "int count = 0;", "Empty count statement");
    TEST_ASSERT_EQ(count_utf8_bytes("", false), 0ULL, "Empty UTF-8 bytes");
    TEST_ASSERT_EQ(get_common_usage(cps), "N/A", "Empty usage");
}

void test_ascii() {
    // Non-latin filter should exclude all pure ASCII
    auto cps = get_codepoints("Hello World!", false);
    TEST_ASSERT(cps.empty(), "Pure ASCII should produce empty non-latin codepoints");
    TEST_ASSERT_EQ(count_utf8_bytes("Hello World!", false), 0ULL, "Pure ASCII 0 non-latin bytes");

    // With include_latin = true, non-whitespace ASCII characters should be included
    auto cps_latin = get_codepoints("Hello", true);
    std::vector<uint32_t> expected = {'H', 'e', 'l', 'l', 'o'};
    TEST_ASSERT(cps_latin == expected, "ASCII Hello with include_latin");
    TEST_ASSERT_EQ(get_common_usage(cps_latin), "General", "ASCII usage is General");
    TEST_ASSERT_EQ(count_utf8_bytes("Hello", true), 5ULL, "ASCII byte count 5");
}

void test_chinese() {
    // Chinese characters: 你好，世界 (U+4F60, U+597D, U+FF0C, U+4E16, U+754C)
    const std::string text = "你好，世界";
    auto cps = get_codepoints(text, false);
    std::vector<uint32_t> expected = {0x4F60, 0x597D, 0xFF0C, 0x4E16, 0x754C};
    TEST_ASSERT(cps == expected, "Chinese codepoints match");

    TEST_ASSERT_EQ(count_utf8_bytes(text, false), 15ULL, "Chinese 5 chars * 3 bytes = 15");
    TEST_ASSERT_EQ(get_common_usage(cps), "CJK / General", "Chinese with fullwidth comma usage is CJK / General");

    // Pure Chinese without punctuation
    auto cps_pure = get_codepoints("你好世界", false);
    TEST_ASSERT_EQ(get_common_usage(cps_pure), "CJK", "Pure Chinese usage is CJK");

    TEST_ASSERT_EQ(format_c_array(cps),
                   "int codepoints[] = {\n    0x4f60, 0x597d, 0xff0c, 0x4e16, 0x754c\n};",
                   "Chinese C array");

    TEST_ASSERT_EQ(format_cpp_vector(cps),
                   "std::vector<int> codepoints = {\n    0x4f60, 0x597d, 0xff0c, 0x4e16, 0x754c\n};",
                   "Chinese C++ vector");

    TEST_ASSERT_EQ(format_json(cps),
                   "[\n    \"0x4f60\", \"0x597d\", \"0xff0c\", \"0x4e16\", \"0x754c\"\n]",
                   "Chinese JSON");

    TEST_ASSERT_EQ(format_space_separated(cps),
                   "0x4f60 0x597d 0xff0c 0x4e16 0x754c",
                   "Chinese space separated");

    TEST_ASSERT_EQ(format_unicode_escape(cps),
                   "U+4f60 U+597d U+ff0c U+4e16 U+754c",
                   "Chinese unicode escape");

    TEST_ASSERT_EQ(format_count_statement(cps), "int count = 5;", "Chinese count");
}

void test_tamil() {
    // Tamil: தமிழ் (U+0BA4, U+0BAE, U+0BBF, U+0BB4, U+0BCD)
    const std::string text = "தமிழ்";
    auto cps = get_codepoints(text, false);
    std::vector<uint32_t> expected = {0x0BA4, 0x0BAE, 0x0BBF, 0x0BB4, 0x0BCD};
    TEST_ASSERT(cps == expected, "Tamil codepoints");
    TEST_ASSERT_EQ(get_common_usage(cps), "Tamil", "Tamil usage is Tamil");
    TEST_ASSERT_EQ(count_utf8_bytes(text, false), 15ULL, "Tamil 5 chars * 3 bytes = 15");
}

void test_arabic() {
    // Arabic: مرحبا (U+0645, U+0631, U+062D, U+0628, U+0627)
    const std::string text = "مرحبا";
    auto cps = get_codepoints(text, false);
    std::vector<uint32_t> expected = {0x0645, 0x0631, 0x062D, 0x0628, 0x0627};
    TEST_ASSERT(cps == expected, "Arabic codepoints");
    TEST_ASSERT_EQ(get_common_usage(cps), "Arabic", "Arabic usage is Arabic");
    TEST_ASSERT_EQ(count_utf8_bytes(text, false), 10ULL, "Arabic 5 chars * 2 bytes = 10");
}

void test_mixed_text() {
    // English + Chinese + Arabic: "Hello 世界 مرحبا"
    const std::string text = "Hello 世界 مرحبا";

    // Non-latin filter: drops English and spaces, keeps Chinese and Arabic
    auto cps = get_codepoints(text, false);
    std::vector<uint32_t> expected = {0x4E16, 0x754C, 0x0645, 0x0631, 0x062D, 0x0628, 0x0627};
    TEST_ASSERT(cps == expected, "Mixed text non-latin extraction");
    TEST_ASSERT_EQ(get_common_usage(cps), "Arabic / CJK", "Mixed script sorting alphabetical");

    // Include latin: includes English letters too, skips spaces
    auto cps_all = get_codepoints(text, true);
    TEST_ASSERT_EQ(cps_all.size(), 12ULL, "Mixed text total non-space codepoints");
    TEST_ASSERT_EQ(get_common_usage(cps_all), "Arabic / CJK / General", "Mixed with Latin usage");
}

void test_whitespace() {
    // Various forms of whitespace: spaces, tabs, newlines, carriage returns
    const std::string ws_only = "   \t\t\n\r\n   ";
    auto cps1 = get_codepoints(ws_only, false);
    TEST_ASSERT(cps1.empty(), "Whitespace only non-latin empty");
    auto cps2 = get_codepoints(ws_only, true);
    TEST_ASSERT(cps2.empty(), "Whitespace only latin empty");

    // Whitespace surrounding Chinese characters
    const std::string surrounded = " \n 你 \t 好 \r ";
    auto cps3 = get_codepoints(surrounded, false);
    std::vector<uint32_t> exp3 = {0x4F60, 0x597D};
    TEST_ASSERT(cps3 == exp3, "Surrounding whitespace stripped properly");
}

void test_emoji_and_supplementary() {
    // Supplementary-plane characters (Plane 1): Party Popper (U+1F389) and Rocket (U+1F680)
    // UTF-8: 4 bytes each
    const std::string text = "🎉🚀";
    auto cps = get_codepoints(text, false);
    std::vector<uint32_t> expected = {0x1F389, 0x1F680};
    TEST_ASSERT(cps == expected, "Emoji Plane 1 codepoints decoded correctly");

    // Check that we didn't confuse with UTF-16 surrogate pairs
    TEST_ASSERT_EQ(cps.size(), 2ULL, "Exactly 2 codepoints, not surrogates");
    TEST_ASSERT_EQ(count_utf8_bytes(text, false), 8ULL, "2 emoji * 4 bytes = 8");
    TEST_ASSERT_EQ(get_common_usage(cps), "General", "Emoji classified as General");

    // Formatting 5-digit hex codepoints
    TEST_ASSERT_EQ(format_hex(0x1F389, true, false), "0x1f389", "Emoji lowercase hex prefix");
    TEST_ASSERT_EQ(format_hex(0x1F389, true, true), "0x1F389", "Emoji uppercase hex prefix");
    TEST_ASSERT_EQ(format_hex(0x1F389, false, true), "1F389", "Emoji uppercase hex no prefix");
    TEST_ASSERT_EQ(format_unicode_escape(cps, true), "U+1F389 U+1F680", "Emoji Unicode escape uppercase");
}

void test_hex_options() {
    std::vector<uint32_t> cps = {0x4F60, 0x00A9};

    // Prefix + Lowercase (default)
    TEST_ASSERT_EQ(format_space_separated(cps, true, false), "0x4f60 0x00a9", "Space sep prefix lower");
    TEST_ASSERT_EQ(format_c_array(cps, true, false),
                   "int codepoints[] = {\n    0x4f60, 0x00a9\n};", "C array prefix lower");

    // Prefix + Uppercase
    TEST_ASSERT_EQ(format_space_separated(cps, true, true), "0x4F60 0x00A9", "Space sep prefix upper");
    TEST_ASSERT_EQ(format_c_array(cps, true, true),
                   "int codepoints[] = {\n    0x4F60, 0x00A9\n};", "C array prefix upper");

    // No Prefix + Lowercase
    TEST_ASSERT_EQ(format_space_separated(cps, false, false), "4f60 00a9", "Space sep no prefix lower");

    // No Prefix + Uppercase
    TEST_ASSERT_EQ(format_space_separated(cps, false, true), "4F60 00A9", "Space sep no prefix upper");

    // Unicode escape case
    TEST_ASSERT_EQ(format_unicode_escape(cps, false), "U+4f60 U+00a9", "Escape lower");
    TEST_ASSERT_EQ(format_unicode_escape(cps, true), "U+4F60 U+00A9", "Escape upper");
}

void test_combining_characters() {
    // Combining Acute Accent: 'e' (U+0065) + combining acute accent (U+0301) -> é
    const std::string text = "e\xCC\x81"; // UTF-8: 0x65, 0xCC 0x81
    auto cps_nonlatin = get_codepoints(text, false);
    std::vector<uint32_t> exp_nonlatin = {0x0301};
    TEST_ASSERT(cps_nonlatin == exp_nonlatin, "Combining mark extracted when Latin is excluded");
    TEST_ASSERT_EQ(format_unicode_escape(cps_nonlatin, true), "U+0301", "Combining mark escape");

    auto cps_latin = get_codepoints(text, true);
    std::vector<uint32_t> exp_latin = {0x0065, 0x0301};
    TEST_ASSERT(cps_latin == exp_latin, "Base letter and combining mark both extracted with Latin included");
    TEST_ASSERT_EQ(format_unicode_escape(cps_latin, true), "U+0065 U+0301", "Combining character escape with Latin");

    // Devanagari combined: क (U+0915) + ि (U+093F combining vowel sign i) = कि
    const std::string devanagari = "\xE0\xA4\x95\xE0\xA4\xBF";
    auto cps_deva = get_codepoints(devanagari, false);
    std::vector<uint32_t> exp_deva = {0x0915, 0x093F};
    TEST_ASSERT(cps_deva == exp_deva, "Devanagari base and combining vowel mark extracted");
    TEST_ASSERT_EQ(count_utf8_bytes(devanagari, false), 6ULL, "Devanagari 2 codepoints * 3 bytes = 6");
}

int main() {
    std::cout << "Running GlyphAtlas Unicode Core Unit Tests...\n";

    test_empty_input();
    test_ascii();
    test_chinese();
    test_tamil();
    test_arabic();
    test_mixed_text();
    test_whitespace();
    test_emoji_and_supplementary();
    test_hex_options();
    test_combining_characters();

    std::cout << "\nResults: " << g_passed << " passed, " << g_failed << " failed.\n";

    return (g_failed == 0) ? 0 : 1;
}
