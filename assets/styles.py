# styles.py
# MyOffer Monitor - Branded Light Theme
# Clean, professional design with MyOffer blue brand colors

# --- COLOR PALETTE ---
# Brand colors from the logo
COLORS = {
    # Brand Blues
    "brand_primary": "#207ADC",      # Main brand blue
    "brand_light": "#66C4FF",        # Light accent blue
    "brand_dark": "#002F6E",         # Dark navy blue
    
    # Backgrounds - Warm light grays
    "bg_main": "#F5F5F5",            # Main background (off-white)
    "bg_white": "#F5F5F5",           # Cards and elevated surfaces
    "bg_subtle": "#E5E5E5",          # Subtle differentiation
    "bg_hover": "#D8E8F8",           # Hover state (light blue tint)
    
    # Text
    "text_primary": "#1A1A2E",       # Near black with slight blue
    "text_secondary": "#5A6978",     # Medium gray-blue
    "text_tertiary": "#8E99A4",      # Light gray
    "text_inverse": "#FFFFFF",       # White text
    
    # Borders
    "border": "#C8D1DA",             # Soft blue-gray border
    "border_light": "#DEE5EC",       # Very subtle border
    "divider": "#E8ECF0",            # Table lines
    
    # Accent (using brand primary)
    "accent": "#207ADC",             # Brand blue
    "accent_hover": "#1A68BC",       # Darker on hover
    "accent_light": "#E8F2FC",       # Very light blue for highlights
    "accent_subtle": "#D0E4F7",      # Subtle blue background
    
    # Semantic Colors - Harmonized with brand
    "success": "#10A37F",            # Teal-green (complements blue)
    "success_hover": "#0D8A6A",
    "success_light": "#E6F7F2",
    
    "warning": "#E67E22",            # Warm orange
    "warning_hover": "#D35400",
    "warning_light": "#FEF5E7",
    
    "danger": "#DC3545",             # Red
    "danger_hover": "#C82333",
    "danger_light": "#FDEAEA",
    
    # Row Status Colors
    "row_pass_bg": "#E6F7F2",        # Light teal
    "row_pass_text": "#0D7A5F",      # Dark teal
    
    "row_fail_bg": "#FDEAEA",        # Light red
    "row_fail_text": "#A71D2A",      # Dark red
    
    "row_warn_bg": "#FEF5E7",        # Light orange
    "row_warn_text": "#9A5B13",      # Dark orange
    
    "row_pending_bg": "#FFFFFF",     # White
    "row_pending_text": "#5A6978",   # Secondary text
    
    "row_blocked_bg": "#F0F3F6",     # Light gray
    "row_blocked_text": "#5A6978",   # Secondary text
    
    "row_unverifiable_bg": "#FEF3C7", # Light amber/yellow
    "row_unverifiable_text": "#92400E", # Dark amber (very readable)
    
    "row_inactive_bg": "#F5F5F5",    # Very light gray
    "row_inactive_text": "#A0A0A0",  # Muted
}

