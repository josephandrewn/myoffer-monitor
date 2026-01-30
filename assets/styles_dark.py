# styles.py
# MyOffer Monitor - Dev Tool Dark Theme
# Terminal-inspired with syntax highlighting colors and a techy feel

# --- COLOR PALETTE ---
# Dark theme with vibrant accents inspired by popular code editors
COLORS = {
    # Backgrounds - Deep, rich darks
    "bg_main": "#0D1117",           # GitHub dark background
    "bg_white": "#161B22",          # Elevated surfaces (cards)
    "bg_elevated": "#1C2128",       # Higher elevation
    "bg_subtle": "#21262D",         # Subtle differentiation
    "bg_input": "#0D1117",          # Input fields
    
    # Text - Clear hierarchy
    "text_primary": "#E6EDF3",      # Primary text (off-white)
    "text_secondary": "#8B949E",    # Secondary text
    "text_tertiary": "#6E7681",     # Muted text
    "text_inverse": "#0D1117",      # Dark text on light bg
    
    # Borders & Dividers
    "border": "#30363D",            # Standard border
    "border_light": "#21262D",      # Subtle border
    "border_focus": "#58A6FF",      # Focus ring
    "divider": "#21262D",           # Table lines
    
    # Brand Accent - Electric cyan/blue
    "accent": "#58A6FF",            # Bright blue (links, primary)
    "accent_hover": "#79C0FF",      # Lighter on hover
    "accent_subtle": "#388BFD26",   # Transparent accent
    "accent_muted": "#1F6FEB",      # Darker accent
    
    # Syntax Highlighting Colors (semantic)
    "success": "#3FB950",           # Green - like string literals
    "success_hover": "#56D364",
    "success_subtle": "#238636",
    "success_bg": "#12261E",
    
    "warning": "#D29922",           # Yellow/Gold - like warnings
    "warning_hover": "#E3B341",
    "warning_subtle": "#9E6A03",
    "warning_bg": "#2D2305",
    
    "danger": "#F85149",            # Red - like errors
    "danger_hover": "#FF7B72",
    "danger_subtle": "#DA3633",
    "danger_bg": "#2D1214",
    
    "info": "#58A6FF",              # Blue - like keywords
    "info_bg": "#0D2240",
    
    "purple": "#A371F7",            # Purple - like functions
    "orange": "#FFA657",            # Orange - like numbers
    "cyan": "#39D4BA",              # Cyan - like types
    
    # Row Status Colors - Dark theme versions
    "row_pass_bg": "#12261E",       # Dark green
    "row_pass_text": "#3FB950",     # Bright green
    
    "row_fail_bg": "#2D1214",       # Dark red
    "row_fail_text": "#F85149",     # Bright red
    
    "row_warn_bg": "#2D2305",       # Dark yellow
    "row_warn_text": "#D29922",     # Gold
    
    "row_pending_bg": "#161B22",    # Card background
    "row_pending_text": "#8B949E",  # Secondary text
    
    "row_blocked_bg": "#1C2128",    # Elevated bg
    "row_blocked_text": "#6E7681",  # Muted text
    
    "row_unverifiable_bg": "#2D1B06", # Dark orange
    "row_unverifiable_text": "#FFA657", # Bright orange
    
    "row_inactive_bg": "#0D1117",   # Main bg
    "row_inactive_text": "#484F58", # Very muted
}

