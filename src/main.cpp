#include "app-window.h"
#include "unicode_core.hpp"

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#endif

#include <format>
#include <iostream>
#include <memory>
#include <string>
#include <string_view>
#include <vector>

using namespace glyph_atlas::core;

namespace {

const std::vector<std::string> kPreviewFonts = {
    "Microsoft YaHei",
    "Segoe UI",
    "SimSun",
    "SimHei",
    "Malgun Gothic",
    "Arial Unicode MS",
    "Arial"
};

void copy_to_clipboard(std::string_view utf8_text) {
#ifdef _WIN32
    if (utf8_text.empty()) {
        return;
    }
    const int wlen = MultiByteToWideChar(CP_UTF8, 0, utf8_text.data(), static_cast<int>(utf8_text.size()), nullptr, 0);
    if (wlen <= 0) {
        return;
    }
    HGLOBAL hMem = GlobalAlloc(GMEM_MOVEABLE, static_cast<size_t>(wlen + 1) * sizeof(wchar_t));
    if (!hMem) {
        return;
    }
    auto* pMem = static_cast<wchar_t*>(GlobalLock(hMem));
    MultiByteToWideChar(CP_UTF8, 0, utf8_text.data(), static_cast<int>(utf8_text.size()), pMem, wlen);
    pMem[wlen] = L'\0';
    GlobalUnlock(hMem);

    if (OpenClipboard(nullptr)) {
        EmptyClipboard();
        SetClipboardData(CF_UNICODETEXT, hMem);
        CloseClipboard();
    } else {
        GlobalFree(hMem);
    }
#endif
}

#ifdef _WIN32
bool apply_native_window_icon() {
    HINSTANCE hInstance = GetModuleHandleW(nullptr);
    HICON hIconBig = static_cast<HICON>(LoadImageW(
        hInstance, MAKEINTRESOURCEW(1), IMAGE_ICON, 32, 32, LR_DEFAULTCOLOR));
    HICON hIconSmall = static_cast<HICON>(LoadImageW(
        hInstance, MAKEINTRESOURCEW(1), IMAGE_ICON, 16, 16, LR_DEFAULTCOLOR));

    if (!hIconBig && !hIconSmall) {
        hIconBig = LoadIconW(hInstance, MAKEINTRESOURCEW(1));
        hIconSmall = hIconBig;
    }

    if (!hIconBig && !hIconSmall) {
        return false;
    }

    struct EnumData {
        HICON big;
        HICON small;
        DWORD current_pid;
        bool found;
    };
    EnumData data{hIconBig, hIconSmall, GetCurrentProcessId(), false};

    EnumWindows([](HWND hwnd, LPARAM lParam) -> BOOL {
        auto* d = reinterpret_cast<EnumData*>(lParam);
        DWORD pid = 0;
        GetWindowThreadProcessId(hwnd, &pid);
        if (pid == d->current_pid) {
            if (d->small) {
                SetClassLongPtrW(hwnd, GCLP_HICONSM, reinterpret_cast<LONG_PTR>(d->small));
                PostMessageW(hwnd, WM_SETICON, ICON_SMALL, reinterpret_cast<LPARAM>(d->small));
            }
            if (d->big) {
                SetClassLongPtrW(hwnd, GCLP_HICON, reinterpret_cast<LONG_PTR>(d->big));
                PostMessageW(hwnd, WM_SETICON, ICON_BIG, reinterpret_cast<LPARAM>(d->big));
            }
            d->found = true;
        }
        return TRUE;
    }, reinterpret_cast<LPARAM>(&data));

    return data.found;
}
#endif

struct AppController {
    std::string input_text;
    FormatOptions options;
    std::vector<uint32_t> current_codepoints;
    size_t font_index = 0;
    int selected_tab = 0;

    void update_other_formats(AppWindow& window) {
        if (selected_tab == 0) {
            // C++ Vector
            if (current_codepoints.empty()) {
                window.set_other_format_empty(true);
                window.set_other_format_output(slint::SharedString(format_cpp_vector(current_codepoints, options.prefix, options.uppercase)));
                window.set_other_format_line2(slint::SharedString(""));
            } else {
                window.set_other_format_empty(false);
                window.set_other_format_output(slint::SharedString(format_cpp_vector(current_codepoints, options.prefix, options.uppercase)));
                std::string comma_hex;
                for (size_t i = 0; i < current_codepoints.size(); ++i) {
                    if (i > 0) comma_hex += ", ";
                    comma_hex += format_hex(current_codepoints[i], options.prefix, options.uppercase);
                }
                window.set_other_format_line2(slint::SharedString(comma_hex));
            }
        } else if (selected_tab == 1) {
            // JSON
            window.set_other_format_empty(current_codepoints.empty());
            window.set_other_format_output(slint::SharedString(format_json(current_codepoints, options.prefix, options.uppercase)));
        } else if (selected_tab == 2) {
            // Space Separated
            window.set_other_format_empty(current_codepoints.empty());
            window.set_other_format_output(slint::SharedString(format_space_separated(current_codepoints, options.prefix, options.uppercase)));
        } else {
            // Unicode Escape
            window.set_other_format_empty(current_codepoints.empty());
            window.set_other_format_output(slint::SharedString(format_unicode_escape(current_codepoints, options.uppercase)));
        }
    }

