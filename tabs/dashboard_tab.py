# dashboard_tab.py
# MyOffer Monitor - Dashboard Tab
# Visual summary with status cards, recent changes, and provider breakdown

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QScrollArea, QPushButton, QDialog, QTextEdit, QApplication,
    QMessageBox, QGridLayout, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import qtawesome as qta
from datetime import datetime
from pathlib import Path
import json

import assets.styles as styles

# File to store status change history
HISTORY_FILE = Path("data") / "status_history.json"


class StatusCard(QFrame):
    """A styled card displaying a status count."""
    
    def __init__(self, title, icon_name, count=0, percentage=None, color_key="brand_primary"):
        super().__init__()
        self.color_key = color_key
        self.setObjectName("status_card")
        self.setMinimumSize(160, 140)
        self.setMaximumSize(200, 160)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icon and title row
        title_layout = QHBoxLayout()
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_label = QLabel()
        icon = qta.icon(icon_name, color=styles.COLORS[color_key])
        icon_label.setPixmap(icon.pixmap(20, 20))
        title_layout.addWidget(icon_label)
        
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.title_label.setStyleSheet(f"color: {styles.COLORS[color_key]};font-size: 16px;")
        title_layout.addWidget(self.title_label)
        
        layout.addLayout(title_layout)
        
        # Count - large prominent number
        self.count_label = QLabel(str(count))
        self.count_label.setFont(QFont("Arial", 48, QFont.Weight.Bold))
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_label.setStyleSheet(f"color: {styles.COLORS['text_primary']};font-size: 36px;")
        layout.addWidget(self.count_label)
        
        # Percentage (optional)
        self.percentage_label = QLabel("")
        self.percentage_label.setFont(QFont("Arial", 10))
        self.percentage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.percentage_label.setStyleSheet(f"color: {styles.COLORS['text_secondary']};")
        layout.addWidget(self.percentage_label)
        
        if percentage is not None:
            self.percentage_label.setText(f"({percentage:.1f}%)")
        
        self.apply_style()
    
    def apply_style(self):
        self.setStyleSheet(f"""
            QFrame#status_card {{
                background-color: {styles.COLORS['bg_white']};
                border: 1px solid {styles.COLORS['border']};
                border-radius: 12px;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                border-left: 4px solid {styles.COLORS[self.color_key]};
            }}
        """)
    
    def update_values(self, count, percentage=None):
        self.count_label.setText(str(count))
        if percentage is not None:
            self.percentage_label.setText(f"({percentage:.1f}%)")
        else:
            self.percentage_label.setText("")


class QuickStatsCard(QFrame):
    """A subtle card showing quick statistics."""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("quick_stats_card")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("📊 Quick Stats")
        title.setStyleSheet(f"color: {styles.COLORS['text_secondary']}; font-size: 12px; font-weight: bold;")
        layout.addWidget(title)
        
        # Stats grid
        stats_layout = QGridLayout()
        stats_layout.setSpacing(4)
        
        # Create stat labels
        self.last_scan_label = QLabel("Last scan: --")
        self.sites_scanned_label = QLabel("Sites scanned today: --")
        self.success_rate_label = QLabel("Success rate: --")
        self.offer_coverage_label = QLabel("Offer coverage: --")
        
        stat_style = f"color: {styles.COLORS['text_secondary']}; font-size: 11px;"
        self.last_scan_label.setStyleSheet(stat_style)
        self.sites_scanned_label.setStyleSheet(stat_style)
        self.success_rate_label.setStyleSheet(stat_style)
        self.offer_coverage_label.setStyleSheet(stat_style)
        
        stats_layout.addWidget(self.last_scan_label, 0, 0)
        stats_layout.addWidget(self.sites_scanned_label, 0, 1)
        stats_layout.addWidget(self.success_rate_label, 1, 0)
        stats_layout.addWidget(self.offer_coverage_label, 1, 1)
        
        layout.addLayout(stats_layout)
        
        self.setStyleSheet(f"""
            QFrame#quick_stats_card {{
                background-color: {styles.COLORS['bg_subtle']};
                border: 1px solid {styles.COLORS['border_light']};
                border-radius: 8px;
            }}
        """)
    
    def update_stats(self, last_scan=None, sites_scanned=None, success_rate=None, offer_coverage=None):
        if last_scan:
            self.last_scan_label.setText(f"Last scan: {last_scan}")
        if sites_scanned is not None:
            self.sites_scanned_label.setText(f"Scanned today: {sites_scanned}")
        if success_rate is not None:
            self.success_rate_label.setText(f"Success rate: {success_rate:.1f}%")
        if offer_coverage is not None:
            self.offer_coverage_label.setText(f"Offer coverage: {offer_coverage:.1f}%")


