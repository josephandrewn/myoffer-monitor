# styles.py
# MyOffer Monitor - Minimal Professional Theme
# Clean, refined, with subtle depth and quality typography

# --- COLOR PALETTE ---
# Refined neutrals with a sophisticated accent
COLORS = {
    # Backgrounds - Warm grays for a softer feel
    "bg_main": "#F8F9FA",           # Soft off-white
    "bg_white": "#FFFFFF",          # Pure white for cards
    "bg_elevated": "#FFFFFF",       # Elevated surfaces
    "bg_subtle": "#F1F3F4",         # Subtle differentiation
    
    # Text - High contrast, readable
    "text_primary": "#202124",      # Near black, warm
    "text_secondary": "#5F6368",    # Medium gray
    "text_tertiary": "#9AA0A6",     # Light gray
    "text_inverse": "#FFFFFF",      # White text
    
    # Borders & Dividers
    "border": "#DADCE0",            # Soft border
    "border_light": "#E8EAED",      # Very subtle
    "divider": "#EEEEEE",           # Table lines
    
    # Brand Accent - Deep teal/cyan for sophistication
    "accent": "#0D9488",            # Teal - professional but distinctive
    "accent_hover": "#0F766E",      # Darker teal
    "accent_light": "#CCFBF1",      # Light teal for highlights
    "accent_subtle": "#F0FDFA",     # Very light teal
    
    # Semantic Colors - Refined, not harsh
    "success": "#059669",           # Emerald green
    "success_hover": "#047857",
    "success_light": "#D1FAE5",
    
    "warning": "#D97706",           # Amber
    "warning_hover": "#B45309",
    "warning_light": "#FEF3C7",
    
    "danger": "#DC2626",            # Red
    "danger_hover": "#B91C1C",
    "danger_light": "#FEE2E2",
    
    "info": "#0284C7",              # Sky blue
    "info_light": "#E0F2FE",
    
    # Row Status Colors - Softer, more refined pastels
    "row_pass_bg": "#ECFDF5",       # Light emerald
    "row_pass_text": "#065F46",     # Dark emerald
    
    "row_fail_bg": "#FEF2F2",       # Light red
    "row_fail_text": "#991B1B",     # Dark red
    
    "row_warn_bg": "#FFFBEB",       # Light amber
    "row_warn_text": "#92400E",     # Dark amber
    
    "row_pending_bg": "#FFFFFF",    # White
    "row_pending_text": "#374151",  # Dark gray
    
    "row_blocked_bg": "#F3F4F6",    # Light gray
    "row_blocked_text": "#4B5563",  # Medium gray
    
    "row_unverifiable_bg": "#FFF7ED",  # Light orange
    "row_unverifiable_text": "#9A3412", # Dark orange
    
    "row_inactive_bg": "#F9FAFB",   # Very light gray
    "row_inactive_text": "#9CA3AF", # Muted text
    
    # Shadows (for reference in code)
    "shadow_sm": "0 1px 2px rgba(0,0,0,0.05)",
    "shadow_md": "0 4px 6px rgba(0,0,0,0.07)",
}

