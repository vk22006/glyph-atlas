"""
GlyphAtlas — Main Application Window
"""

import tkinter as tk
from tkinter import font as tkfont
import customtkinter as ctk
from PIL import Image
import os
import sys

import theme as T
from utils import (
    get_codepoints, format_c_array, format_cpp_vector, format_json,
    format_space_separated, format_unicode_escape, format_count_statement,
    count_utf8_bytes, get_common_usage, is_non_latin
)

# ── CustomTkinter global setup ────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

ASSET_DIR = os.path.join(os.path.dirname(__file__), "assets")


def asset(name: str) -> str:
    return os.path.join(ASSET_DIR, name)


# ── Reusable card frame ───────────────────────────────────────────────────────
class CardFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", T.BG_CARD)
        kwargs.setdefault("corner_radius", T.RADIUS)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", T.BORDER_DEFAULT)
        super().__init__(master, **kwargs)


# ── Syntax-highlighted code widget (using tk.Text) ────────────────────────────
class CodeText(tk.Text):
    """A read-only Text widget with dark code styling and syntax highlighting."""

    TAG_TYPE = "type"
    TAG_HEX  = "hex"
    TAG_PUNC = "punc"
    TAG_KW   = "kw"

    def __init__(self, master, height=5, **kwargs):
        super().__init__(
            master,
            height=height,
            bg=T.BG_CODE,
            fg=T.TEXT_CODE_BASE,
            insertbackground=T.TEXT_PRIMARY,
            selectbackground=T.ACCENT_PURPLE,
            selectforeground=T.TEXT_PRIMARY,
            font=(T.FONT_FAMILY_CODE, T.FONT_BASE),
            relief="flat",
            bd=0,
            padx=14,
            pady=10,
            wrap="word",
            state="disabled",
            **kwargs,
        )
        self.tag_configure(self.TAG_TYPE, foreground=T.TEXT_CODE_TYPE)
        self.tag_configure(self.TAG_HEX,  foreground=T.TEXT_CODE_HEX)
        self.tag_configure(self.TAG_PUNC, foreground=T.TEXT_CODE_PUNC)
        self.tag_configure(self.TAG_KW,   foreground=T.ACCENT_PURPLE_L)

    def set_code(self, text: str):
        """Replace content and apply syntax highlighting."""
        self.configure(state="normal")
        self.delete("1.0", "end")
        self._insert_highlighted(text)
        self.configure(state="disabled")

    def _insert_highlighted(self, code: str):
        import re
        # Tokenise: keywords/types, hex values, rest
        tokens = re.split(r"(0x[0-9a-fA-F]+|int|std::vector<int>|std::vector)", code)
        for tok in tokens:
            if re.fullmatch(r"0x[0-9a-fA-F]+", tok):
                self.insert("end", tok, self.TAG_HEX)
            elif tok in ("int", "std::vector<int>", "std::vector"):
                self.insert("end", tok, self.TAG_TYPE)
            else:
                self.insert("end", tok)

    def get_content(self) -> str:
        return self.get("1.0", "end-1c")