class RecentChangesPanel(QFrame):
    """Panel showing recent status changes."""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("recent_changes_panel")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("🔄 Recent Status Changes")
        title.setStyleSheet(f"color: {styles.COLORS['text_primary']}; font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        
        # Scrollable list
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.container = QWidget()
        self.changes_layout = QVBoxLayout(self.container)
        self.changes_layout.setContentsMargins(0, 0, 0, 0)
        self.changes_layout.setSpacing(6)
        self.changes_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll, 1)
        
        self.setStyleSheet(f"""
            QFrame#recent_changes_panel {{
                background-color: {styles.COLORS['bg_white']};
                border: 1px solid {styles.COLORS['border']};
                border-radius: 8px;
            }}
        """)
    
    def update_changes(self, changes):
        """Update the list of recent changes. 
        changes: list of dicts with keys: client, old_status, new_status, timestamp
        """
        # Clear existing
        while self.changes_layout.count():
            child = self.changes_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not changes:
            no_changes = QLabel("No recent changes")
            no_changes.setStyleSheet(f"color: {styles.COLORS['text_tertiary']}; font-size: 11px; padding: 10px;")
            no_changes.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.changes_layout.addWidget(no_changes)
        else:
            for change in changes[:15]:  # Show max 15
                item = self._create_change_item(change)
                self.changes_layout.addWidget(item)
        
        self.changes_layout.addStretch()
    
    def _create_change_item(self, change):
        """Create a single change item widget."""
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)
        
        # Status change icon/arrow
        old_status = change.get('old_status', '?')
        new_status = change.get('new_status', '?')
        
        # Determine color based on change direction
        if new_status == 'PASS':
            color = styles.COLORS['success']
            icon_name = 'fa5s.arrow-up'
        elif new_status in ['FAIL', 'ERROR']:
            color = styles.COLORS['danger']
            icon_name = 'fa5s.arrow-down'
        else:
            color = styles.COLORS['warning']
            icon_name = 'fa5s.arrow-right'
        
        icon_label = QLabel()
        icon = qta.icon(icon_name, color=color)
        icon_label.setPixmap(icon.pixmap(12, 12))
        layout.addWidget(icon_label)
        
        # Client name and change text
        text = f"{change.get('client', 'Unknown')}: {old_status} → {new_status}"
        text_label = QLabel(text)
        text_label.setStyleSheet(f"color: {styles.COLORS['text_primary']}; font-size: 11px;")
        layout.addWidget(text_label, 1)
        
        # Timestamp
        timestamp = change.get('timestamp', '')
        if timestamp:
            time_label = QLabel(timestamp)
            time_label.setStyleSheet(f"color: {styles.COLORS['text_tertiary']}; font-size: 10px;")
            layout.addWidget(time_label)
        
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {styles.COLORS['bg_subtle']};
                border-radius: 4px;
            }}
        """)
        
        return frame


class ProviderBreakdownPanel(QFrame):
    """Panel showing breakdown of sites by provider."""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("provider_panel")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("🔌 Web Providers")
        title.setStyleSheet(f"color: {styles.COLORS['text_primary']}; font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        
        # Container for bars
        self.bars_container = QWidget()
        self.bars_layout = QVBoxLayout(self.bars_container)
        self.bars_layout.setContentsMargins(0, 0, 0, 0)
        self.bars_layout.setSpacing(8)
        
        layout.addWidget(self.bars_container, 1)
        
        self.setStyleSheet(f"""
            QFrame#provider_panel {{
                background-color: {styles.COLORS['bg_white']};
                border: 1px solid {styles.COLORS['border']};
                border-radius: 8px;
            }}
        """)
    
    def update_providers(self, provider_counts, total):
        """Update provider breakdown.
        provider_counts: dict of provider_name -> count
        total: total number of sites
        """
        # Clear existing
        while self.bars_layout.count():
            child = self.bars_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not provider_counts or total == 0:
            no_data = QLabel("No provider data")
            no_data.setStyleSheet(f"color: {styles.COLORS['text_tertiary']}; font-size: 11px;")
            no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.bars_layout.addWidget(no_data)
            return
        
        # Sort by count descending
        sorted_providers = sorted(provider_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Color palette for providers
        colors = [
            styles.COLORS['brand_primary'],
            styles.COLORS['success'],
            styles.COLORS['warning'],
            styles.COLORS['danger'],
            styles.COLORS['text_secondary'],
            styles.COLORS['brand_light'],
        ]
        
        for i, (provider, count) in enumerate(sorted_providers):
            if not provider or provider == 'nan':
                provider = "Unknown"
            
            bar = self._create_provider_bar(provider, count, total, colors[i % len(colors)])
            self.bars_layout.addWidget(bar)
        
        self.bars_layout.addStretch()
    
    def _create_provider_bar(self, provider, count, total, color):
        """Create a single provider bar."""
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Label row
        label_layout = QHBoxLayout()
        
        name_label = QLabel(provider)
        name_label.setStyleSheet(f"color: {styles.COLORS['text_primary']}; font-size: 11px;")
        label_layout.addWidget(name_label)
        
        label_layout.addStretch()
        
        count_label = QLabel(f"{count}")
        count_label.setStyleSheet(f"color: {styles.COLORS['text_secondary']}; font-size: 11px;")
        label_layout.addWidget(count_label)
        
        layout.addLayout(label_layout)
        
        # Progress bar using horizontal layout for proper percentage scaling
        percentage = (count / total) * 100 if total > 0 else 0
        
        bar_layout = QHBoxLayout()
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(0)
        
        # Filled portion
        bar_fill = QFrame()
        bar_fill.setFixedHeight(8)
        bar_fill.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)
        
        # Empty portion
        bar_empty = QFrame()
        bar_empty.setFixedHeight(8)
        bar_empty.setStyleSheet(f"""
            QFrame {{
                background-color: {styles.COLORS['bg_subtle']};
                border-radius: 4px;
            }}
        """)
        
        # Use stretch factors for percentage-based sizing
        fill_stretch = max(1, int(percentage))
        empty_stretch = max(1, int(100 - percentage))
        
        bar_layout.addWidget(bar_fill, fill_stretch)
        bar_layout.addWidget(bar_empty, empty_stretch)
        
        layout.addLayout(bar_layout)
        
        return frame


class OfferBreakdownPanel(QFrame):
    """Panel showing breakdown of sites by offer type."""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("offer_panel")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("🏷️ Active Offers")
        title.setStyleSheet(f"color: {styles.COLORS['text_primary']}; font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        
        # Container for bars
        self.bars_container = QWidget()
        self.bars_layout = QVBoxLayout(self.bars_container)
        self.bars_layout.setContentsMargins(0, 0, 0, 0)
        self.bars_layout.setSpacing(8)
        
        layout.addWidget(self.bars_container, 1)
        
        self.setStyleSheet(f"""
            QFrame#offer_panel {{
                background-color: {styles.COLORS['bg_white']};
                border: 1px solid {styles.COLORS['border']};
                border-radius: 8px;
            }}
        """)
    
    def update_offers(self, offer_counts, total):
        """Update offer breakdown.
        offer_counts: dict of offer_name -> count
        total: total number of sites
        """
        # Clear existing
        while self.bars_layout.count():
            child = self.bars_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not offer_counts or total == 0:
            no_data = QLabel("No offer data")
            no_data.setStyleSheet(f"color: {styles.COLORS['text_tertiary']}; font-size: 11px;")
            no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.bars_layout.addWidget(no_data)
            return
        
        # Sort by count descending
        sorted_offers = sorted(offer_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Color palette for offers (different from providers)
        colors = [
            styles.COLORS['success'],
            styles.COLORS['brand_primary'],
            styles.COLORS['warning'],
            styles.COLORS['brand_light'],
            styles.COLORS['danger'],
            styles.COLORS['text_secondary'],
        ]
        
        for i, (offer, count) in enumerate(sorted_offers[:10]):  # Limit to top 8
            bar = self._create_offer_bar(offer, count, total, colors[i % len(colors)])
            self.bars_layout.addWidget(bar)
        
        self.bars_layout.addStretch()
    
    def _create_offer_bar(self, offer, count, total, color):
        """Create a single offer bar."""
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Label row - truncate long offer names
        label_layout = QHBoxLayout()
        
        display_name = offer[:20] + "..." if len(offer) > 20 else offer
        name_label = QLabel(display_name)
        name_label.setStyleSheet(f"color: {styles.COLORS['text_primary']}; font-size: 11px;")
        name_label.setToolTip(offer)  # Full name on hover
        label_layout.addWidget(name_label)
        
        label_layout.addStretch()
        
        count_label = QLabel(f"{count}")
        count_label.setStyleSheet(f"color: {styles.COLORS['text_secondary']}; font-size: 11px;")
        label_layout.addWidget(count_label)
        
        layout.addLayout(label_layout)
        
        # Progress bar using horizontal layout for proper percentage scaling
        percentage = (count / total) * 100 if total > 0 else 0
        
        bar_layout = QHBoxLayout()
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(0)
        
        # Filled portion
        bar_fill = QFrame()
        bar_fill.setFixedHeight(8)
        bar_fill.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)
        
        # Empty portion
        bar_empty = QFrame()
        bar_empty.setFixedHeight(8)
        bar_empty.setStyleSheet(f"""
            QFrame {{
                background-color: {styles.COLORS['bg_subtle']};
                border-radius: 4px;
            }}
        """)
        
        # Use stretch factors for percentage-based sizing
        fill_stretch = max(1, int(percentage))
        empty_stretch = max(1, int(100 - percentage))
        
        bar_layout.addWidget(bar_fill, fill_stretch)
        bar_layout.addWidget(bar_empty, empty_stretch)
        
        layout.addLayout(bar_layout)
        
        return frame


class AttentionItem(QFrame):
    """A single item in the attention list."""
    
    def __init__(self, client_name, status, details, url=""):
        super().__init__()
        self.setObjectName("attention_item")
        
        # Determine color based on status
        if status == "FAIL":
            color = styles.COLORS["danger"]
            icon_name = "fa5s.times-circle"
        elif status == "WARN":
            color = styles.COLORS["warning_yellow"]
            icon_name = "fa5s.exclamation-triangle"
        elif status == "BLOCKED":
            color = styles.COLORS["warning"]
            icon_name = "fa5s.ban"
        else:
            color = styles.COLORS["text_secondary"]
            icon_name = "fa5s.question-circle"
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)
        
        # Status icon
        icon_label = QLabel()
        icon = qta.icon(icon_name, color=color)
        icon_label.setPixmap(icon.pixmap(14, 14))
        layout.addWidget(icon_label)
        
        # Client name
        name_label = QLabel(client_name)
        name_label.setStyleSheet(f"color: {styles.COLORS['text_primary']}; font-size: 11px; font-weight: bold;")
        name_label.setMinimumWidth(120)
        name_label.setMaximumWidth(180)
        layout.addWidget(name_label)
        
        # Status badge
        status_label = QLabel(status)
        status_label.setStyleSheet(f"""
            background-color: {color};
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 9px;
            font-weight: bold;
        """)
        layout.addWidget(status_label)
        
        # Details (truncated)
        details_text = details[:40] + "..." if len(details) > 40 else details
        details_label = QLabel(details_text)
        details_label.setStyleSheet(f"color: {styles.COLORS['text_secondary']}; font-size: 10px;")
        layout.addWidget(details_label, 1)
        
        self.setStyleSheet(f"""
            QFrame#attention_item {{
                background-color: {styles.COLORS['bg_white']};
                border: 1px solid {styles.COLORS['border_light']};
                border-radius: 4px;
            }}
            QFrame#attention_item:hover {{
                background-color: {styles.COLORS['bg_hover']};
            }}
        """)


class EmailReportDialog(QDialog):
    """Dialog showing email content for copy/paste."""
    
    def __init__(self, content, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Email Report")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header = QLabel("📧 Email Report Content")
        header.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header.setStyleSheet(f"color: {styles.COLORS['brand_dark']};font-size: 24px;")
        layout.addWidget(header)
        
        # Instructions
        instructions = QLabel("Copy the content below and paste into your email client:")
        instructions.setStyleSheet(f"color: {styles.COLORS['text_secondary']};")
        layout.addWidget(instructions)
        
        # Content area
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(content)
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(QFont("Consolas", 10))
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {styles.COLORS['bg_white']};
                border: 1px solid {styles.COLORS['border']};
                border-radius: 4px;
                padding: 10px;
            }}
        """)
        layout.addWidget(self.text_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        copy_btn = QPushButton(" Copy to Clipboard")
        copy_btn.setObjectName("btn_brand")
        copy_btn.setIcon(qta.icon('fa5s.copy', color='white'))
        copy_btn.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(copy_btn)
        
        close_btn = QPushButton(" Close")
        close_btn.setIcon(qta.icon('fa5s.times', color='#555'))
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.setStyleSheet(styles.MODERN_STYLESHEET)
    
    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())
        QMessageBox.information(self, "Copied", "Report content copied to clipboard!")