# --- GLOBAL STYLESHEET ---
MODERN_STYLESHEET = f"""
    /* ============================================
       GLOBAL STYLES
       ============================================ */
    QMainWindow {{
        background-color: {COLORS["bg_main"]};
    }}
    
    QWidget {{
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        font-size: 13px;
        color: {COLORS["text_primary"]};
    }}

    /* ============================================
       TAB WIDGET - Clean card-style tabs
       ============================================ */
    QTabWidget::pane {{
        background: {COLORS["bg_white"]};
        border: 1px solid {COLORS["border_light"]};
        border-radius: 12px;
        top: -1px;
        padding: 4px;
    }}
    
    QTabBar {{
        qproperty-drawBase: 0;
    }}
    
    QTabBar::tab {{
        background: transparent;
        border: none;
        padding: 12px 24px;
        margin-right: 4px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 13px;
        color: {COLORS["text_secondary"]};
        min-width: 100px;
    }}
    
    QTabBar::tab:selected {{
        background: {COLORS["accent"]};
        color: {COLORS["text_inverse"]};
    }}
    
    QTabBar::tab:!selected:hover {{
        background: {COLORS["bg_subtle"]};
        color: {COLORS["text_primary"]};
    }}

    /* ============================================
       BUTTONS - Refined with subtle depth
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
        background-color: {COLORS["bg_subtle"]};
        border-color: {COLORS["border"]};
    }}
    
    QPushButton:pressed {{
        background-color: {COLORS["border_light"]};
    }}
    
    QPushButton:disabled {{
        color: {COLORS["text_tertiary"]};
        background-color: {COLORS["bg_subtle"]};
        border-color: {COLORS["border_light"]};
    }}
    
    /* Primary Button - Accent color */
    QPushButton#btn_primary {{
        background-color: {COLORS["accent"]};
        color: {COLORS["text_inverse"]};
        border: none;
        padding: 8px 20px;
    }}
    QPushButton#btn_primary:hover {{
        background-color: {COLORS["accent_hover"]};
    }}
    QPushButton#btn_primary:pressed {{
        background-color: #0E7C71;
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

    /* ============================================
       TABLE - Clean data presentation
       ============================================ */
    QTableWidget {{
        background-color: {COLORS["bg_white"]};
        border: 1px solid {COLORS["border_light"]};
        border-radius: 10px;
        gridline-color: {COLORS["divider"]};
        selection-background-color: {COLORS["accent_light"]};
        selection-color: {COLORS["text_primary"]};
        outline: none;
    }}
    
    QTableWidget::item {{
        padding: 8px 12px;
        border-bottom: 1px solid {COLORS["divider"]};
    }}
    
    QTableWidget::item:selected {{
        background-color: {COLORS["accent_light"]};
        color: {COLORS["text_primary"]};
    }}
    
    QHeaderView {{
        background-color: transparent;
    }}
    
    QHeaderView::section {{
        background-color: {COLORS["bg_subtle"]};
        padding: 12px 12px;
        border: none;
        border-bottom: 2px solid {COLORS["border"]};
        font-weight: 700;
        font-size: 11px;
        color: {COLORS["text_secondary"]};
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    QHeaderView::section:first {{
        border-top-left-radius: 10px;
    }}
    
    QHeaderView::section:last {{
        border-top-right-radius: 10px;
    }}

    /* Scrollbar styling */
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
        background: {COLORS["text_tertiary"]};
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

    /* ============================================
       INPUT FIELDS - Clean with focus states
       ============================================ */
    QLineEdit {{
        background-color: {COLORS["bg_white"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 13px;
        selection-background-color: {COLORS["accent_light"]};
    }}
    
    QLineEdit:focus {{
        border: 2px solid {COLORS["accent"]};
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
       COMBOBOX - Dropdown styling
       ============================================ */
    QComboBox {{
        background-color: {COLORS["bg_white"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        padding: 8px 14px;
        padding-right: 30px;
        font-size: 13px;
        min-width: 120px;
    }}
    
    QComboBox:focus {{
        border: 2px solid {COLORS["accent"]};
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 30px;
    }}
    
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {COLORS["text_secondary"]};
        margin-right: 10px;
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
    }}
    
    QComboBox QAbstractItemView::item:hover {{
        background-color: {COLORS["bg_subtle"]};
    }}

    /* ============================================
       FRAMES & CARDS
       ============================================ */
    QFrame#top_control_frame {{
        background-color: {COLORS["bg_white"]};
        border: 1px solid {COLORS["border_light"]};
        border-radius: 12px;
    }}

    /* ============================================
       PROGRESS BAR - Sleek and modern
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
            stop:0 {COLORS["accent"]},
            stop:1 {COLORS["success"]});
        border-radius: 6px;
    }}

    /* ============================================
       LABELS
       ============================================ */
    QLabel {{
        color: {COLORS["text_primary"]};
    }}
    
    QLabel#header_label {{
        font-size: 18px;
        font-weight: 700;
        color: {COLORS["text_primary"]};
    }}
    
    QLabel#subtitle_label {{
        font-size: 13px;
        color: {COLORS["text_secondary"]};
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
       TOOLTIPS
       ============================================ */
    QToolTip {{
        background-color: {COLORS["text_primary"]};
        color: {COLORS["text_inverse"]};
        border: none;
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 12px;
    }}
"""

# --- ADDITIONAL STYLE HELPERS ---
# For programmatic styling in Python code

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
