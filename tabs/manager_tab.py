import sys
import pandas as pd
import qtawesome as qta 
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QMessageBox, QFileDialog, QLineEdit, QAbstractItemView, 
                             QFrame, QComboBox, QLabel, QDialog, QTextEdit,
                             QDialogButtonBox, QScrollArea, QGridLayout, QSizePolicy,
                             QSpacerItem, QApplication)
from PyQt6.QtGui import (QColor, QFont, QUndoStack, QUndoCommand, QCursor)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer

import assets.styles as styles 

from config import DEFAULT_COLUMNS, app_settings
try:
    from config import ENABLE_DATABASE
except ImportError:
    ENABLE_DATABASE = False
from logger import get_logger
from database import get_database
import harvester

logger = get_logger(__name__)


# ============================================================================
# HELPER: Trim URL for display
# ============================================================================

def trim_url_for_display(url: str) -> str:
    """Strip protocol and www. for card display. Full URL preserved in data."""
    display = url.strip()
    for prefix in ["https://www.", "http://www.", "https://", "http://"]:
        if display.lower().startswith(prefix):
            display = display[len(prefix):]
            break
    return display.rstrip("/")


# ============================================================================
# STATUS BADGE STYLES
# ============================================================================

def get_badge_style(status: str) -> str:
    """Return QSS for a status badge label based on status text."""
    status_upper = status.upper().strip() if status else ""
    
    color_map = {
        "PASS": (styles.COLORS["row_pass_bg"], styles.COLORS["row_pass_text"]),
        "FAIL": (styles.COLORS["row_fail_bg"], styles.COLORS["row_fail_text"]),
        "ERROR": (styles.COLORS["row_fail_bg"], styles.COLORS["row_fail_text"]),
        "WARN": (styles.COLORS["row_warn_bg"], styles.COLORS["row_warn_text"]),
        "BLOCKED": (styles.COLORS["row_warn_bg"], styles.COLORS["row_warn_text"]),
        "UNVERIFIABLE": (styles.COLORS["row_unverifiable_bg"], styles.COLORS["row_unverifiable_text"]),
        "N/A": (styles.COLORS["row_unverifiable_bg"], styles.COLORS["row_unverifiable_text"]),
        "PENDING": (styles.COLORS["row_pending_bg"], styles.COLORS["row_pending_text"]),
    }
    
    bg, fg = color_map.get(status_upper, (styles.COLORS["row_pending_bg"], styles.COLORS["row_pending_text"]))
    
    return f"""
        background-color: {bg};
        color: {fg};
        font-weight: 700;
        font-size: 10px;
        padding: 3px 10px;
        border-radius: 10px;
        border: 1px solid {fg}40;
    """


def get_card_border_color(status: str) -> str:
    """Return a left-border accent color for a card based on status."""
    status_upper = status.upper().strip() if status else ""
    border_map = {
        "PASS": styles.COLORS["success"],
        "FAIL": styles.COLORS["danger"],
        "ERROR": styles.COLORS["danger"],
        "WARN": styles.COLORS["warning"],
        "BLOCKED": styles.COLORS["warning"],
        "UNVERIFIABLE": "#D97706",
        "N/A": "#D97706",
        "PENDING": styles.COLORS["border"],
    }
    return border_map.get(status_upper, styles.COLORS["border"])


# ============================================================================
# CLIENT CARD WIDGET
# ============================================================================