class DashboardTab(QWidget):
    """Dashboard tab with status overview and email report generation."""
    
    # Signal to request data refresh from main window
    refresh_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.data = None
        self.previous_statuses = {}  # Track previous statuses for change detection
        self.status_history = []  # List of status changes
        self.load_history()
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # --- Header ---
        header_layout = QHBoxLayout()
        
        title = QLabel("Admin Summary")
        title.setStyleSheet(f"color: {styles.COLORS['brand_dark']}; font-size: 28px; font-weight: bold;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Last updated label
        self.last_updated = QLabel("Last updated: --")
        self.last_updated.setStyleSheet(f"color: {styles.COLORS['text_tertiary']};")
        header_layout.addWidget(self.last_updated)
        
        # Refresh button
        refresh_btn = QPushButton(" Refresh")
        refresh_btn.setIcon(qta.icon('fa5s.sync-alt', color='#555'))
        refresh_btn.clicked.connect(self.request_refresh)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # --- Main Content: Two Columns ---
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # === LEFT COLUMN ===
        left_column = QVBoxLayout()
        left_column.setSpacing(15)
        
        # Status Cards Row 1
        cards_layout_1 = QHBoxLayout()
        cards_layout_1.setSpacing(12)
        
        self.card_total = StatusCard("TOTAL", "fa5s.list", color_key="brand_primary")
        self.card_pass = StatusCard("PASS", "fa5s.check-circle", color_key="success")
        self.card_fail = StatusCard("FAIL", "fa5s.times-circle", color_key="danger")
        self.card_warn = StatusCard("WARN", "fa5s.exclamation-triangle", color_key="warning_yellow")
        
        cards_layout_1.addWidget(self.card_total)
        cards_layout_1.addWidget(self.card_pass)
        cards_layout_1.addWidget(self.card_fail)
        cards_layout_1.addWidget(self.card_warn)
        
        left_column.addLayout(cards_layout_1)
        
        # Status Cards Row 2
        cards_layout_2 = QHBoxLayout()
        cards_layout_2.setSpacing(12)
        
        self.card_pending = StatusCard("PENDING", "fa5s.clock", color_key="text_secondary")
        self.card_blocked = StatusCard("BLOCKED", "fa5s.ban", color_key="warning")
        self.card_na = StatusCard("N/A", "fa5s.question-circle", color_key="row_unverifiable_red")
        self.card_archived = StatusCard("ARCHIVED", "fa5s.archive", color_key="text_tertiary")
        
        cards_layout_2.addWidget(self.card_pending)
        cards_layout_2.addWidget(self.card_blocked)
        cards_layout_2.addWidget(self.card_na)
        cards_layout_2.addWidget(self.card_archived)
        
        left_column.addLayout(cards_layout_2)
        
        # Attention Section Header
        attention_header = QHBoxLayout()
        
        attention_title = QLabel("⚠️ Sites Needing Attention")
        attention_title.setStyleSheet(f"color: {styles.COLORS['text_primary']}; font-size: 16px; font-weight: bold;")
        attention_header.addWidget(attention_title)
        
        attention_header.addStretch()
        
        # Email Report Button
        self.email_btn = QPushButton(" Email Report")
        self.email_btn.setObjectName("btn_brand")
        self.email_btn.setIcon(qta.icon('fa5s.envelope', color='white'))
        self.email_btn.clicked.connect(self.generate_email_report)
        attention_header.addWidget(self.email_btn)
        
        left_column.addLayout(attention_header)
        
        # Attention List
        self.attention_scroll = QScrollArea()
        self.attention_scroll.setWidgetResizable(True)
        self.attention_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {styles.COLORS['border']};
                border-radius: 8px;
                background-color: {styles.COLORS['bg_subtle']};
            }}
        """)
        
        self.attention_container = QWidget()
        self.attention_layout = QVBoxLayout(self.attention_container)
        self.attention_layout.setContentsMargins(8, 8, 8, 8)
        self.attention_layout.setSpacing(6)
        self.attention_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.attention_scroll.setWidget(self.attention_container)
        left_column.addWidget(self.attention_scroll, 1)
        
        # Add left column to content (takes ~55% width)
        left_widget = QWidget()
        left_widget.setLayout(left_column)
        content_layout.addWidget(left_widget, 55)
        
        # === RIGHT COLUMN ===
        right_column = QVBoxLayout()
        right_column.setSpacing(15)
        
        # Quick Stats Card (subtle, at top)
        self.quick_stats = QuickStatsCard()
        right_column.addWidget(self.quick_stats)
        
        # Recent Changes Panel
        self.recent_changes = RecentChangesPanel()
        right_column.addWidget(self.recent_changes, 1)
        
        # Bottom row: Provider and Offer panels side-by-side
        bottom_panels = QHBoxLayout()
        bottom_panels.setSpacing(15)
        
        # Provider Breakdown Panel
        self.provider_breakdown = ProviderBreakdownPanel()
        bottom_panels.addWidget(self.provider_breakdown, 1)
        
        # Offer Breakdown Panel
        self.offer_breakdown = OfferBreakdownPanel()
        bottom_panels.addWidget(self.offer_breakdown, 1)
        
        right_column.addLayout(bottom_panels, 1)
        
        # Add right column to content (takes ~45% width)
        right_widget = QWidget()
        right_widget.setLayout(right_column)
        content_layout.addWidget(right_widget, 45)
        
        layout.addLayout(content_layout, 1)
    
    def request_refresh(self):
        self.refresh_requested.emit()
    
    def load_history(self):
        """Load status change history from file."""
        try:
            if HISTORY_FILE.exists():
                with open(HISTORY_FILE, 'r') as f:
                    data = json.load(f)
                    self.status_history = data.get('changes', [])
                    self.previous_statuses = data.get('last_statuses', {})
        except Exception as e:
            print(f"Could not load history: {e}")
            self.status_history = []
            self.previous_statuses = {}
    
    def save_history(self):
        """Save status change history to file."""
        try:
            HISTORY_FILE.parent.mkdir(exist_ok=True)
            with open(HISTORY_FILE, 'w') as f:
                json.dump({
                    'changes': self.status_history[-100:],  # Keep last 100
                    'last_statuses': self.previous_statuses
                }, f, indent=2)
        except Exception as e:
            print(f"Could not save history: {e}")
    
    def update_dashboard(self, df):
        """Update all dashboard metrics from dataframe."""
        self.data = df
        
        if df is None or df.empty:
            self.clear_dashboard()
            return
        
        # Count statuses and gather data
        total_active = 0
        archived = 0
        counts = {
            'PASS': 0, 'FAIL': 0, 'WARN': 0, 'PENDING': 0,
            'BLOCKED': 0, 'N/A': 0, 'UNVERIFIABLE': 0, 'ERROR': 0
        }
        provider_counts = {}
        offer_counts = {}
        attention_items = []
        current_statuses = {}
        sites_with_offers = 0
        
        for _, row in df.iterrows():
            active = str(row.get('Active', 'Yes'))
            client_name = str(row.get('Client Name', 'Unknown'))
            
            if active == "No":
                archived += 1
                continue
            
            total_active += 1
            status = str(row.get('Status', 'PENDING')).replace('📋', '').strip()
            
            # Normalize status
            if status == 'N/A':
                status = 'UNVERIFIABLE'
            
            current_statuses[client_name] = status
            
            if status in counts:
                counts[status] += 1
            else:
                counts['PENDING'] += 1
            
            # Provider tracking
            provider = str(row.get('Detected Provider', '') or row.get('Expected Provider', ''))
            if provider and provider != 'nan':
                provider_counts[provider] = provider_counts.get(provider, 0) + 1
            else:
                provider_counts['Unknown'] = provider_counts.get('Unknown', 0) + 1
            
            # Offer tracking
            offer = str(row.get('Offer', ''))
            if offer and offer != 'nan' and offer.strip():
                sites_with_offers += 1
                # Count by offer type
                offer_counts[offer] = offer_counts.get(offer, 0) + 1
            else:
                offer_counts['No Offer'] = offer_counts.get('No Offer', 0) + 1
            
            # Attention items
            if status in ['FAIL', 'WARN', 'BLOCKED', 'ERROR']:
                attention_items.append((
                    client_name,
                    status,
                    str(row.get('Details', '')),
                    str(row.get('URL', ''))
                ))
        
        # Detect status changes
        self.detect_changes(current_statuses)
        
        # Combine N/A and UNVERIFIABLE
        na_count = counts['N/A'] + counts['UNVERIFIABLE']
        
        # Update status cards
        if total_active > 0:
            self.card_pass.update_values(counts['PASS'], (counts['PASS'] / total_active) * 100)
            self.card_fail.update_values(counts['FAIL'], (counts['FAIL'] / total_active) * 100)
            self.card_warn.update_values(counts['WARN'], (counts['WARN'] / total_active) * 100)
        else:
            self.card_pass.update_values(0)
            self.card_fail.update_values(0)
            self.card_warn.update_values(0)
        
        self.card_total.update_values(total_active)
        self.card_pending.update_values(counts['PENDING'])
        self.card_blocked.update_values(counts['BLOCKED'])
        self.card_na.update_values(na_count)
        self.card_archived.update_values(archived)
        
        # Update quick stats
        success_rate = (counts['PASS'] / total_active * 100) if total_active > 0 else 0
        offer_coverage = (sites_with_offers / total_active * 100) if total_active > 0 else 0
        self.quick_stats.update_stats(
            last_scan=datetime.now().strftime('%I:%M %p'),
            sites_scanned=total_active,
            success_rate=success_rate,
            offer_coverage=offer_coverage
        )
        
        # Update attention list
        self.update_attention_list(attention_items)
        
        # Update recent changes
        self.recent_changes.update_changes(self.status_history[-15:][::-1])  # Reverse for newest first
        
        # Update provider breakdown
        self.provider_breakdown.update_providers(provider_counts, total_active)
        
        # Update offer breakdown
        self.offer_breakdown.update_offers(offer_counts, total_active)
        
        # Update timestamp
        self.last_updated.setText(f"Last updated: {datetime.now().strftime('%I:%M %p')}")
    
    def detect_changes(self, current_statuses):
        """Detect and record status changes."""
        timestamp = datetime.now().strftime('%m/%d %I:%M %p')
        
        for client, new_status in current_statuses.items():
            old_status = self.previous_statuses.get(client)
            
            if old_status and old_status != new_status:
                # Status changed!
                change = {
                    'client': client,
                    'old_status': old_status,
                    'new_status': new_status,
                    'timestamp': timestamp
                }
                self.status_history.append(change)
        
        # Update previous statuses
        self.previous_statuses = current_statuses.copy()
        self.save_history()
    
    def update_attention_list(self, items):
        """Update the attention items list."""
        while self.attention_layout.count():
            child = self.attention_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not items:
            no_issues = QLabel("✅ All clear - no sites need attention!")
            no_issues.setStyleSheet(f"color: {styles.COLORS['success']}; font-size: 12px; padding: 15px;")
            no_issues.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.attention_layout.addWidget(no_issues)
        else:
            priority = {'FAIL': 0, 'ERROR': 1, 'WARN': 2, 'BLOCKED': 3}
            items.sort(key=lambda x: priority.get(x[1], 99))
            
            for client, status, details, url in items:
                item = AttentionItem(client, status, details, url)
                self.attention_layout.addWidget(item)
        
        self.attention_layout.addStretch()
    
    def clear_dashboard(self):
        """Clear all dashboard data."""
        self.card_pass.update_values(0)
        self.card_fail.update_values(0)
        self.card_warn.update_values(0)
        self.card_total.update_values(0)
        self.card_pending.update_values(0)
        self.card_blocked.update_values(0)
        self.card_na.update_values(0)
        self.card_archived.update_values(0)
        self.update_attention_list([])
        self.recent_changes.update_changes([])
        self.provider_breakdown.update_providers({}, 0)
        self.offer_breakdown.update_offers({}, 0)
        self.last_updated.setText("Last updated: --")
    
    def generate_email_report(self):
        """Generate email report content and show dialog."""
        if self.data is None or self.data.empty:
            QMessageBox.warning(self, "No Data", "No data available to generate report.")
            return
        
        # Gather stats
        total_active = 0
        archived = 0
        counts = {'PASS': 0, 'FAIL': 0, 'WARN': 0, 'PENDING': 0, 'BLOCKED': 0, 'N/A': 0}
        attention_items = []
        
        for _, row in self.data.iterrows():
            active = str(row.get('Active', 'Yes'))
            if active == "No":
                archived += 1
                continue
            
            total_active += 1
            status = str(row.get('Status', 'PENDING')).replace('📋', '').strip()
            
            if status == 'UNVERIFIABLE':
                status = 'N/A'
            
            if status in counts:
                counts[status] += 1
            
            if status in ['FAIL', 'WARN', 'ERROR']:
                attention_items.append({
                    'client': str(row.get('Client Name', 'Unknown')),
                    'url': str(row.get('URL', '')),
                    'status': status,
                    'details': str(row.get('Details', '')),
                    'offer': str(row.get('Offer', ''))
                })
        
        priority = {'FAIL': 0, 'ERROR': 1, 'WARN': 2}
        attention_items.sort(key=lambda x: priority.get(x['status'], 99))
        
        date_str = datetime.now().strftime("%B %d, %Y")
        time_str = datetime.now().strftime("%I:%M %p")
        
        content = f"""MyOffer Monitor - Daily Health Check
{date_str} at {time_str}
{'=' * 50}