# ── Sidebar navigation item ───────────────────────────────────────────────────
class NavItem(ctk.CTkFrame):
    def __init__(self, master, icon: str, label: str, selected=False, command=None, **kwargs):
        super().__init__(master, fg_color="transparent", corner_radius=8, **kwargs)
        self._selected = selected
        self._command  = command
        self._icon_chr = icon
        self._label_str = label

        self._bg_frame = ctk.CTkFrame(self, fg_color=T.BG_SELECTED if selected else "transparent",
                                      corner_radius=8)
        self._bg_frame.pack(fill="x", padx=6, pady=2)

        inner = ctk.CTkFrame(self._bg_frame, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=8)

        self._icon_lbl = ctk.CTkLabel(inner, text=icon, font=(T.FONT_FAMILY_UI, 15),
                                      text_color=T.ACCENT_PURPLE_L if selected else T.TEXT_SECONDARY,
                                      width=24)
        self._icon_lbl.pack(side="left")

        self._text_lbl = ctk.CTkLabel(inner, text=label, font=(T.FONT_FAMILY_UI, T.FONT_BASE, "bold" if selected else "normal"),
                                      text_color=T.TEXT_PRIMARY if selected else T.TEXT_SECONDARY)
        self._text_lbl.pack(side="left", padx=(8, 0))

        # Bind clicks
        for w in (self._bg_frame, inner, self._icon_lbl, self._text_lbl):
            w.bind("<Button-1>", self._on_click)
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

    def set_selected(self, val: bool):
        self._selected = val
        self._bg_frame.configure(fg_color=T.BG_SELECTED if val else "transparent")
        self._icon_lbl.configure(text_color=T.ACCENT_PURPLE_L if val else T.TEXT_SECONDARY)
        self._text_lbl.configure(text_color=T.TEXT_PRIMARY if val else T.TEXT_SECONDARY,
                                 font=(T.FONT_FAMILY_UI, T.FONT_BASE, "bold" if val else "normal"))

    def _on_click(self, _):
        if self._command:
            self._command()

    def _on_enter(self, _):
        if not self._selected:
            self._bg_frame.configure(fg_color=T.BG_HOVER)

    def _on_leave(self, _):
        if not self._selected:
            self._bg_frame.configure(fg_color="transparent")