# --- GLOBAL STYLESHEET ---
MODERN_STYLESHEET = f"""
    /* ============================================
       GLOBAL STYLES - Dark Theme
       ============================================ */
    * {{
        background-color: {COLORS["bg_main"]};
    }}
    
    QMainWindow {{
        background-color: {COLORS["bg_main"]};
    }}
    
    QWidget {{
        font-family: "SF Mono", "JetBrains Mono", "Fira Code", "Cascadia Code", "Consolas", monospace;
        font-size: 13px;
        color: {COLORS["text_primary"]};
        background-color: {COLORS["bg_main"]};
    }}
    
    QWidget#central_widget {{
        background-color: {COLORS["bg_main"]};
    }}

    /* ============================================
       TAB WIDGET - Terminal-style tabs (full width)
       ============================================ */
    QTabWidget {{
        background-color: {COLORS["bg_main"]};
        border: none;
    }}
    
    QTabWidget::pane {{
        background-color: {COLORS["bg_white"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 0px 0px 8px 8px;
        top: 0px;
    }}
    
    QTabBar {{
        qproperty-drawBase: 0;
        background-color: {COLORS["bg_main"]};
    }}
    
    /* The area behind tabs (empty space) */
    QTabWidget > QWidget {{
        background-color: {COLORS["bg_main"]};
    }}
    
    /* Make tabs expand to fill width - each tab takes equal space */
    QTabBar::tab {{
        background: {COLORS["bg_elevated"]};
        border: 1px solid {COLORS["border"]};
        border-bottom: none;
        padding: 14px 24px;
        margin-right: 0px;
        font-weight: 600;
        font-size: 13px;
        color: {COLORS["text_secondary"]};
        letter-spacing: 0.5px;
        min-width: 150px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
    }}
    
    QTabBar::tab:selected {{
        background: {COLORS["bg_white"]};
        color: {COLORS["accent"]};
        border: 1px solid {COLORS["border"]};
        border-bottom: 2px solid {COLORS["bg_white"]};
        margin-bottom: -1px;
    }}
    
    QTabBar::tab:!selected {{
        margin-top: 4px;
        background: {COLORS["bg_subtle"]};
    }}
    
    QTabBar::tab:!selected:hover {{
        background: {COLORS["bg_elevated"]};
        color: {COLORS["text_primary"]};
    }}

    /* ============================================
       BUTTONS - Subtle with glowing hover states
       ============================================ */
    QPushButton {{
        background-color: {COLORS["bg_subtle"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 600;
        font-size: 12px;
        color: {COLORS["text_primary"]};
        min-height: 18px;
    }}
    
    QPushButton:hover {{
        background-color: {COLORS["bg_elevated"]};
        border-color: {COLORS["text_tertiary"]};
    }}
    
    QPushButton:pressed {{
        background-color: {COLORS["bg_main"]};
    }}
    
    QPushButton:disabled {{
        color: {COLORS["text_tertiary"]};
        background-color: {COLORS["bg_main"]};
        border-color: {COLORS["border_light"]};
    }}
    
    /* Primary Button - Accent color with glow effect */
    QPushButton#btn_primary {{
        background-color: {COLORS["accent_muted"]};
        color: {COLORS["text_primary"]};
        border: 1px solid {COLORS["accent"]};
        padding: 8px 20px;
    }}
    QPushButton#btn_primary:hover {{
        background-color: {COLORS["accent"]};
        color: {COLORS["text_inverse"]};
    }}
    QPushButton#btn_primary:pressed {{
        background-color: {COLORS["accent_muted"]};
    }}
    QPushButton#btn_primary:disabled {{
        background-color: {COLORS["bg_subtle"]};
        border-color: {COLORS["border"]};
        color: {COLORS["text_tertiary"]};
    }}
    
    /* Success Button - Green terminal style */
    QPushButton#btn_success {{
        background-color: {COLORS["success_subtle"]};
        color: {COLORS["success"]};
        border: 1px solid {COLORS["success"]};
        padding: 8px 20px;
    }}
    QPushButton#btn_success:hover {{
        background-color: {COLORS["success"]};
        color: {COLORS["text_inverse"]};
    }}

    /* Danger Button - Red alert style */
    QPushButton#btn_danger {{
        background-color: {COLORS["danger_subtle"]};
        color: {COLORS["danger"]};
        border: 1px solid {COLORS["danger"]};
        padding: 8px 20px;
    }}
    QPushButton#btn_danger:hover {{
        background-color: {COLORS["danger"]};
        color: {COLORS["text_primary"]};
    }}

    /* ============================================
       TABLE - Data grid with syntax colors
       ============================================ */
    QTableWidget {{
        background-color: {COLORS["bg_white"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        gridline-color: {COLORS["border_light"]};
        selection-background-color: {COLORS["accent_subtle"]};
        selection-color: {COLORS["text_primary"]};
        outline: none;
    }}
    
    QTableWidget::item {{
        padding: 6px 12px;
        border-bottom: 1px solid {COLORS["border_light"]};
        min-height: 20px;
    }}
    
    QTableWidget::item:selected {{
        background-color: {COLORS["accent_subtle"]};
        border-left: 2px solid {COLORS["accent"]};
    }}
    
    QHeaderView {{
        background-color: {COLORS["bg_elevated"]};
    }}
    
    /* Horizontal header (column names) */
    QHeaderView::section {{
        background-color: {COLORS["bg_elevated"]};
        padding: 12px 12px;
        border: none;
        border-bottom: 1px solid {COLORS["border"]};
        border-right: 1px solid {COLORS["border_light"]};
        font-weight: 700;
        font-size: 11px;
        color: {COLORS["purple"]};
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    QHeaderView::section:last {{
        border-right: none;
    }}
    
    /* Vertical header (row numbers) */
    QHeaderView::section:vertical {{
        background-color: {COLORS["bg_elevated"]};
        padding: 4px 8px;
        border: none;
        border-bottom: 1px solid {COLORS["border_light"]};
        border-right: 1px solid {COLORS["border"]};
        font-weight: 600;
        font-size: 11px;
        color: {COLORS["text_tertiary"]};
        min-height: 24px;
    }}

    /* Custom Scrollbars - Minimal dark style */
    QScrollBar:vertical {{
        background: {COLORS["bg_main"]};
        width: 12px;
        border-radius: 6px;
        margin: 0;
    }}
    
    QScrollBar::handle:vertical {{
        background: {COLORS["border"]};
        border-radius: 6px;
        min-height: 40px;
        margin: 2px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background: {COLORS["text_tertiary"]};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QScrollBar:horizontal {{
        background: {COLORS["bg_main"]};
        height: 12px;
        border-radius: 6px;
    }}
    
    QScrollBar::handle:horizontal {{
        background: {COLORS["border"]};
        border-radius: 6px;
        min-width: 40px;
        margin: 2px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background: {COLORS["text_tertiary"]};
    }}

    /* ============================================
       INPUT FIELDS - Terminal-style inputs
       ============================================ */
    QLineEdit {{
        background-color: {COLORS["bg_input"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 6px;
        padding: 10px 14px;
        font-size: 13px;
        color: {COLORS["text_primary"]};
        selection-background-color: {COLORS["accent_subtle"]};
        selection-color: {COLORS["text_primary"]};
    }}
    
    QLineEdit:focus {{
        border: 1px solid {COLORS["accent"]};
        background-color: {COLORS["bg_white"]};
    }}
    
    QLineEdit:disabled {{
        background-color: {COLORS["bg_main"]};
        color: {COLORS["text_tertiary"]};
        border-color: {COLORS["border_light"]};
    }}
    
    QLineEdit::placeholder {{
        color: {COLORS["text_tertiary"]};
    }}

    /* ============================================
       COMBOBOX - Dropdown styling
       ============================================ */
    QComboBox {{
        background-color: {COLORS["bg_subtle"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 6px;
        padding: 8px 14px;
        padding-right: 30px;
        font-size: 13px;
        color: {COLORS["text_primary"]};
        min-width: 130px;
    }}
    
    QComboBox:hover {{
        border-color: {COLORS["text_tertiary"]};
    }}
    
    QComboBox:focus {{
        border-color: {COLORS["accent"]};
    }}
    
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: center right;
        width: 24px;
        border: none;
        background: transparent;
    }}
    
    QComboBox::down-arrow {{
        border: none;
        background: none;
        width: 0;
        height: 0;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {COLORS["text_secondary"]};
    }}
    
    QComboBox::down-arrow:hover {{
        border-top-color: {COLORS["accent"]};
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {COLORS["bg_elevated"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 6px;
        padding: 4px;
        selection-background-color: {COLORS["accent_subtle"]};
        selection-color: {COLORS["text_primary"]};
        outline: none;
    }}
    
    QComboBox QAbstractItemView::item {{
        padding: 8px 12px;
        border-radius: 4px;
        color: {COLORS["text_primary"]};
        min-height: 20px;
    }}
    
    QComboBox QAbstractItemView::item:hover {{
        background-color: {COLORS["bg_subtle"]};
    }}

    /* ============================================
       FRAMES & CARDS
       ============================================ */
    QFrame {{
        background-color: {COLORS["bg_main"]};
    }}
    
    QFrame#top_control_frame {{
        background-color: {COLORS["bg_white"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
    }}
    
    /* Layout containers */
    QVBoxLayout, QHBoxLayout {{
        background-color: {COLORS["bg_main"]};
    }}

    /* ============================================
       PROGRESS BAR - Cyberpunk style
       ============================================ */
    QProgressBar {{
        border: 1px solid {COLORS["border"]};
        background-color: {COLORS["bg_main"]};
        border-radius: 4px;
        height: 8px;
        text-align: center;
    }}
    
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS["cyan"]},
            stop:0.5 {COLORS["accent"]},
            stop:1 {COLORS["purple"]});
        border-radius: 3px;
    }}

    /* ============================================
       LABELS
       ============================================ */
    QLabel {{
        color: {COLORS["text_primary"]};
        background: transparent;
    }}
    
    QLabel#header_label {{
        font-size: 16px;
        font-weight: 700;
        color: {COLORS["text_primary"]};
        letter-spacing: 0.5px;
    }}
    
    QLabel#subtitle_label {{
        font-size: 12px;
        color: {COLORS["text_secondary"]};
    }}
    
    QLabel#accent_label {{
        color: {COLORS["accent"]};
    }}

    /* ============================================
       MESSAGE BOX
       ============================================ */
    QMessageBox {{
        background-color: {COLORS["bg_white"]};
    }}
    
    QMessageBox QLabel {{
        color: {COLORS["text_primary"]};
        font-size: 13px;
    }}
    
    QMessageBox QPushButton {{
        min-width: 80px;
        padding: 8px 20px;
    }}

    /* ============================================
       TOOLTIPS - Dark tooltip
       ============================================ */
    QToolTip {{
        background-color: {COLORS["bg_elevated"]};
        color: {COLORS["text_primary"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 4px;
        padding: 8px 12px;
        font-size: 12px;
    }}

    /* ============================================
       STATUS BAR (if used)
       ============================================ */
    QStatusBar {{
        background-color: {COLORS["bg_main"]};
        color: {COLORS["text_secondary"]};
        border-top: 1px solid {COLORS["border"]};
    }}

    /* ============================================
       TOOLBAR - Dark styled
       ============================================ */
    QToolBar {{
        background-color: {COLORS["bg_main"]};
        border: none;
        border-bottom: 1px solid {COLORS["border"]};
        padding: 8px 12px;
        spacing: 8px;
    }}
    
    QToolBar::separator {{
        background-color: {COLORS["border"]};
        width: 1px;
        margin: 4px 8px;
    }}

    /* ============================================
       MENU BAR - Dark styled
       ============================================ */
    QMenuBar {{
        background-color: {COLORS["bg_main"]};
        color: {COLORS["text_primary"]};
        border-bottom: 1px solid {COLORS["border"]};
        padding: 4px 8px;
    }}
    
    QMenuBar::item {{
        background: transparent;
        padding: 6px 12px;
        border-radius: 4px;
    }}
    
    QMenuBar::item:selected {{
        background-color: {COLORS["bg_subtle"]};
    }}
    
    QMenuBar::item:pressed {{
        background-color: {COLORS["bg_elevated"]};
    }}

    /* ============================================
       MENU (Dropdown) - Dark styled
       ============================================ */
    QMenu {{
        background-color: {COLORS["bg_elevated"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        padding: 6px;
    }}
    
    QMenu::item {{
        padding: 8px 24px 8px 12px;
        border-radius: 4px;
        color: {COLORS["text_primary"]};
    }}
    
    QMenu::item:selected {{
        background-color: {COLORS["accent_subtle"]};
        color: {COLORS["text_primary"]};
    }}
    
    QMenu::item:disabled {{
        color: {COLORS["text_tertiary"]};
    }}
    
    QMenu::separator {{
        height: 1px;
        background-color: {COLORS["border"]};
        margin: 6px 8px;
    }}
    
    QMenu::icon {{
        margin-left: 8px;
    }}
"""