SUMMARY
-------
✅ PASS:    {counts['PASS']:>4}  ({(counts['PASS']/total_active*100) if total_active > 0 else 0:.1f}%)
❌ FAIL:    {counts['FAIL']:>4}  ({(counts['FAIL']/total_active*100) if total_active > 0 else 0:.1f}%)
⚠️ WARN:    {counts['WARN']:>4}  ({(counts['WARN']/total_active*100) if total_active > 0 else 0:.1f}%)
🔄 PENDING: {counts['PENDING']:>4}
🚫 BLOCKED: {counts['BLOCKED']:>4}
📋 N/A:     {counts['N/A']:>4}
{'─' * 30}
   TOTAL:   {total_active:>4} active sites

"""
        
        if attention_items:
            content += f"""
SITES NEEDING ATTENTION ({len(attention_items)})
{'─' * 50}
"""
            for item in attention_items:
                content += f"""
❌ {item['client']}
   URL: {item['url']}
   Status: {item['status']}
   Issue: {item['details']}
"""
                if item['offer']:
                    content += f"   Offer: {item['offer']}\n"
        else:
            content += """
✅ ALL SITES PASSING
No sites need attention at this time.
"""
        
        content += f"""
{'=' * 50}
Generated by MyOffer Monitor
"""
        
        dialog = EmailReportDialog(content, self)
        dialog.exec()