# ── Converter page ────────────────────────────────────────────────────────────
class ConverterPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._current_tab = "C++ Vector"
        self._font_index  = 0
        self._preview_fonts = self._load_preview_fonts()
        self._build_ui()

    # ── Font helpers ──────────────────────────────────────────────────────────
    def _load_preview_fonts(self) -> list[str]:
        """Return a list of fonts suitable for CJK/Unicode preview."""
        candidates = [
            "Noto Sans CJK SC", "Noto Sans CJK", "Microsoft YaHei",
            "SimHei", "SimSun", "Malgun Gothic", "Arial Unicode MS",
            "Segoe UI", "Arial"
        ]
        available = set(tkfont.families())
        found = [f for f in candidates if f in available]
        return found if found else ["Arial"]

    # ── UI construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        # Top header row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 0))

        ctk.CTkLabel(header, text="Text to Codepoint Converter",
                     font=(T.FONT_FAMILY_UI, T.FONT_XL, "bold"),
                     text_color=T.TEXT_PRIMARY).pack(side="left")

        btn_row = ctk.CTkFrame(header, fg_color="transparent")
        btn_row.pack(side="right")

        self._theme_btn = ctk.CTkButton(
            btn_row, text="🌙  Dark", width=100, height=34,
            font=(T.FONT_FAMILY_UI, T.FONT_SM),
            fg_color=T.BTN_SECONDARY_BG, hover_color=T.BTN_SECONDARY_HOVER,
            text_color=T.TEXT_SECONDARY, corner_radius=8,
            command=self._toggle_theme
        )
        self._theme_btn.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="⧉  Copy All", width=110, height=34,
            font=(T.FONT_FAMILY_UI, T.FONT_SM),
            fg_color=T.BTN_PRIMARY_BG, hover_color=T.BTN_PRIMARY_HOVER,
            text_color=T.TEXT_PRIMARY, corner_radius=8,
            command=self._copy_all
        ).pack(side="left")

        ctk.CTkLabel(header.master, text="Enter any text and convert it to Unicode codepoints for your C/C++ projects.",
                     font=(T.FONT_FAMILY_UI, T.FONT_SM),
                     text_color=T.TEXT_SECONDARY).pack(anchor="w", padx=24, pady=(2, 14))

        # ── Two-column content area ───────────────────────────────────────────
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24)
        content.columnconfigure(0, weight=5, minsize=340)
        content.columnconfigure(1, weight=4, minsize=280)

        # Left column
        left = ctk.CTkFrame(content, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Right column
        right = ctk.CTkFrame(content, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew")

        self._build_left(left)
        self._build_right(right)

    # ── Left column ───────────────────────────────────────────────────────────
    def _build_left(self, parent):
        # 1. Input card
        inp_card = CardFrame(parent)
        inp_card.pack(fill="x", pady=(0, 10))

        inp_header = ctk.CTkFrame(inp_card, fg_color="transparent")
        inp_header.pack(fill="x", padx=14, pady=(12, 0))
        ctk.CTkLabel(inp_header, text="⇄  1. Input Text",
                     font=(T.FONT_FAMILY_UI, T.FONT_BASE, "bold"),
                     text_color=T.TEXT_SECONDARY).pack(side="left")

        # Input text box
        input_wrap = ctk.CTkFrame(inp_card, fg_color=T.BG_INPUT,
                                   corner_radius=8, border_width=1,
                                   border_color=T.BORDER_INPUT)
        input_wrap.pack(fill="x", padx=14, pady=(8, 4))

        self._input_text = tk.Text(
            input_wrap,
            height=5,
            bg=T.BG_INPUT,
            fg=T.TEXT_PRIMARY,
            insertbackground=T.TEXT_PRIMARY,
            selectbackground=T.ACCENT_PURPLE,
            font=(T.FONT_FAMILY_UI, T.FONT_MD),
            relief="flat", bd=0, padx=12, pady=10,
            wrap="word",
        )
        self._input_text.pack(fill="x")
        self._input_text.bind("<KeyRelease>", self._on_input_change)
        self._input_text.bind("<<Paste>>", lambda e: self.after(10, self._on_input_change))

        # Footer: char count + clear
        inp_foot = ctk.CTkFrame(inp_card, fg_color="transparent")
        inp_foot.pack(fill="x", padx=14, pady=(2, 10))
        self._char_count_lbl = ctk.CTkLabel(
            inp_foot, text="Characters: 0",
            font=(T.FONT_FAMILY_UI, T.FONT_SM), text_color=T.TEXT_MUTED
        )
        self._char_count_lbl.pack(side="left")

        ctk.CTkButton(inp_foot, text="🗑  Clear", width=80, height=26,
                      font=(T.FONT_FAMILY_UI, T.FONT_SM),
                      fg_color=T.BTN_SECONDARY_BG, hover_color=T.BTN_SECONDARY_HOVER,
                      text_color=T.TEXT_SECONDARY, corner_radius=6,
                      command=self._clear_input).pack(side="right")

        # 2. Codepoint Array card
        arr_card = CardFrame(parent)
        arr_card.pack(fill="x", pady=(0, 10))

        arr_header = ctk.CTkFrame(arr_card, fg_color="transparent")
        arr_header.pack(fill="x", padx=14, pady=(12, 0))
        ctk.CTkLabel(arr_header, text="▦  2. Codepoint Array (C/C++)",
                     font=(T.FONT_FAMILY_UI, T.FONT_BASE, "bold"),
                     text_color=T.TEXT_SECONDARY).pack(side="left")
        ctk.CTkButton(arr_header, text="⧉  Copy", width=72, height=26,
                      font=(T.FONT_FAMILY_UI, T.FONT_SM),
                      fg_color=T.BTN_SECONDARY_BG, hover_color=T.BTN_SECONDARY_HOVER,
                      text_color=T.TEXT_SECONDARY, corner_radius=6,
                      command=lambda: self._copy_widget(self._array_code)
                      ).pack(side="right")

        arr_wrap = ctk.CTkFrame(arr_card, fg_color=T.BG_CODE, corner_radius=8)
        arr_wrap.pack(fill="x", padx=14, pady=(6, 14))
        self._array_code = CodeText(arr_wrap, height=4)
        self._array_code.pack(fill="x")

        # 3. Codepoint Count card
        cnt_card = CardFrame(parent)
        cnt_card.pack(fill="x", pady=(0, 10))

        cnt_header = ctk.CTkFrame(cnt_card, fg_color="transparent")
        cnt_header.pack(fill="x", padx=14, pady=(12, 0))
        ctk.CTkLabel(cnt_header, text="#  Codepoint Count",
                     font=(T.FONT_FAMILY_UI, T.FONT_BASE, "bold"),
                     text_color=T.TEXT_SECONDARY).pack(side="left")
        ctk.CTkButton(cnt_header, text="⧉  Copy", width=72, height=26,
                      font=(T.FONT_FAMILY_UI, T.FONT_SM),
                      fg_color=T.BTN_SECONDARY_BG, hover_color=T.BTN_SECONDARY_HOVER,
                      text_color=T.TEXT_SECONDARY, corner_radius=6,
                      command=lambda: self._copy_widget(self._count_code)
                      ).pack(side="right")

        cnt_wrap = ctk.CTkFrame(cnt_card, fg_color=T.BG_CODE, corner_radius=8)
        cnt_wrap.pack(fill="x", padx=14, pady=(6, 14))
        self._count_code = CodeText(cnt_wrap, height=2)
        self._count_code.pack(fill="x")

        # 4. Quick Info card
        qi_card = CardFrame(parent)
        qi_card.pack(fill="x", pady=(0, 10))

        qi_header = ctk.CTkFrame(qi_card, fg_color="transparent")
        qi_header.pack(fill="x", padx=14, pady=(12, 6))
        ctk.CTkLabel(qi_header, text="ⓘ  Quick Info",
                     font=(T.FONT_FAMILY_UI, T.FONT_BASE, "bold"),
                     text_color=T.TEXT_SECONDARY).pack(side="left")

        qi_grid = ctk.CTkFrame(qi_card, fg_color="transparent")
        qi_grid.pack(fill="x", padx=14, pady=(0, 12))
        for i in range(5):
            qi_grid.columnconfigure(i, weight=1)

        def make_info_cell(parent, icon, icon_color, label, value_text, col):
            cell = ctk.CTkFrame(parent, fg_color=T.BG_INPUT, corner_radius=8)
            cell.grid(row=0, column=col, padx=3, sticky="ew")
            top = ctk.CTkFrame(cell, fg_color="transparent")
            top.pack(padx=10, pady=(8, 2), anchor="w")
            ctk.CTkLabel(top, text=icon, font=(T.FONT_FAMILY_UI, 12),
                         text_color=icon_color).pack(side="left")
            ctk.CTkLabel(top, text=label, font=(T.FONT_FAMILY_UI, 10),
                         text_color=T.TEXT_MUTED).pack(side="left", padx=(4, 0))
            var = ctk.StringVar(value=value_text)
            lbl = ctk.CTkLabel(cell, textvariable=var,
                               font=(T.FONT_FAMILY_UI, T.FONT_BASE, "bold"),
                               text_color=T.TEXT_PRIMARY)
            lbl.pack(padx=10, pady=(0, 8), anchor="w")
            return var

        self._qi_decimal   = make_info_cell(qi_grid, "#", T.ACCENT_PURPLE_L, "Decimal Count", "0",          0)
        self._qi_utf8      = make_info_cell(qi_grid, "A", T.ACCENT_BLUE,     "UTF-8 Bytes",   "0",          1)
        self._qi_first     = make_info_cell(qi_grid, "</>", T.TEXT_GREEN,    "First Codepoint","—",         2)
        self._qi_last      = make_info_cell(qi_grid, "</>", T.TEXT_GREEN,    "Last Codepoint", "—",         3)
        self._qi_usage     = make_info_cell(qi_grid, "★", T.TEXT_YELLOW,     "Common Usage",  "N/A",        4)

    # ── Right column ──────────────────────────────────────────────────────────
    def _build_right(self, parent):
        # Live Preview card
        prev_card = CardFrame(parent)
        prev_card.pack(fill="x", pady=(0, 10))

        prev_header = ctk.CTkFrame(prev_card, fg_color="transparent")
        prev_header.pack(fill="x", padx=14, pady=(12, 0))
        ctk.CTkLabel(prev_header, text="👁  Live Preview",
                     font=(T.FONT_FAMILY_UI, T.FONT_BASE, "bold"),
                     text_color=T.TEXT_SECONDARY).pack(side="left")

        # Big preview label
        prev_content = ctk.CTkFrame(prev_card, fg_color=T.BG_INPUT, corner_radius=8)
        prev_content.pack(fill="x", padx=14, pady=(8, 4))
        self._preview_lbl = ctk.CTkLabel(
            prev_content, text="",
            font=(self._preview_fonts[0], T.FONT_2XL),
            text_color=T.TEXT_PRIMARY,
            wraplength=340
        )
        self._preview_lbl.pack(padx=16, pady=16, anchor="w")

        prev_foot = ctk.CTkFrame(prev_card, fg_color="transparent")
        prev_foot.pack(fill="x", padx=14, pady=(4, 12))
        self._font_lbl = ctk.CTkLabel(
            prev_foot,
            text=f"Font: {self._preview_fonts[0]}",
            font=(T.FONT_FAMILY_UI, T.FONT_SM),
            text_color=T.TEXT_MUTED
        )
        self._font_lbl.pack(side="left")
        ctk.CTkButton(
            prev_foot, text="T  Change Font", width=110, height=28,
            font=(T.FONT_FAMILY_UI, T.FONT_SM),
            fg_color=T.BTN_SECONDARY_BG, hover_color=T.BTN_SECONDARY_HOVER,
            text_color=T.TEXT_SECONDARY, corner_radius=6,
            command=self._cycle_font
        ).pack(side="right")

        # Other formats card
        fmt_card = CardFrame(parent)
        fmt_card.pack(fill="x", pady=(0, 10))

        fmt_header = ctk.CTkFrame(fmt_card, fg_color="transparent")
        fmt_header.pack(fill="x", padx=14, pady=(12, 0))
        ctk.CTkLabel(fmt_header, text="⬚  3. Other Formats",
                     font=(T.FONT_FAMILY_UI, T.FONT_BASE, "bold"),
                     text_color=T.TEXT_SECONDARY).pack(side="left")
        ctk.CTkButton(fmt_header, text="⧉  Copy", width=72, height=26,
                      font=(T.FONT_FAMILY_UI, T.FONT_SM),
                      fg_color=T.BTN_SECONDARY_BG, hover_color=T.BTN_SECONDARY_HOVER,
                      text_color=T.TEXT_SECONDARY, corner_radius=6,
                      command=lambda: self._copy_widget(self._fmt_code)
                      ).pack(side="right")

        # Tab strip
        tabs_frame = ctk.CTkFrame(fmt_card, fg_color="transparent")
        tabs_frame.pack(fill="x", padx=14, pady=(8, 0))

        self._tab_btns: dict[str, ctk.CTkButton] = {}
        tab_names = ["C++ Vector", "JSON", "Space Separated", "Unicode Escape"]
        for name in tab_names:
            is_sel = (name == self._current_tab)
            btn = ctk.CTkButton(
                tabs_frame, text=name, width=0,
                font=(T.FONT_FAMILY_UI, T.FONT_SM, "bold" if is_sel else "normal"),
                fg_color=T.BTN_PRIMARY_BG if is_sel else T.BG_TAB,
                hover_color=T.BTN_PRIMARY_HOVER if is_sel else T.BTN_SECONDARY_HOVER,
                text_color=T.TEXT_PRIMARY, corner_radius=6, height=28,
                command=lambda n=name: self._select_tab(n)
            )
            btn.pack(side="left", padx=(0, 4))
            self._tab_btns[name] = btn

        fmt_wrap = ctk.CTkFrame(fmt_card, fg_color=T.BG_CODE, corner_radius=8)
        fmt_wrap.pack(fill="x", padx=14, pady=(8, 14))
        self._fmt_code = CodeText(fmt_wrap, height=5)
        self._fmt_code.pack(fill="x")

    # ── Event handlers ────────────────────────────────────────────────────────
    def _on_input_change(self, _event=None):
        text = self._input_text.get("1.0", "end-1c")
        cps  = get_codepoints(text)
        nl_chars = [ch for ch in text if is_non_latin(ch)]

        # Char count (non-latin only)
        self._char_count_lbl.configure(text=f"Characters: {len(nl_chars)}")

        # Live preview — show only non-latin chars
        preview = "".join(nl_chars)
        self._preview_lbl.configure(text=preview)

        # C array
        self._array_code.set_code(format_c_array(cps))

        # Count
        self._count_code.set_code(format_count_statement(cps))

        # Other formats
        self._update_fmt_code(cps)

        # Quick info
        n = len(cps)
        utf8 = count_utf8_bytes(text)
        first = f"U+{cps[0]:04X}"  if cps else "—"
        last  = f"U+{cps[-1]:04X}" if cps else "—"
        usage = get_common_usage(cps)
        self._qi_decimal.set(str(n))
        self._qi_utf8.set(str(utf8))
        self._qi_first.set(first)
        self._qi_last.set(last)
        self._qi_usage.set(usage)

    def _update_fmt_code(self, cps: list[int]):
        tab = self._current_tab
        if tab == "C++ Vector":
            code = format_cpp_vector(cps)
        elif tab == "JSON":
            code = format_json(cps)
        elif tab == "Space Separated":
            code = format_space_separated(cps)
        else:  # Unicode Escape
            code = format_unicode_escape(cps)
        self._fmt_code.set_code(code)

    def _select_tab(self, name: str):
        self._current_tab = name
        for n, btn in self._tab_btns.items():
            is_sel = (n == name)
            btn.configure(
                fg_color=T.BTN_PRIMARY_BG if is_sel else T.BG_TAB,
                hover_color=T.BTN_PRIMARY_HOVER if is_sel else T.BTN_SECONDARY_HOVER,
                font=(T.FONT_FAMILY_UI, T.FONT_SM, "bold" if is_sel else "normal"),
            )
        text = self._input_text.get("1.0", "end-1c")
        self._update_fmt_code(get_codepoints(text))

    def _clear_input(self):
        self._input_text.delete("1.0", "end")
        self._on_input_change()

    def _copy_widget(self, widget: CodeText):
        content = widget.get_content()
        self.clipboard_clear()
        self.clipboard_append(content)

    def _copy_all(self):
        text = self._input_text.get("1.0", "end-1c")
        cps  = get_codepoints(text)
        all_text = (
            f"=== C/C++ Array ===\n{format_c_array(cps)}\n\n"
            f"=== C++ Vector ===\n{format_cpp_vector(cps)}\n\n"
            f"=== JSON ===\n{format_json(cps)}\n\n"
            f"=== Space Separated ===\n{format_space_separated(cps)}\n\n"
            f"=== Unicode Escape ===\n{format_unicode_escape(cps)}\n\n"
            f"=== Count ===\n{format_count_statement(cps)}"
        )
        self.clipboard_clear()
        self.clipboard_append(all_text)

    def _cycle_font(self):
        self._font_index = (self._font_index + 1) % len(self._preview_fonts)
        fname = self._preview_fonts[self._font_index]
        self._preview_lbl.configure(font=(fname, T.FONT_2XL))
        self._font_lbl.configure(text=f"Font: {fname}")

    def _toggle_theme(self):
        # Placeholder — dark mode is the primary mode; light would need
        # a full re-theme pass which is out of scope for now.
        pass


# ── Settings page ─────────────────────────────────────────────────────────────
class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        ctk.CTkLabel(self, text="⚙  Settings",
                     font=(T.FONT_FAMILY_UI, T.FONT_XL, "bold"),
                     text_color=T.TEXT_PRIMARY).pack(anchor="w", padx=24, pady=24)

        card = CardFrame(self)
        card.pack(fill="x", padx=24)

        rows = [
            ("Include Latin characters", "When enabled, Latin printable characters are also converted."),
            ("Show hex prefix (0x)",     "Prefix hex codepoints with 0x."),
            ("Uppercase hex",             "Use uppercase hex digits (e.g. 0X4F60 → 0X4F60)."),
        ]
        for i, (title, desc) in enumerate(rows):
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=(12 if i == 0 else 4, 4))
            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(left, text=title,
                         font=(T.FONT_FAMILY_UI, T.FONT_BASE, "bold"),
                         text_color=T.TEXT_PRIMARY).pack(anchor="w")
            ctk.CTkLabel(left, text=desc,
                         font=(T.FONT_FAMILY_UI, T.FONT_SM),
                         text_color=T.TEXT_MUTED).pack(anchor="w")
            ctk.CTkSwitch(row, text="", onvalue=True, offvalue=False,
                          button_color=T.ACCENT_PURPLE, progress_color=T.ACCENT_PURPLE_L
                          ).pack(side="right", padx=8)

        ctk.CTkFrame(card, fg_color="transparent", height=12).pack()


# ── About page ────────────────────────────────────────────────────────────────
class AboutPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        ctk.CTkLabel(self, text="ⓘ  About",
                     font=(T.FONT_FAMILY_UI, T.FONT_XL, "bold"),
                     text_color=T.TEXT_PRIMARY).pack(anchor="w", padx=24, pady=24)

        card = CardFrame(self)
        card.pack(fill="x", padx=24)

        try:
            logo_img = ctk.CTkImage(
                light_image=Image.open(asset("logo.png")),
                dark_image=Image.open(asset("logo.png")),
                size=(120, 60)
            )
            ctk.CTkLabel(card, image=logo_img, text="").pack(pady=(20, 4))
        except Exception:
            pass

        ctk.CTkLabel(card, text="GlyphAtlas v1.0.0",
                     font=(T.FONT_FAMILY_UI, T.FONT_LG, "bold"),
                     text_color=T.TEXT_PRIMARY).pack(pady=(4, 2))
        ctk.CTkLabel(card, text="Unicode to Codepoint Converter — Made simple.",
                     font=(T.FONT_FAMILY_UI, T.FONT_SM),
                     text_color=T.TEXT_SECONDARY).pack(pady=(0, 6))
        ctk.CTkLabel(card,
                     text="GlyphAtlas converts non-Latin Unicode characters into C/C++ codepoint arrays.\n"
                          "Ideal for game developers, embedded engineers, and anyone working with\n"
                          "multi-language text in native codebases.",
                     font=(T.FONT_FAMILY_UI, T.FONT_SM),
                     text_color=T.TEXT_MUTED,
                     justify="center").pack(pady=(0, 20))


# ── Main Application ──────────────────────────────────────────────────────────
class GlyphAtlasApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GlyphAtlas")
        self.geometry("1080x700")
        self.minsize(900, 600)
        self.configure(fg_color=T.BG_DARKEST)

        # Window icon
        try:
            ico = Image.open(asset("logo.png"))
            self.iconphoto(True, tk.PhotoImage(file=asset("logo.png")))
        except Exception:
            pass

        self._pages: dict[str, ctk.CTkFrame] = {}
        self._nav_items: dict[str, NavItem] = {}
        self._current_page = "Converter"

        self._build_layout()
        self._show_page("Converter")

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_layout(self):
        self.columnconfigure(0, weight=0, minsize=200)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        self._build_sidebar()
        self._build_main_area()
        self._build_status_bar()

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, fg_color=T.BG_SIDEBAR, corner_radius=0,
                               border_width=1, border_color=T.BORDER_DEFAULT,
                               width=200)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        # ── Logo area ─────────────────────────────────────────────────────────
        logo_area = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_area.pack(fill="x", padx=16, pady=(20, 24))

        try:
            logo_img = ctk.CTkImage(
                light_image=Image.open(asset("logo.png")),
                dark_image=Image.open(asset("logo.png")),
                size=(168, 60)
            )
            ctk.CTkLabel(logo_area, image=logo_img, text="").pack()
        except Exception:
            ctk.CTkLabel(logo_area, text="GlyphAtlas",
                         font=(T.FONT_FAMILY_UI, 20, "bold"),
                         text_color=T.ACCENT_PURPLE_L,
                         fg_color="transparent"
                         ).pack()

        # ── Divider ───────────────────────────────────────────────────────────
        ctk.CTkFrame(sidebar, fg_color=T.BORDER_DEFAULT, height=1).pack(fill="x", padx=12, pady=(0, 12))

        # ── Nav items ─────────────────────────────────────────────────────────
        nav_defs = [
            ("</>", "Converter"),
            ("⚙",   "Settings"),
            ("ⓘ",   "About"),
        ]
        nav_container = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_container.pack(fill="x")

        for icon, label in nav_defs:
            item = NavItem(nav_container, icon=icon, label=label,
                           selected=(label == self._current_page),
                           command=lambda l=label: self._show_page(l))
            item.pack(fill="x")
            self._nav_items[label] = item

        # ── Bottom user badge ─────────────────────────────────────────────────
        bottom = ctk.CTkFrame(sidebar, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=14, pady=14)
        ctk.CTkFrame(bottom, fg_color=T.BORDER_DEFAULT, height=1).pack(fill="x", pady=(0, 10))

        badge_row = ctk.CTkFrame(bottom, fg_color="transparent")
        badge_row.pack(fill="x")

        avatar = ctk.CTkLabel(badge_row, text="GA",
                              font=(T.FONT_FAMILY_UI, 12, "bold"),
                              text_color=T.TEXT_PRIMARY,
                              fg_color=T.ACCENT_PURPLE, corner_radius=20,
                              width=34, height=34)
        avatar.pack(side="left")

        info = ctk.CTkFrame(badge_row, fg_color="transparent")
        info.pack(side="left", padx=(8, 0))
        ctk.CTkLabel(info, text="GlyphAtlas v1.0.0",
                     font=(T.FONT_FAMILY_UI, 11, "bold"),
                     text_color=T.TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(info, text="Crafted for developers.",
                     font=(T.FONT_FAMILY_UI, 10),
                     text_color=T.TEXT_MUTED).pack(anchor="w")

    def _build_main_area(self):
        main = ctk.CTkFrame(self, fg_color=T.BG_DARKEST, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.rowconfigure(0, weight=1)
        main.columnconfigure(0, weight=1)
        self._main_container = main

        # Build all pages (hidden by default)
        self._pages["Converter"] = ConverterPage(main)
        self._pages["Settings"]  = SettingsPage(main)
        self._pages["About"]     = AboutPage(main)

        for page in self._pages.values():
            page.grid(row=0, column=0, sticky="nsew")

    def _build_status_bar(self):
        bar = ctk.CTkFrame(self, fg_color=T.BG_CODE, corner_radius=0,
                           height=30, border_width=1, border_color=T.BORDER_DEFAULT)
        bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        bar.grid_propagate(False)

        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.pack(side="left", padx=16, fill="y")

        # Green dot + "Ready to convert"
        dot = ctk.CTkLabel(left, text="●", font=(T.FONT_FAMILY_UI, 12),
                           text_color=T.TEXT_GREEN)
        dot.pack(side="left", pady=6)
        ctk.CTkLabel(left, text=" Ready to convert",
                     font=(T.FONT_FAMILY_UI, T.FONT_SM),
                     text_color=T.TEXT_MUTED).pack(side="left", pady=6)

        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.pack(side="right", padx=16, fill="y")
        ctk.CTkLabel(right, text="UTF-8  ●  No errors  ✓",
                     font=(T.FONT_FAMILY_UI, T.FONT_SM),
                     text_color=T.TEXT_MUTED).pack(side="right", pady=6)

    # ── Page navigation ───────────────────────────────────────────────────────
    def _show_page(self, name: str):
        self._current_page = name
        for n, item in self._nav_items.items():
            item.set_selected(n == name)
        for n, page in self._pages.items():
            if n == name:
                page.tkraise()