class ClientCard(QFrame):
    """
    A clickable card representing one client row.
    Shows: Client Name, Status Badge, Trimmed URL.
    Clicking opens the detail editor dialog.
    """
    clicked = pyqtSignal(int)  # Emits the row index
    
    def __init__(self, row_index: int, client_name: str, url: str, status: str, 
                 is_active: bool = True, parent=None):
        super().__init__(parent)
        self.row_index = row_index
        self._is_active = is_active
        self._status = status
        self._selected = False
        
        self.setObjectName("client_card")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(88)
        self.setMinimumWidth(280)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Card internal layout
        card_layout = QVBoxLayout(self)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(4)
        
        # Top row: Name + Status Badge
        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        
        self.name_label = QLabel(client_name)
        self.name_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self.name_label.setStyleSheet(f"color: {styles.COLORS['text_primary']}; background: transparent;")
        self.name_label.setWordWrap(False)
        
        # Display text for status
        display_status = "N/A" if status.upper() in ["UNVERIFIABLE", "N/A"] else status
        self.status_badge = QLabel(display_status)
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.setFixedHeight(22)
        self.status_badge.setMinimumWidth(60)
        self.status_badge.setMaximumWidth(110)
        self.status_badge.setStyleSheet(get_badge_style(status))
        
        top_row.addWidget(self.name_label, 1)
        top_row.addWidget(self.status_badge, 0)
        
        card_layout.addLayout(top_row)
        
        # URL row
        display_url = trim_url_for_display(url)
        self.url_label = QLabel(display_url)
        self.url_label.setFont(QFont("Arial", 11))
        self.url_label.setStyleSheet(f"color: {styles.COLORS['text_tertiary']}; background: transparent;")
        self.url_label.setWordWrap(False)
        
        card_layout.addWidget(self.url_label)
        card_layout.addStretch()
        
        # Apply styling
        self._apply_style()
    
    def _apply_style(self):
        """Apply card styling based on status and active state."""
        border_color = get_card_border_color(self._status)
        
        if not self._is_active:
            self.setStyleSheet(f"""
                QFrame#client_card {{
                    background-color: {styles.COLORS['row_inactive_bg']};
                    border: 1px solid {styles.COLORS['border_light']};
                    border-left: 4px solid {styles.COLORS['text_tertiary']};
                    border-radius: 8px;
                    border-top-left-radius: 0;
                    border-bottom-left-radius: 0;
                }}
                QFrame#client_card:hover {{
                    border-color: {styles.COLORS['border']};
                    background-color: {styles.COLORS['bg_subtle']};
                }}
            """)
            self.name_label.setStyleSheet(f"color: {styles.COLORS['row_inactive_text']}; background: transparent;")
            self.url_label.setStyleSheet(f"color: {styles.COLORS['row_inactive_text']}; background: transparent;")
        else:
            selected_extra = f"border: 2px solid {styles.COLORS['brand_primary']};" if self._selected else f"border: 1px solid {styles.COLORS['border_light']};"
            self.setStyleSheet(f"""
                QFrame#client_card {{
                    background-color: {styles.COLORS['bg_white']};
                    {selected_extra}
                    border-left: 4px solid {border_color};
                    border-radius: 8px;
                    border-top-left-radius: 0;
                    border-bottom-left-radius: 0;
                }}
                QFrame#client_card:hover {{
                    background-color: {styles.COLORS['bg_hover']};
                    border-color: {styles.COLORS['brand_primary']};
                    border-left: 4px solid {border_color};
                }}
            """)
            self.name_label.setStyleSheet(f"color: {styles.COLORS['text_primary']}; background: transparent;")
            self.url_label.setStyleSheet(f"color: {styles.COLORS['text_tertiary']}; background: transparent;")
    
    def set_selected(self, selected: bool):
        """Highlight card as selected."""
        self._selected = selected
        self._apply_style()
    
    def update_data(self, client_name: str, url: str, status: str, is_active: bool):
        """Update displayed data without rebuilding the widget."""
        self._status = status
        self._is_active = is_active
        self.name_label.setText(client_name)
        display_status = "N/A" if status.upper() in ["UNVERIFIABLE", "N/A"] else status
        self.status_badge.setText(display_status)
        self.status_badge.setStyleSheet(get_badge_style(status))
        self.url_label.setText(trim_url_for_display(url))
        self._apply_style()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.row_index)
        super().mousePressEvent(event)


# ============================================================================
# DETAIL EDITOR DIALOG  
# ============================================================================