    void update_all(AppWindow& window) {
        current_codepoints = get_codepoints(input_text, options.include_latin);
        window.set_char_count(static_cast<int>(current_codepoints.size()));

        // Live preview displays extracted glyphs
        std::string preview = encode_utf8(current_codepoints);
        window.set_preview_text(slint::SharedString(preview));

        // C Array
        if (current_codepoints.empty()) {
            window.set_c_array_empty(true);
            window.set_c_array_full(slint::SharedString(format_c_array(current_codepoints, options.prefix, options.uppercase)));
            window.set_c_array_line2(slint::SharedString(""));
        } else {
            window.set_c_array_empty(false);
            window.set_c_array_full(slint::SharedString(format_c_array(current_codepoints, options.prefix, options.uppercase)));
            std::string comma_hex;
            for (size_t i = 0; i < current_codepoints.size(); ++i) {
                if (i > 0) comma_hex += ", ";
                comma_hex += format_hex(current_codepoints[i], options.prefix, options.uppercase);
            }
            window.set_c_array_line2(slint::SharedString(comma_hex));
        }

        // Codepoint Count
        window.set_count_val(static_cast<int>(current_codepoints.size()));
        window.set_count_statement(slint::SharedString(format_count_statement(current_codepoints)));

        // Other Formats
        update_other_formats(window);

        // Quick Info
        window.set_qi_decimal(slint::SharedString(std::to_string(current_codepoints.size())));
        const size_t bytes = count_utf8_bytes(current_codepoints);
        window.set_qi_utf8(slint::SharedString(std::to_string(bytes)));

        if (current_codepoints.empty()) {
            window.set_qi_first(slint::SharedString("—"));
            window.set_qi_last(slint::SharedString("—"));
            window.set_qi_usage(slint::SharedString("N/A"));
        } else {
            window.set_qi_first(slint::SharedString(std::format("U+{:04X}", current_codepoints.front())));
            window.set_qi_last(slint::SharedString(std::format("U+{:04X}", current_codepoints.back())));
            window.set_qi_usage(slint::SharedString(get_common_usage(current_codepoints)));
        }
    }

    std::string get_other_format_for_copy() const {
        if (selected_tab == 0) {
            return format_cpp_vector(current_codepoints, options.prefix, options.uppercase);
        } else if (selected_tab == 1) {
            return format_json(current_codepoints, options.prefix, options.uppercase);
        } else if (selected_tab == 2) {
            return format_space_separated(current_codepoints, options.prefix, options.uppercase);
        } else {
            return format_unicode_escape(current_codepoints, options.uppercase);
        }
    }

    std::string build_copy_all_text() const {
        return std::format(
            "=== C/C++ Array ===\n{}\n\n"
            "=== C++ Vector ===\n{}\n\n"
            "=== JSON ===\n{}\n\n"
            "=== Space Separated ===\n{}\n\n"
            "=== Unicode Escape ===\n{}\n\n"
            "=== Count ===\n{}",
            format_c_array(current_codepoints, options.prefix, options.uppercase),
            format_cpp_vector(current_codepoints, options.prefix, options.uppercase),
            format_json(current_codepoints, options.prefix, options.uppercase),
            format_space_separated(current_codepoints, options.prefix, options.uppercase),
            format_unicode_escape(current_codepoints, options.uppercase),
            format_count_statement(current_codepoints)
        );
    }
};

} // namespace

int main(int argc, char **argv) {
    auto app = AppWindow::create();
    auto controller = std::make_shared<AppController>();

    // Initial state
    controller->options.include_latin = false;
    controller->options.prefix = true;
    controller->options.uppercase = false;
    app->set_current_font(slint::SharedString(kPreviewFonts[0]));
    controller->update_all(*app);

    slint::ComponentWeakHandle<AppWindow> weak_app(app);

    // Callbacks
    app->on_input_changed([weak_app, controller](slint::SharedString text) {
        if (auto locked_app = weak_app.lock()) {
            controller->input_text = text.data();
            controller->update_all(**locked_app);
        }
    });

    app->on_clear_input([weak_app, controller]() {
        if (auto locked_app = weak_app.lock()) {
            controller->input_text.clear();
            controller->update_all(**locked_app);
        }
    });

    app->on_copy_c_array([controller]() {
        copy_to_clipboard(format_c_array(controller->current_codepoints, controller->options.prefix, controller->options.uppercase));
    });

    app->on_copy_count([controller]() {
        copy_to_clipboard(format_count_statement(controller->current_codepoints));
    });

    app->on_copy_other_format([controller]() {
        copy_to_clipboard(controller->get_other_format_for_copy());
    });

    app->on_copy_all([controller]() {
        copy_to_clipboard(controller->build_copy_all_text());
    });

    app->on_change_font([weak_app, controller]() {
        if (auto locked_app = weak_app.lock()) {
            controller->font_index = (controller->font_index + 1) % kPreviewFonts.size();
            (*locked_app)->set_current_font(slint::SharedString(kPreviewFonts[controller->font_index]));
        }
    });

    app->on_tab_changed([weak_app, controller](int tab_idx) {
        if (auto locked_app = weak_app.lock()) {
            controller->selected_tab = tab_idx;
            controller->update_other_formats(**locked_app);
        }
    });

    app->on_setting_changed([weak_app, controller](bool include_latin, bool prefix, bool upper) {
        if (auto locked_app = weak_app.lock()) {
            controller->options.include_latin = include_latin;
            controller->options.prefix = prefix;
            controller->options.uppercase = upper;
            controller->update_all(**locked_app);
        }
    });

    app->on_toggle_theme([]() {
        // Theme property toggled directly inside Slint UI
    });

    app->show();
#ifdef _WIN32
    apply_native_window_icon();
    auto icon_timer = std::make_shared<slint::Timer>();
    icon_timer->start(slint::TimerMode::Repeated, std::chrono::milliseconds(50), [icon_timer]() {
        if (apply_native_window_icon()) {
            icon_timer->stop();
        }
    });
#endif
    app->run();
    return 0;
}