# --- ADDITIONAL STYLE HELPERS ---

def get_status_style(status: str) -> dict:
    """Get background and text colors for a status."""
    status_map = {
        'PASS': ('row_pass_bg', 'row_pass_text'),
        'FAIL': ('row_fail_bg', 'row_fail_text'),
        'WARN': ('row_warn_bg', 'row_warn_text'),
        'BLOCKED': ('row_blocked_bg', 'row_blocked_text'),
        'UNVERIFIABLE': ('row_unverifiable_bg', 'row_unverifiable_text'),
        'PENDING': ('row_pending_bg', 'row_pending_text'),
        'ERROR': ('row_fail_bg', 'row_fail_text'),
    }
    bg_key, text_key = status_map.get(status, ('row_pending_bg', 'row_pending_text'))
    return {
        'background': COLORS[bg_key],
        'color': COLORS[text_key]
    }


def get_syntax_color(element: str) -> str:
    """Get syntax highlighting colors for special elements."""
    syntax_map = {
        'keyword': COLORS["accent"],      # Blue - keywords, links
        'string': COLORS["success"],      # Green - success, strings
        'number': COLORS["orange"],       # Orange - numbers, counts
        'function': COLORS["purple"],     # Purple - functions, headers
        'type': COLORS["cyan"],           # Cyan - types, special
        'error': COLORS["danger"],        # Red - errors
        'warning': COLORS["warning"],     # Yellow - warnings
        'comment': COLORS["text_tertiary"], # Gray - muted
    }
    return syntax_map.get(element, COLORS["text_primary"])


# --- APP METADATA ---
APP_NAME = "MyOffer Monitor"
APP_VERSION = "1.0.0"
APP_THEME = "Dev Tool Dark"