class ClientDetailDialog(QDialog):
    """
    Modal dialog showing all fields for a client record.
    Editable fields: Client Name, URL, Expected Provider, Offer, Active.
    Read-only fields: Detected Provider, Config, Status, Details, Site Map.
    """
    
    # List of known providers for dropdown
    PROVIDER_OPTIONS = ["", "DealerOn", "Dealer.com", "Dealer Inspire", "DealerSocket", "Sokal", "Other"]
    
    def __init__(self, parent, row_data: dict, row_index: int):
        super().__init__(parent)
        self.row_data = row_data.copy()
        self.row_index = row_index
        self.result_data = None  # Will hold edited data on accept
        
        client_name = row_data.get("Client Name", "Client")
        self.setWindowTitle(f"Client Details: {client_name}")
        self.setMinimumWidth(520)
        self.setMinimumHeight(500)
        self.resize(560, 580)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(16)
        
        # --- Header ---
        header = QLabel(client_name)
        header.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {styles.COLORS['brand_dark']}; background: transparent;")
        layout.addWidget(header)
        
        # Status + Config line
        status = row_data.get("Status", "PENDING")
        config = row_data.get("Config", "")
        status_line = QHBoxLayout()
        
        display_status = "N/A" if status.upper() in ["UNVERIFIABLE", "N/A"] else status
        status_badge = QLabel(f"  {display_status}  ")
        status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_badge.setFixedHeight(26)
        status_badge.setStyleSheet(get_badge_style(status))
        status_line.addWidget(status_badge)
        
        if config:
            config_label = QLabel(f"Config: {config}")
            config_label.setStyleSheet(f"color: {styles.COLORS['text_secondary']}; background: transparent; font-weight: 600;")
            status_line.addWidget(config_label)
        
        status_line.addStretch()
        
        # Active toggle
        is_active = row_data.get("Active", "Yes") == "Yes"
        active_label = QLabel("● Active" if is_active else "○ Archived")
        active_color = styles.COLORS["success"] if is_active else styles.COLORS["text_tertiary"]
        active_label.setStyleSheet(f"color: {active_color}; background: transparent; font-weight: 600;")
        status_line.addWidget(active_label)
        
        layout.addLayout(status_line)
        
        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {styles.COLORS['border']}; max-height: 1px;")
        layout.addWidget(sep)
        
        # --- Scrollable Form Area ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: transparent; }}")
        
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(0, 8, 0, 8)
        form_layout.setSpacing(14)
        
        # Editable fields
        self.fields = {}
        
        # Client Name
        self.fields["Client Name"] = self._add_field(form_layout, "Client Name", 
            row_data.get("Client Name", ""), editable=True)
        
        # URL
        self.fields["URL"] = self._add_field(form_layout, "URL", 
            row_data.get("URL", ""), editable=True)
        
        # Expected Provider (dropdown)
        provider_layout = QVBoxLayout()
        provider_label = QLabel("Expected Provider")
        provider_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        provider_label.setStyleSheet(f"color: {styles.COLORS['text_secondary']}; background: transparent;")
        provider_layout.addWidget(provider_label)
        
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(self.PROVIDER_OPTIONS)
        current_provider = row_data.get("Expected Provider", "")
        idx = self.provider_combo.findText(current_provider)
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)
        else:
            self.provider_combo.setCurrentText(current_provider)
        provider_layout.addWidget(self.provider_combo)
        form_layout.addLayout(provider_layout)
        
        # Read-only fields
        self._add_field(form_layout, "Detected Provider", 
            row_data.get("Detected Provider", ""), editable=False)
        
        self._add_field(form_layout, "Config", 
            row_data.get("Config", ""), editable=False)
        
        self._add_field(form_layout, "Status", 
            row_data.get("Status", "PENDING"), editable=False)
        
        self._add_field(form_layout, "Details", 
            row_data.get("Details", ""), editable=False)
        
        # Offer (editable)
        self.fields["Offer"] = self._add_field(form_layout, "Offer", 
            row_data.get("Offer", ""), editable=True)
        
        # Site Map info (read-only)
        site_map_val = row_data.get("Site Map", "")
        self._add_field(form_layout, "Site Map", 
            site_map_val if site_map_val else "Not harvested", editable=False)
        
        # Active toggle
        active_layout = QVBoxLayout()
        active_label_field = QLabel("Active Status")
        active_label_field.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        active_label_field.setStyleSheet(f"color: {styles.COLORS['text_secondary']}; background: transparent;")
        active_layout.addWidget(active_label_field)
        
        self.active_combo = QComboBox()
        self.active_combo.addItems(["Yes", "No"])
        self.active_combo.setCurrentText(row_data.get("Active", "Yes"))
        active_layout.addWidget(self.active_combo)
        form_layout.addLayout(active_layout)
        
        form_layout.addStretch()
        scroll.setWidget(form_widget)
        layout.addWidget(scroll)
        
        # --- Button Row ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        # View Site Map button
        self.btn_view_sitemap = QPushButton(" View Site Map")
        self.btn_view_sitemap.setIcon(qta.icon('fa5s.sitemap', color='#555'))
        self.btn_view_sitemap.clicked.connect(self._view_site_map)
        btn_layout.addWidget(self.btn_view_sitemap)
        
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton(" Save Changes")
        save_btn.setObjectName("btn_primary")
        save_btn.setIcon(qta.icon('fa5s.check', color='white'))
        save_btn.clicked.connect(self._save_and_accept)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _add_field(self, parent_layout, label_text: str, value: str, editable: bool = True):
        """Add a labeled field to the form. Returns the QLineEdit if editable."""
        field_layout = QVBoxLayout()
        field_layout.setSpacing(4)
        
        label = QLabel(label_text)
        label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        label.setStyleSheet(f"color: {styles.COLORS['text_secondary']}; background: transparent;")
        field_layout.addWidget(label)
        
        if editable:
            line_edit = QLineEdit(value)
            field_layout.addWidget(line_edit)
            parent_layout.addLayout(field_layout)
            return line_edit
        else:
            val_label = QLabel(value if value else "—")
            val_label.setStyleSheet(f"color: {styles.COLORS['text_primary']}; background: transparent; padding: 6px 0;")
            val_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            val_label.setWordWrap(True)
            field_layout.addWidget(val_label)
            parent_layout.addLayout(field_layout)
            return None
    
    def _view_site_map(self):
        """Open the site map dialog for this client."""
        url = self.row_data.get("URL", "")
        if not url:
            QMessageBox.warning(self, "No URL", "This client has no URL.")
            return
        
        client_name = self.row_data.get("Client Name", "Unknown")
        provider = self.row_data.get("Expected Provider", "")
        
        check_url = url if url.startswith("http") else f"https://{url}"
        site_map = harvester.get_site_map_summary(check_url)
        
        dialog = SiteMapDialog(self, client_name, url, provider, site_map)
        dialog.exec()
    
    def _save_and_accept(self):
        """Collect edited values and close dialog."""
        self.result_data = self.row_data.copy()
        
        # Update editable fields
        if self.fields.get("Client Name"):
            self.result_data["Client Name"] = self.fields["Client Name"].text()
        if self.fields.get("URL"):
            self.result_data["URL"] = self.fields["URL"].text()
        if self.fields.get("Offer"):
            self.result_data["Offer"] = self.fields["Offer"].text()
        
        self.result_data["Expected Provider"] = self.provider_combo.currentText()
        self.result_data["Active"] = self.active_combo.currentText()
        
        self.accept()


# ============================================================================
# FLOW LAYOUT (cards wrap to fill available width)
# ============================================================================

class FlowLayout(QVBoxLayout):
    """
    A simple layout that arranges cards in a responsive grid.
    Uses QGridLayout internally but recalculates columns on resize.
    """
    pass  # We'll use a simpler approach with QGridLayout + manual column management


# ============================================================================
# UNDO COMMANDS (adapted from table-based to data-based)
# ============================================================================

class CommandEditClient(QUndoCommand):
    """Undo command for editing a client's data via the detail dialog."""
    def __init__(self, manager, row_index: int, old_data: dict, new_data: dict):
        super().__init__(f"Edit Client {row_index}")
        self.manager = manager
        self.row_index = row_index
        self.old_data = old_data
        self.new_data = new_data
    
    def redo(self):
        self.manager._apply_row_data(self.row_index, self.new_data)
    
    def undo(self):
        self.manager._apply_row_data(self.row_index, self.old_data)


