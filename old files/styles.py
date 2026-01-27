# styles.py

# --- COLOR PALETTE ---
# Modern, professional colors (Apple/Bootstrap inspired)
COLORS = {
    "bg_main": "#F5F5F7",       # Light Grey Background
    "bg_white": "#FFFFFF",      # Pure White for Cards
    "text_primary": "#1D1D1F",  # Near Black
    "text_secondary": "#86868B",# Dark Grey
    "border": "#D2D2D7",        # Light Border
    
    # Semantic Colors
    "accent": "#007AFF",        # Blue (Primary)
    "accent_hover": "#0051A8",
    "success": "#34C759",       # Green
    "success_hover": "#248A3D",
    "warning": "#FF9F0A",       # Orange
    "danger": "#FF3B30",        # Red
    "danger_hover": "#D70015",
    
    # Row Status Colors (Pastels for background, Dark for text)
    "row_pass_bg": "#d4edda",
    "row_pass_text": "#155724",
    "row_fail_bg": "#f8d7da",
    "row_fail_text": "#721c24",
    "row_warn_bg": "#fff3cd",
    "row_warn_text": "#856404",
    "row_pending_bg": "#ffffff",
    "row_pending_text": "#1d1d1f",
    "row_inactive_bg": "#f0f0f0",
    "row_inactive_text": "#86868b"
}

# --- GLOBAL STYLESHEET ---
MODERN_STYLESHEET = f"""
    QMainWindow {{
        background-color: {COLORS["bg_main"]};
    }}
    QWidget {{
        font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
        font-size: 13px;
        color: {COLORS["text_primary"]};
    }}

    /* --- TABS --- */
    QTabWidget::pane {{
        border: 1px solid {COLORS["border"]};
        background: {COLORS["bg_white"]};
        border-radius: 8px;
        top: -1px; 
    }}
    QTabBar::tab {{
        background: {COLORS["bg_main"]};
        border: 1px solid transparent;
        border-bottom: 1px solid {COLORS["border"]};
        padding: 10px 20px;
        margin-right: 4px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        font-weight: bold;
        color: {COLORS["text_secondary"]};
    }}
    QTabBar::tab:selected {{
        background: {COLORS["bg_white"]};
        color: {COLORS["accent"]};
        border: 1px solid {COLORS["border"]};
        border-bottom: 2px solid {COLORS["bg_white"]}; /* Blends with pane */
    }}
    QTabBar::tab:hover {{
        background: #E5E5EA;
    }}

    /* --- BUTTONS --- */
    QPushButton {{
        background-color: {COLORS["bg_white"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 6px;
        padding: 6px 14px;
        font-weight: 600;
        color: {COLORS["text_primary"]};
    }}
    QPushButton:hover {{
        background-color: #F2F2F7;
        border-color: #C6C6C6;
    }}
    QPushButton:pressed {{
        background-color: #E5E5EA;
    }}
    QPushButton:disabled {{
        color: #C7C7CC;
        background-color: #F2F2F7;
        border-color: #E5E5EA;
    }}
    
    /* ID-Based Styles for Semantic Buttons */
    QPushButton#btn_primary {{
        background-color: {COLORS["accent"]};
        color: white;
        border: none;
    }}
    QPushButton#btn_primary:hover {{ background-color: {COLORS["accent_hover"]}; }}
    
    QPushButton#btn_success {{
        background-color: {COLORS["success"]};
        color: white;
        border: none;
    }}
    QPushButton#btn_success:hover {{ background-color: {COLORS["success_hover"]}; }}

    QPushButton#btn_danger {{
        background-color: {COLORS["danger"]};
        color: white;
        border: none;
    }}
    QPushButton#btn_danger:hover {{ background-color: {COLORS["danger_hover"]}; }}

    /* --- TABLE --- */
    QTableWidget {{
        background-color: {COLORS["bg_white"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 8px;
        gridline-color: #F0F0F0;
        selection-background-color: {COLORS["accent"]}; /* Blue selection */
        selection-color: white;
    }}
    QHeaderView::section {{
        background-color: {COLORS["bg_main"]};
        padding: 8px;
        border: none;
        border-bottom: 1px solid {COLORS["border"]};
        font-weight: bold;
        color: {COLORS["text_secondary"]};
    }}
    QTableWidget::item {{
        padding: 4px;
    }}

    /* --- INPUTS --- */
    QLineEdit, QComboBox {{
        background-color: {COLORS["bg_white"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 6px;
        padding: 6px;
    }}
    QLineEdit:focus, QComboBox:focus {{
        border: 1px solid {COLORS["accent"]};
    }}

    /* --- FRAMES --- */
    QFrame#top_control_frame {{
        background-color: {COLORS["bg_white"]};
        border-bottom: 1px solid {COLORS["border"]};
        border-radius: 8px;
    }}
    
    /* --- PROGRESS BAR --- */
    QProgressBar {{
        border: none;
        background-color: #E5E5EA;
        border-radius: 4px;
        height: 8px;
        text-align: center;
    }}
    QProgressBar::chunk {{
        background-color: {COLORS["accent"]};
        border-radius: 4px;
    }}
"""