# --- GLOBAL STYLESHEET ---
MODERN_STYLESHEET = f"""
    /* ============================================
       GLOBAL STYLES - Branded Light Theme
       ============================================ */
    * {{
        background-color: {COLORS["bg_main"]};
    }}
    
    QMainWindow {{
        background-color: {COLORS["bg_main"]};
    }}
    
    QWidget {{
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        font-size: 13px;
        color: {COLORS["text_primary"]};
        background-color: {COLORS["bg_main"]};
    }}
    
    QWidget#central_widget {{
        background-color: {COLORS["bg_main"]};
    }}

    /* ============================================
       TAB WIDGET - Brand-colored tabs
       ============================================ */
    QTabWidget {{
        background-color: {COLORS["bg_main"]};
        border: none;
    }}
    
    QTabWidget::pane {{
        background-color: {COLORS["bg_white"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 0px 0px 10px 10px;
        top: 0px;
    }}
    
    QTabBar {{
        qproperty-drawBase: 0;
        background-color: {COLORS["bg_main"]};
    }}
    
    QTabWidget > QWidget {{
        background-color: {COLORS["bg_main"]};
    }}
    
    /* Tabs expand to fill width */
    QTabBar::tab {{
        background-color: {COLORS["bg_subtle"]};
        border: 1px solid {COLORS["border"]};
        border-bottom: none;
        padding: 14px 24px;
        font-weight: 600;
        font-size: 14px;
        color: {COLORS["text_secondary"]};
        min-width: 150px;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
    }}
    
    QTabBar::tab:selected {{
        background-color: {COLORS["bg_white"]};
        color: {COLORS["brand_primary"]};
        border: 1px solid {COLORS["border"]};
        border-bottom: 2px solid {COLORS["bg_white"]};
        margin-bottom: -1px;
    }}
    
    QTabBar::tab:!selected {{
        margin-top: 4px;
        background-color: {COLORS["bg_subtle"]};
        border-bottom: 1px solid {COLORS["border"]};
    }}
    
    QTabBar::tab:!selected:hover {{
        background-color: {COLORS["bg_hover"]};
        color: {COLORS["brand_primary"]};
    }}

    /* ============================================
       BUTTONS - Brand styled
       ============================================ */
    QPushButton {{
        background-color: {COLORS["bg_white"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
        font-size: 13px;
        color: {COLORS["text_primary"]};
        min-height: 20px;
    }}
    
    QPushButton:hover {{
        background-color: {COLORS["bg_hover"]};
        border-color: {COLORS["brand_primary"]};
        color: {COLORS["brand_primary"]};
    }}
    
    QPushButton:pressed {{
        background-color: {COLORS["accent_subtle"]};
    }}
    
    QPushButton:disabled {{
        color: {COLORS["text_tertiary"]};
        background-color: {COLORS["bg_subtle"]};
        border-color: {COLORS["border_light"]};
    }}
    
    /* Primary Button - Brand blue */
    QPushButton#btn_primary {{
        background-color: {COLORS["brand_primary"]};
        color: {COLORS["text_inverse"]};
        border: none;
        padding: 8px 20px;
    }}
    QPushButton#btn_primary:hover {{
        background-color: {COLORS["accent_hover"]};
    }}
    QPushButton#btn_primary:pressed {{
        background-color: {COLORS["brand_dark"]};
    }}
    QPushButton#btn_primary:disabled {{
        background-color: {COLORS["text_tertiary"]};
    }}
    
    /* Success Button */
    QPushButton#btn_success {{
        background-color: {COLORS["success"]};
        color: {COLORS["text_inverse"]};
        border: none;
        padding: 8px 20px;
    }}
    QPushButton#btn_success:hover {{
        background-color: {COLORS["success_hover"]};
    }}

    /* Danger Button */
    QPushButton#btn_danger {{
        background-color: {COLORS["danger"]};
        color: {COLORS["text_inverse"]};
        border: none;
        padding: 8px 20px;
    }}
    QPushButton#btn_danger:hover {{
        background-color: {COLORS["danger_hover"]};
    }}

    /* Brand Button - MyOffer blue */
    QPushButton#btn_brand {{
        background-color: {COLORS["brand_primary"]};
        color: {COLORS["text_inverse"]};
        border: none;
        padding: 8px 20px;
    }}
    QPushButton#btn_brand:hover {{
        background-color: {COLORS["accent_hover"]};
    }}
    QPushButton#btn_brand:pressed {{
        background-color: {COLORS["brand_dark"]};
    }}

    /* ============================================
       TABLE - Clean with brand accents
       ============================================ */
    QTableWidget {{
        background-color: {COLORS["bg_white"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 0;
        gridline-color: {COLORS["divider"]};
        selection-background-color: {COLORS["accent_light"]};
        selection-color: {COLORS["text_primary"]};
        outline: none;
    }}
    
    QTableWidget::item {{
        padding: 6px 12px;
        border-bottom: 1px solid {COLORS["divider"]};
    }}
    
    QTableWidget::item:selected {{
        background-color: {COLORS["accent_light"]};
    }}
    
    QHeaderView {{
        background-color: {COLORS["bg_subtle"]};
    }}
    
    /* Horizontal header (column names) */
    QHeaderView::section {{
        background-color: {COLORS["bg_subtle"]};
        padding: 12px 12px;
        border: none;
        border-bottom: 2px solid {COLORS["brand_primary"]};
        border-right: 1px solid {COLORS["border_light"]};
        font-weight: 700;
        font-size: 11px;
        color: {COLORS["brand_dark"]};
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    QHeaderView::section:last {{
        border-right: none;
    }}
    
    /* Vertical header (row numbers) */
    QHeaderView::section:vertical {{
        background-color: {COLORS["bg_subtle"]};
        padding: 4px 8px;
        border: none;
        border-bottom: 1px solid {COLORS["border_light"]};
        border-right: 1px solid {COLORS["border"]};
        font-weight: 600;
        font-size: 11px;
        color: {COLORS["text_tertiary"]};
        min-height: 24px;
    }}

    /* Scrollbars - Subtle brand colored */
    QScrollBar:vertical {{
        background: {COLORS["bg_subtle"]};
        width: 10px;
        border-radius: 5px;
        margin: 2px;
    }}
    
    QScrollBar::handle:vertical {{
        background: {COLORS["border"]};
        border-radius: 5px;
        min-height: 30px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background: {COLORS["brand_primary"]};
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QScrollBar:horizontal {{
        background: {COLORS["bg_subtle"]};
        height: 10px;
        border-radius: 5px;
        margin: 2px;
    }}
    
    QScrollBar::handle:horizontal {{
        background: {COLORS["border"]};
        border-radius: 5px;
        min-width: 30px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background: {COLORS["brand_primary"]};
    }}

    /* ============================================
       INPUT FIELDS - Clean with brand focus
       ============================================ */
    QLineEdit {{
        background-color: {COLORS["bg_white"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 13px;
        color: {COLORS["text_primary"]};
        selection-background-color: {COLORS["accent_light"]};
    }}
    
    QLineEdit:focus {{
        border: 2px solid {COLORS["brand_primary"]};
        padding: 9px 13px;
    }}
    
    QLineEdit:disabled {{
        background-color: {COLORS["bg_subtle"]};
        color: {COLORS["text_tertiary"]};
    }}
    
    QLineEdit::placeholder {{
        color: {COLORS["text_tertiary"]};
    }}

    /* ============================================
       COMBOBOX - Dropdown with visible arrow
       ============================================ */
    QComboBox {{
        background-color: {COLORS["bg_white"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        padding: 8px 14px;
        padding-right: 30px;
        font-size: 13px;
        color: {COLORS["text_primary"]};
        min-width: 130px;
    }}
    
    QComboBox:hover {{
        border-color: {COLORS["brand_primary"]};
    }}
    
    QComboBox:focus {{
        border: 2px solid {COLORS["brand_primary"]};
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
        width: 0;
        height: 0;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {COLORS["text_secondary"]};
    }}
    
    QComboBox::down-arrow:hover {{
        border-top-color: {COLORS["brand_primary"]};
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {COLORS["bg_white"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        padding: 4px;
        selection-background-color: {COLORS["accent_light"]};
        selection-color: {COLORS["text_primary"]};
        outline: none;
    }}
    
    QComboBox QAbstractItemView::item {{
        padding: 8px 12px;
        border-radius: 4px;
        min-height: 20px;
    }}
    
    QComboBox QAbstractItemView::item:hover {{
        background-color: {COLORS["bg_hover"]};
    }}

    /* ============================================
       FRAMES & CARDS
       ============================================ */
    QFrame {{
        background-color: {COLORS["bg_main"]};
    }}
    
    QFrame#top_control_frame {{
        background-color: {COLORS["bg_subtle"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 10px;
    }}

    /* ============================================
       PROGRESS BAR - Brand gradient
       ============================================ */
    QProgressBar {{
        border: none;
        background-color: {COLORS["border_light"]};
        border-radius: 6px;
        height: 10px;
        text-align: center;
    }}
    
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLORS["brand_dark"]},
            stop:0.5 {COLORS["brand_primary"]},
            stop:1 {COLORS["brand_light"]});
        border-radius: 6px;
    }}

    /* ============================================
       LABELS
       ============================================ */
    QLabel {{
        color: {COLORS["text_primary"]};
        background: transparent;
    }}
    
    QLabel#header_label {{
        font-size: 18px;
        font-weight: 700;
        color: {COLORS["brand_dark"]};
    }}
    
    QLabel#subtitle_label {{
        font-size: 13px;
        color: {COLORS["text_secondary"]};
    }}
    
    QLabel#brand_label {{
        color: {COLORS["brand_primary"]};
        font-weight: 600;
    }}

    /* ============================================
       STATUS BAR
       ============================================ */
    QStatusBar {{
        background-color: {COLORS["bg_main"]};
        color: {COLORS["text_secondary"]};
        border-top: 1px solid {COLORS["border"]};
    }}

    /* ============================================
       TOOLBAR
       ============================================ */
    QToolBar {{
        background-color: {COLORS["bg_main"]};
        border: none;
        border-bottom: 1px solid {COLORS["border"]};
        padding: 8px 12px;
        spacing: 8px;
    }}

    /* ============================================
       MENU BAR
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
        background-color: {COLORS["accent_light"]};
        color: {COLORS["brand_primary"]};
    }}

    /* ============================================
       MENU (Dropdown)
       ============================================ */
    QMenu {{
        background-color: {COLORS["bg_white"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        padding: 6px;
    }}
    
    QMenu::item {{
        padding: 8px 24px 8px 12px;
        border-radius: 4px;
    }}
    
    QMenu::item:selected {{
        background-color: {COLORS["accent_light"]};
        color: {COLORS["brand_primary"]};
    }}
    
    QMenu::separator {{
        height: 1px;
        background-color: {COLORS["border"]};
        margin: 6px 8px;
    }}

    /* ============================================
       MESSAGE BOX
       ============================================ */
    QMessageBox {{
        background-color: {COLORS["bg_white"]};
    }}
    
    QMessageBox QLabel {{
        color: {COLORS["text_primary"]};
    }}
    
    QMessageBox QPushButton {{
        min-width: 80px;
    }}

    /* ============================================
       TOOLTIPS
       ============================================ */
    QToolTip {{
        background-color: {COLORS["brand_dark"]};
        color: {COLORS["text_inverse"]};
        border: none;
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 12px;
    }}
"""

# --- STYLE HELPERS ---

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


# --- APP METADATA ---
APP_NAME = "MyOffer Monitor"
APP_VERSION = "1.0.0"
APP_THEME = "Branded Light"