class CommandToggleActive(QUndoCommand):
    def __init__(self, manager, row_indices):
        super().__init__("Toggle Active Status")
        self.manager = manager
        self.row_indices = row_indices
        self.previous_states = {}
    
    def redo(self):
        for row in self.row_indices:
            current = self.manager._get_row_field(row, "Active")
            self.previous_states[row] = current
            new_val = "No" if current == "Yes" else "Yes"
            self.manager._set_row_field(row, "Active", new_val)
        self.manager.refresh_cards()
        self.manager.emit_change()
    
    def undo(self):
        for row, old_val in self.previous_states.items():
            self.manager._set_row_field(row, "Active", old_val)
        self.manager.refresh_cards()
        self.manager.emit_change()


class CommandAddRow(QUndoCommand):
    def __init__(self, manager, row_idx):
        super().__init__("Add Row")
        self.manager = manager
        self.row_idx = row_idx
    
    def redo(self):
        new_row = {col: "" for col in self.manager.columns}
        new_row["Client Name"] = "New Client"
        new_row["URL"] = "https://"
        new_row["Status"] = "PENDING"
        new_row["Active"] = "Yes"
        self.manager._data.insert(self.row_idx, new_row)
        self.manager.refresh_cards()
        self.manager.emit_change()
    
    def undo(self):
        if self.row_idx < len(self.manager._data):
            self.manager._data.pop(self.row_idx)
        self.manager.refresh_cards()
        self.manager.emit_change()


class CommandDeleteRow(QUndoCommand):
    def __init__(self, manager, row_idx, row_data):
        super().__init__("Delete Row")
        self.manager = manager
        self.row_idx = row_idx
        self.row_data = row_data
    
    def redo(self):
        if self.row_idx < len(self.manager._data):
            self.manager._data.pop(self.row_idx)
        self.manager.refresh_cards()
        self.manager.emit_change()
    
    def undo(self):
        self.manager._data.insert(self.row_idx, self.row_data.copy())
        self.manager.refresh_cards()
        self.manager.emit_change()


class CommandResetStatus(QUndoCommand):
    def __init__(self, manager, row_indices):
        super().__init__("Reset Status")
        self.manager = manager
        self.row_indices = row_indices
        self.previous_data = {}
    
    def redo(self):
        for row in self.row_indices:
            self.previous_data[row] = {
                "Config": self.manager._get_row_field(row, "Config"),
                "Status": self.manager._get_row_field(row, "Status"),
                "Details": self.manager._get_row_field(row, "Details"),
                "Active": self.manager._get_row_field(row, "Active"),
            }
            self.manager._set_row_field(row, "Config", "")
            self.manager._set_row_field(row, "Status", "PENDING")
            self.manager._set_row_field(row, "Details", "")
            self.manager._set_row_field(row, "Active", "Yes")
        self.manager.refresh_cards()
        self.manager.emit_change()
    
    def undo(self):
        for row, fields in self.previous_data.items():
            for field, val in fields.items():
                self.manager._set_row_field(row, field, val)
        self.manager.refresh_cards()
        self.manager.emit_change()


# ============================================================================
# MAIN WIDGET - Card-Based Manager Tab
# ============================================================================

