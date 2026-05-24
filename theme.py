
# ── Backgrounds ──────────────────────────────────────────────────────────────
BG_DARKEST   = "#0d0d12"   # window / root background
BG_SIDEBAR   = "#111118"   # sidebar panel
BG_CARD      = "#16161f"   # card / panel background
BG_INPUT     = "#1a1a26"   # text-input field
BG_CODE      = "#13131c"   # code blocks
BG_HOVER     = "#1e1e2e"   # hover state for nav items
BG_SELECTED  = "#24204a"   # selected nav item (purple tint)
BG_TAB       = "#1a1a26"   # unselected tab
BG_TAB_SEL   = "#6c47cc"   # selected tab (accent purple)
BG_STATUS    = "#0d0d12"   # status bar

# ── Borders ───────────────────────────────────────────────────────────────────
BORDER_DEFAULT = "#2a2a3d"
BORDER_ACCENT  = "#5a3fa0"
BORDER_INPUT   = "#3d3d5c"

# ── Text ──────────────────────────────────────────────────────────────────────
TEXT_PRIMARY    = "#e8e8f0"
TEXT_SECONDARY  = "#8888aa"
TEXT_MUTED      = "#55557a"
TEXT_ACCENT     = "#a97ef5"   # purple accent labels
TEXT_CODE_BASE  = "#c5c5e0"
TEXT_CODE_TYPE  = "#569cd6"   # int / std::vector  (blue)
TEXT_CODE_HEX   = "#9d7fe3"   # 0x hex values       (purple)
TEXT_CODE_PUNC  = "#c5c5e0"   # braces, commas
TEXT_GREEN      = "#4ec994"
TEXT_YELLOW     = "#f0c060"

# ── Accent / Brand ────────────────────────────────────────────────────────────
ACCENT_PURPLE   = "#7c4ddf"
ACCENT_PURPLE_L = "#a97ef5"
ACCENT_BLUE     = "#4a7cf5"

# ── Buttons ───────────────────────────────────────────────────────────────────
BTN_PRIMARY_BG      = "#6c47cc"
BTN_PRIMARY_HOVER   = "#7c55dd"
BTN_SECONDARY_BG    = "#1e1e2e"
BTN_SECONDARY_HOVER = "#252535"

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONT_FAMILY_UI   = "Segoe UI"
FONT_FAMILY_CODE = "Consolas"
FONT_FAMILY_MONO = "Courier New"

FONT_SM   = 11
FONT_BASE = 13
FONT_MD   = 14
FONT_LG   = 16
FONT_XL   = 22
FONT_2XL  = 32

# ── Misc ──────────────────────────────────────────────────────────────────────
RADIUS = 10   # default corner radius
CARD_PAD = 12

# ── Theme palettes ────────────────────────────────────────────────────────────
DARK = dict(
    BG_DARKEST="#0d0d12", BG_SIDEBAR="#111118", BG_CARD="#16161f",
    BG_INPUT="#1a1a26", BG_CODE="#13131c", BG_HOVER="#1e1e2e",
    BG_SELECTED="#24204a", BG_TAB="#1a1a26", BG_STATUS="#0d0d12",
    BORDER_DEFAULT="#2a2a3d", BORDER_ACCENT="#5a3fa0", BORDER_INPUT="#3d3d5c",
    TEXT_PRIMARY="#e8e8f0", TEXT_SECONDARY="#8888aa", TEXT_MUTED="#55557a",
    TEXT_ACCENT="#a97ef5", TEXT_CODE_BASE="#c5c5e0", TEXT_CODE_TYPE="#569cd6",
    TEXT_CODE_HEX="#9d7fe3", TEXT_CODE_PUNC="#c5c5e0", TEXT_GREEN="#4ec994",
    TEXT_YELLOW="#f0c060",
    ACCENT_PURPLE="#7c4ddf", ACCENT_PURPLE_L="#a97ef5", ACCENT_BLUE="#4a7cf5",
    BTN_PRIMARY_BG="#6c47cc", BTN_PRIMARY_HOVER="#7c55dd",
    BTN_SECONDARY_BG="#1e1e2e", BTN_SECONDARY_HOVER="#252535",
)

LIGHT = dict(
    BG_DARKEST="#f0f0f5", BG_SIDEBAR="#dddde8", BG_CARD="#e8e8f0",
    BG_INPUT="#f5f5fa", BG_CODE="#f0f0f8", BG_HOVER="#e0e0eb",
    BG_SELECTED="#d8d0f0", BG_TAB="#eaeaf0", BG_STATUS="#f0f0f5",
    BORDER_DEFAULT="#c8c8d8", BORDER_ACCENT="#8060d0", BORDER_INPUT="#b0b0c8",
    TEXT_PRIMARY="#1a1a2e", TEXT_SECONDARY="#555570", TEXT_MUTED="#888898",
    TEXT_ACCENT="#6a3dc0", TEXT_CODE_BASE="#2d2d44", TEXT_CODE_TYPE="#0550ae",
    TEXT_CODE_HEX="#6e40c9", TEXT_CODE_PUNC="#2d2d44", TEXT_GREEN="#1a7f37",
    TEXT_YELLOW="#9a6700",
    ACCENT_PURPLE="#7c4ddf", ACCENT_PURPLE_L="#6a3dc0", ACCENT_BLUE="#3060d0",
    BTN_PRIMARY_BG="#6c47cc", BTN_PRIMARY_HOVER="#7c55dd",
    BTN_SECONDARY_BG="#e0e0eb", BTN_SECONDARY_HOVER="#d0d0dd",
)


def get_palette(mode: str = "dark") -> dict:
    """Return the palette dict for the given mode."""
    return LIGHT if mode == "light" else DARK