class ManagerTab(QWidget):
    data_modified = pyqtSignal()
    
    PROVIDER_OPTIONS = ["", "DealerOn", "Dealer.com", "Dealer Inspire", "DealerSocket", "Sokal", "Other"]
    
    CARDS_PER_ROW = 3  # Default; recalculated on resize
    
    def __init__(self):
        super().__init__()
        
        self.file_path = None
        self.columns = [
            "Client Name", "URL", "Expected Provider", "Detected Provider", 
            "Config", "Status", "Details", "Site Map", "Offer", "Active"
        ]
        self.df = pd.DataFrame(columns=self.columns)
        self.undo_stack = QUndoStack(self)
        
        # Internal data store (list of dicts, one per row)
        self._data = []
        
        # Card widget references
        self._cards = []
        self._selected_indices = set()
        
        # Hidden QTableWidget for compatibility with main.py's update_master_record
        # This is invisible but keeps the signal contract intact
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.hide()
        
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # --- Top Controls Frame ---
        top_frame = QFrame()
        top_frame.setObjectName("top_control_frame")
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(15, 15, 15, 15)
        top_layout.setSpacing(12)
        
        self.btn_load = QPushButton(" Load List")
        self.btn_load.setIcon(qta.icon('fa5s.folder-open', color='#555'))
        self.btn_load.clicked.connect(self.load_csv)
        
        self.btn_save = QPushButton(" Save Changes")
        self.btn_save.setObjectName("btn_success")
        self.btn_save.setIcon(qta.icon('fa5s.save', color='white'))
        self.btn_save.clicked.connect(self.save_csv)
        
        self.btn_undo = QPushButton(" Undo")
        self.btn_undo.setIcon(qta.icon('fa5s.undo-alt', color='#555'))
        self.btn_undo.clicked.connect(self.undo_stack.undo)
        self.btn_undo.setEnabled(False)
        self.undo_stack.canUndoChanged.connect(self.btn_undo.setEnabled)
        
        self.btn_import_offers = QPushButton(" Import Offers")
        self.btn_import_offers.setObjectName("btn_brand")
        self.btn_import_offers.setIcon(qta.icon('fa5s.file-import', color='white'))
        self.btn_import_offers.clicked.connect(self.import_offers)
        
        self.btn_sitemap = QPushButton(" View Site Map")
        self.btn_sitemap.setIcon(qta.icon('fa5s.sitemap', color='#555'))
        self.btn_sitemap.clicked.connect(self.view_site_map)
        
        self.btn_add = QPushButton(" Add Manual")
        self.btn_add.setIcon(qta.icon('fa5s.plus-circle', color='#555'))
        self.btn_add.clicked.connect(self.add_row)
        
        self.btn_reset = QPushButton(" Reset Status")
        self.btn_reset.setIcon(qta.icon('fa5s.sync-alt', color='#555'))
        self.btn_reset.clicked.connect(self.reset_status)
        
        self.btn_archive = QPushButton(" Archive")
        self.btn_archive.setIcon(qta.icon('fa5s.archive', color='#555'))
        self.btn_archive.clicked.connect(self.toggle_archive)
        
        self.btn_del = QPushButton(" Delete")
        self.btn_del.setObjectName("btn_danger")
        self.btn_del.setIcon(qta.icon('fa5s.trash-alt', color='white'))
        self.btn_del.clicked.connect(self.delete_row)
        
        self.undo_stack.indexChanged.connect(self.emit_change)
        
        top_layout.addWidget(self.btn_load)
        top_layout.addWidget(self.btn_save)
        top_layout.addWidget(self.btn_undo)
        top_layout.addWidget(self.btn_import_offers)
        top_layout.addWidget(self.btn_sitemap)
        top_layout.addStretch()
        top_layout.addWidget(self.btn_add)
        top_layout.addWidget(self.btn_reset)
        top_layout.addWidget(self.btn_archive)
        top_layout.addWidget(self.btn_del)
        layout.addWidget(top_frame)
        
        # --- Filter Bar ---
        filter_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Search Client or URL...")
        self.search_bar.textChanged.connect(self.filter_cards)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Statuses", "PENDING", "PASS", "FAIL", "WARN", "BLOCKED", "N/A", "ERROR", "ARCHIVED"])
        self.filter_combo.currentTextChanged.connect(self.filter_cards)
        
        arrow_label = QLabel("▼")
        arrow_label.setStyleSheet(f"color: {styles.COLORS['text_secondary']}; font-size: 10px; background: transparent; margin-left: -20px;")
        
        # Summary counts
        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet(f"color: {styles.COLORS['text_secondary']}; background: transparent; font-size: 12px;")
        
        filter_layout.addWidget(self.search_bar)
        filter_layout.addWidget(QLabel("Filter by:"))
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addWidget(arrow_label)
        filter_layout.addStretch()
        filter_layout.addWidget(self.summary_label)
        layout.addLayout(filter_layout)
        
        # --- Card Grid (inside scroll area) ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{ 
                border: 1px solid {styles.COLORS['border']}; 
                border-radius: 10px;
                background-color: {styles.COLORS['bg_main']}; 
            }}
        """)
        
        self.card_container = QWidget()
        self.card_container.setStyleSheet(f"background-color: {styles.COLORS['bg_main']};")
        self.card_grid = QGridLayout(self.card_container)
        self.card_grid.setContentsMargins(16, 16, 16, 16)
        self.card_grid.setSpacing(12)
        self.card_grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.card_container)
        layout.addWidget(self.scroll_area)
        
        # Hidden table for compatibility
        layout.addWidget(self.table)
    
    # ================================================================
    # DATA LAYER 
    # ================================================================
    
    def _get_row_field(self, row: int, field: str) -> str:
        if 0 <= row < len(self._data):
            return self._data[row].get(field, "")
        return ""
    
    def _set_row_field(self, row: int, field: str, value: str):
        if 0 <= row < len(self._data):
            self._data[row][field] = value
    
    def _apply_row_data(self, row: int, data: dict):
        """Apply a full data dict to a row. Used by undo commands."""
        if 0 <= row < len(self._data):
            self._data[row] = data.copy()
            self.refresh_cards()
            self._sync_hidden_table()
            self.emit_change()
    
    def _sync_hidden_table(self):
        """
        Sync internal _data to hidden QTableWidget so main.py's
        update_master_record can write to table items by index.
        """
        self.table.blockSignals(True)
        self.table.setRowCount(len(self._data))
        for r, row_data in enumerate(self._data):
            for c, col_name in enumerate(self.columns):
                val = row_data.get(col_name, "")
                item = self.table.item(r, c)
                if not item:
                    item = QTableWidgetItem(val)
                    self.table.setItem(r, c, item)
                else:
                    item.setText(val)
        self.table.blockSignals(False)
    
    def _read_hidden_table_to_data(self):
        """
        Read from hidden QTableWidget back into _data.
        Called after main.py's update_master_record writes to table items.
        """
        for r in range(self.table.rowCount()):
            if r < len(self._data):
                for c, col_name in enumerate(self.columns):
                    item = self.table.item(r, c)
                    if item:
                        self._data[r][col_name] = item.text()
    
    def get_dataframe(self):
        """Return current data as a pandas DataFrame. Contract method for main.py."""
        return pd.DataFrame(self._data, columns=self.columns) if self._data else pd.DataFrame(columns=self.columns)
    
    def emit_change(self):
        self.data_modified.emit()
    
    # ================================================================
    # CARD GRID MANAGEMENT
    # ================================================================
    
    def _calculate_columns(self) -> int:
        """Calculate how many card columns fit in the current width."""
        available_width = self.scroll_area.viewport().width() - 40  # margins
        card_min_width = 300
        cols = max(1, available_width // card_min_width)
        return min(cols, 5)  # cap at 5
    
    def refresh_cards(self):
        """Rebuild the card grid from _data, applying current filters."""
        # Clear existing cards
        for card in self._cards:
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()
        
        # Clear grid
        while self.card_grid.count():
            item = self.card_grid.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        cols = self._calculate_columns()
        search_text = self.search_bar.text().lower() if hasattr(self, 'search_bar') else ""
        status_filter = self.filter_combo.currentText() if hasattr(self, 'filter_combo') else "All Statuses"
        
        # Counters for summary
        total = len(self._data)
        visible = 0
        status_counts = {}
        
        grid_row = 0
        grid_col = 0
        
        for idx, row_data in enumerate(self._data):
            client_name = row_data.get("Client Name", "")
            url = row_data.get("URL", "")
            status = row_data.get("Status", "PENDING")
            active = row_data.get("Active", "Yes")
            
            # Count statuses
            s = status.upper().strip()
            status_counts[s] = status_counts.get(s, 0) + 1
            
            # Apply filters
            if not self._passes_filter(row_data, search_text, status_filter):
                continue
            
            visible += 1
            is_active = active == "Yes"
            
            card = ClientCard(idx, client_name, url, status, is_active, parent=self.card_container)
            card.clicked.connect(self._on_card_clicked)
            
            # Highlight if selected
            if idx in self._selected_indices:
                card.set_selected(True)
            
            self.card_grid.addWidget(card, grid_row, grid_col)
            self._cards.append(card)
            
            grid_col += 1
            if grid_col >= cols:
                grid_col = 0
                grid_row += 1
        
        # Add spacer at bottom
        spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.card_grid.addItem(spacer, grid_row + 1, 0, 1, cols)
        
        # Update summary
        pass_count = status_counts.get("PASS", 0)
        fail_count = status_counts.get("FAIL", 0) + status_counts.get("ERROR", 0)
        warn_count = status_counts.get("WARN", 0) + status_counts.get("BLOCKED", 0)
        pending_count = status_counts.get("PENDING", 0)
        
        if hasattr(self, 'summary_label'):
            parts = [f"{total} total"]
            if visible != total:
                parts.append(f"{visible} shown")
            if pass_count: parts.append(f"✓ {pass_count}")
            if fail_count: parts.append(f"✗ {fail_count}")
            if warn_count: parts.append(f"⚠ {warn_count}")
            if pending_count: parts.append(f"◯ {pending_count}")
            self.summary_label.setText("  |  ".join(parts))
        
        # Also sync hidden table
        self._sync_hidden_table()
    
    def _passes_filter(self, row_data: dict, search_text: str, status_filter: str) -> bool:
        """Check if a row passes current filter criteria."""
        client_name = row_data.get("Client Name", "").lower()
        url = row_data.get("URL", "").lower()
        status = row_data.get("Status", "").upper().strip()
        active = row_data.get("Active", "Yes")
        
        # Text search
        if search_text and search_text not in client_name and search_text not in url:
            return False
        
        # Status filter
        if status_filter == "ARCHIVED":
            return active == "No"
        elif status_filter == "N/A":
            return active == "Yes" and status in ["N/A", "UNVERIFIABLE"]
        elif status_filter != "All Statuses":
            return active == "Yes" and status == status_filter
        
        return True
    
    def filter_cards(self):
        """Re-filter cards based on current search/status."""
        self.refresh_cards()
    
    # Compatibility alias for main.py
    def filter_table(self):
        self.filter_cards()
    
    def _on_card_clicked(self, row_index: int):
        """Handle card click - toggle selection on shift/ctrl, else open detail."""
        modifiers = QApplication.keyboardModifiers()
        
        if modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            # Multi-select mode
            if row_index in self._selected_indices:
                self._selected_indices.discard(row_index)
            else:
                self._selected_indices.add(row_index)
            self.refresh_cards()
        else:
            # Open detail dialog
            self._selected_indices = {row_index}
            self.refresh_cards()
            self._open_detail_dialog(row_index)
    
    def _open_detail_dialog(self, row_index: int):
        """Open the detail editor for a client."""
        if row_index >= len(self._data):
            return
        
        row_data = self._data[row_index]
        dialog = ClientDetailDialog(self, row_data, row_index)
        
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            old_data = row_data.copy()
            new_data = dialog.result_data
            
            # Only push undo if something actually changed
            if old_data != new_data:
                command = CommandEditClient(self, row_index, old_data, new_data)
                self.undo_stack.push(command)
    
    # ================================================================
    # update_row_style - compatibility method for main.py
    # ================================================================
    
    def update_row_style(self, row):
        """
        Compatibility method. main.py calls this after writing to the hidden table.
        We read the updated data back and refresh the relevant card.
        """
        self._read_hidden_table_to_data()
        self.refresh_cards()
    
    # ================================================================
    # populate_table - called after CSV load or project restore
    # ================================================================
    
    def populate_table(self):
        """Populate cards from self.df (the pandas DataFrame)."""
        self._data = []
        
        for _, row in self.df.iterrows():
            row_dict = {}
            for col_name in self.columns:
                val = str(row[col_name]) if pd.notna(row.get(col_name, "")) else ""
                
                # Clean legacy status icons
                if col_name == "Status":
                    val = val.replace('📋', '').strip()
                
                # Check site map existence
                if col_name == "Site Map":
                    url = str(row.get('URL', '')) if pd.notna(row.get('URL', '')) else ""
                    check_url = url if url.startswith('http') else f"https://{url}"
                    val = "Yes" if url and harvester.has_site_map(check_url) else ""
                
                row_dict[col_name] = val
            
            self._data.append(row_dict)
        
        self._selected_indices.clear()
        self.refresh_cards()
    
    # ================================================================
    # TABLE OPERATIONS (toolbar actions)
    # ================================================================
    
    def add_row(self):
        row_idx = len(self._data)
        command = CommandAddRow(self, row_idx)
        self.undo_stack.push(command)
        
        # Scroll to bottom and open the new card's editor
        QTimer.singleShot(100, lambda: self._scroll_to_bottom_and_edit(row_idx))
    
    def _scroll_to_bottom_and_edit(self, row_idx):
        """Scroll to the bottom of the card area."""
        sb = self.scroll_area.verticalScrollBar()
        sb.setValue(sb.maximum())
    
    def delete_row(self):
        if not self._selected_indices:
            QMessageBox.information(self, "Select Cards", "Click a card to select it first, then delete.")
            return
        
        rows = sorted(self._selected_indices, reverse=True)
        self.undo_stack.beginMacro("Delete Rows")
        for row_idx in rows:
            if row_idx < len(self._data):
                row_data = self._data[row_idx].copy()
                command = CommandDeleteRow(self, row_idx, row_data)
                self.undo_stack.push(command)
        self.undo_stack.endMacro()
        self._selected_indices.clear()
    
    def toggle_archive(self):
        if not self._selected_indices:
            QMessageBox.information(self, "Select Cards", "Click a card to select it first (Ctrl+click for multiple).")
            return
        rows = sorted(self._selected_indices)
        command = CommandToggleActive(self, rows)
        self.undo_stack.push(command)
    
    def reset_status(self):
        if not self._selected_indices:
            QMessageBox.information(self, "Select Cards", "Click a card to select it first (Ctrl+click for multiple).")
            return
        rows = sorted(self._selected_indices)
        command = CommandResetStatus(self, rows)
        self.undo_stack.push(command)
    
    def save_csv(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        default_name = f"sites_{timestamp}.csv"
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Snapshot", default_name, "CSV Files (*.csv)")
        
        if not file_path:
            return
        
        new_df = self.get_dataframe()
        try:
            new_df.to_csv(file_path, index=False)
            QMessageBox.information(self, "Saved", f"Snapshot saved successfully!\n{file_path}")
            self.undo_stack.setClean()
            self.file_path = file_path
            self.sync_to_database()
        except Exception as e:
            QMessageBox.critical(self, "Error Saving", str(e))
    
    def load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if path:
            self.file_path = path
            try:
                self.df = pd.read_csv(path)
                
                # Handle legacy "Provider" column
                if "Provider" in self.df.columns and "Expected Provider" not in self.df.columns:
                    self.df = self.df.rename(columns={"Provider": "Expected Provider"})
                    logger.info("Mapped legacy 'Provider' column to 'Expected Provider'")
                
                if "Provider" in self.df.columns and "Expected Provider" in self.df.columns:
                    mask = (self.df["Expected Provider"].isna() | (self.df["Expected Provider"] == "")) & \
                           (self.df["Provider"].notna() & (self.df["Provider"] != ""))
                    self.df.loc[mask, "Expected Provider"] = self.df.loc[mask, "Provider"]
                    logger.info("Copied Provider data to empty Expected Provider fields")
                
                self.df = self.df.reindex(columns=self.columns, fill_value="")
                self.df['Status'] = self.df['Status'].replace("", "PENDING").fillna('PENDING')
                self.df['Active'] = self.df['Active'].replace("", "Yes").fillna('Yes')
                
                self.undo_stack.clear()
                self.populate_table()
                self.emit_change()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
    
    def import_offers(self):
        """Import offers from a CSV file with Client Name and Offer columns."""
        path, _ = QFileDialog.getOpenFileName(self, "Import Offers CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        
        try:
            import_df = pd.read_csv(path)
            
            if 'Client Name' not in import_df.columns:
                QMessageBox.warning(self, "Invalid CSV", "CSV must contain a 'Client Name' column.")
                return
            if 'Offer' not in import_df.columns:
                QMessageBox.warning(self, "Invalid CSV", "CSV must contain an 'Offer' column.")
                return
            
            # Build lookup
            client_to_row = {}
            for idx, row_data in enumerate(self._data):
                client_name = row_data.get("Client Name", "").strip()
                client_to_row[client_name] = idx
            
            updated = 0
            not_found = []
            
            for _, import_row in import_df.iterrows():
                client_name = str(import_row['Client Name']).strip()
                offer_value = str(import_row['Offer']).strip() if pd.notna(import_row['Offer']) else ""
                
                if client_name in client_to_row:
                    row_idx = client_to_row[client_name]
                    self._data[row_idx]["Offer"] = offer_value
                    updated += 1
                else:
                    not_found.append(client_name)
            
            self.refresh_cards()
            self.emit_change()
            
            message = f"Updated {updated} offer(s)."
            if not_found:
                message += f"\n\n⚠️ {len(not_found)} client(s) not found:\n"
                for name in not_found[:10]:
                    message += f"  • {name}\n"
                if len(not_found) > 10:
                    message += f"  ... and {len(not_found) - 10} more"
            
            QMessageBox.information(self, "Import Complete", message)
            
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Error importing offers:\n{str(e)}")
    
    def view_site_map(self):
        """Show site map dialog for selected card."""
        if not self._selected_indices:
            QMessageBox.information(self, "No Selection", "Please click a card to select it first.")
            return
        
        row_idx = min(self._selected_indices)
        if row_idx >= len(self._data):
            return
        
        row_data = self._data[row_idx]
        client_name = row_data.get("Client Name", "Unknown")
        url = row_data.get("URL", "")
        provider = row_data.get("Expected Provider", "")
        
        if not url:
            QMessageBox.warning(self, "No URL", "Selected client has no URL.")
            return
        
        check_url = url if url.startswith("http") else f"https://{url}"
        site_map = harvester.get_site_map_summary(check_url)
        
        dialog = SiteMapDialog(self, client_name, url, provider, site_map)
        dialog.exec()
    
    def sync_to_database(self):
        """Sync current data to database."""
        if not ENABLE_DATABASE:
            return
        try:
            db = get_database()
            df = self.get_dataframe()
            db.from_dataframe(df, replace=True)
            logger.info("Data synced to database", records=len(df))
        except Exception as e:
            logger.error("Failed to sync to database", exception=e)
            QMessageBox.warning(self, "Database Sync Error", f"Could not sync to database: {str(e)}")
    
    # ================================================================
    # RESIZE HANDLING
    # ================================================================
    
    def resizeEvent(self, event):
        """Recalculate card columns on resize."""
        super().resizeEvent(event)
        # Debounce: only refresh if we have data
        if self._data:
            QTimer.singleShot(50, self.refresh_cards)


# ============================================================================
# SITE MAP DIALOG (unchanged from original)
# ============================================================================

class SiteMapDialog(QDialog):
    """Dialog for displaying site map data."""
    
    def __init__(self, parent, client_name: str, url: str, provider: str, site_map: dict = None):
        super().__init__(parent)
        self.url = url
        self.provider = provider
        
        self.setWindowTitle(f"Site Map: {client_name}")
        self.setMinimumSize(550, 600)
        self.resize(550, 700)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header_label = QLabel(f"<b style='font-size: 16px;'>{client_name}</b>")
        header_label.setStyleSheet("background: transparent;")
        layout.addWidget(header_label)
        
        # Metadata
        if site_map:
            harvested_at = site_map.get("harvested_at", "Unknown")
            if harvested_at and harvested_at != "Unknown":
                try:
                    dt = datetime.fromisoformat(harvested_at)
                    harvested_at = dt.strftime("%b %d, %Y at %I:%M %p")
                except:
                    pass
            detected_provider = site_map.get("provider", "Unknown")
            meta_text = f"Provider: {detected_provider} | Harvested: {harvested_at}"
        else:
            meta_text = "No site map data available"
        
        meta_label = QLabel(meta_text)
        meta_label.setStyleSheet(f"color: {styles.COLORS['text_secondary']}; background: transparent;")
        layout.addWidget(meta_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: {styles.COLORS['border']};")
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        
        # Content area (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background-color: {styles.COLORS['bg_white']}; }}")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(8)
        
        if site_map and site_map.get("links"):
            links = site_map.get("links", {})
            
            for category in harvester.CATEGORY_ORDER:
                urls = links.get(category, [])
                
                cat_label = QLabel(f"<b>{category}</b>")
                cat_label.setStyleSheet("background: transparent; margin-top: 8px;")
                content_layout.addWidget(cat_label)
                
                if urls:
                    for url_item in urls:
                        url_label = QLabel(url_item)
                        url_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                        url_label.setWordWrap(True)
                        url_label.setStyleSheet(f"color: {styles.COLORS['brand_primary']}; background: transparent; padding-left: 10px;")
                        content_layout.addWidget(url_label)
                else:
                    not_found = QLabel("Not found")
                    not_found.setStyleSheet(f"color: {styles.COLORS['text_tertiary']}; font-style: italic; background: transparent; padding-left: 10px;")
                    content_layout.addWidget(not_found)
            
            other = site_map.get("other", [])
            if other:
                sep2 = QFrame()
                sep2.setFrameShape(QFrame.Shape.HLine)
                sep2.setStyleSheet(f"background-color: {styles.COLORS['border']}; margin-top: 10px;")
                sep2.setFixedHeight(1)
                content_layout.addWidget(sep2)
                
                other_label = QLabel(f"<b>Other:</b> {', '.join(other[:15])}")
                other_label.setWordWrap(True)
                other_label.setStyleSheet(f"color: {styles.COLORS['text_secondary']}; background: transparent; margin-top: 5px;")
                content_layout.addWidget(other_label)
        else:
            no_data = QLabel(
                "No site map data has been harvested for this site yet.\n\n"
                "Site maps are automatically collected during scans,\n"
                "or you can use 'Check Site Map' in the Scanner tab."
            )
            no_data.setStyleSheet(f"color: {styles.COLORS['text_secondary']}; background: transparent; padding: 20px;")
            no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content_layout.addWidget(no_data)
        
        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_site_map)
        refresh_btn.setEnabled(False)
        refresh_btn.setToolTip("Refresh requires running from Scanner tab")
        button_layout.addWidget(refresh_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setObjectName("btn_primary")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def refresh_site_map(self):
        QMessageBox.information(
            self, "Refresh",
            "To refresh the site map, use 'Check Site Map' in the Scanner tab.\n"
            "This will re-harvest the navigation links from the website."
        )
