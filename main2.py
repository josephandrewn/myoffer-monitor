import sys
import os
import json
import qtawesome as qta
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QMessageBox, 
                             QVBoxLayout, QHBoxLayout, QWidget, QLabel)
from PyQt6.QtGui import QAction, QPixmap, QIcon
from PyQt6.QtCore import Qt, QSize, QTimer

from tabs.manager_tab import ManagerTab
from tabs.scanner_tab import ScannerTab

import assets.styles as styles 

from config import app_settings, save_settings
from logger import get_logger
from database import get_database

logger = get_logger(__name__)

# Data directory for auto-saves and settings
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Logo path
LOGO_PATH = Path("assets/logo.png")
LOGO_PATH_FLAT = Path("assets/logo2.png")

# Settings file for remembering last opened file
RECENT_FILE_PATH = DATA_DIR / "recent_project.json"


def get_last_opened_file() -> str:
    """Get the path to the last opened file, if it exists."""
    try:
        if RECENT_FILE_PATH.exists():
            with open(RECENT_FILE_PATH, 'r') as f:
                data = json.load(f)
                path = data.get('last_file', '')
                if path and os.path.exists(path):
                    return path
    except Exception as e:
        logger.warning("Could not load recent file", exception=e)
    return ''


def save_last_opened_file(file_path: str):
    """Save the path to the most recently opened file."""
    try:
        DATA_DIR.mkdir(exist_ok=True)
        with open(RECENT_FILE_PATH, 'w') as f:
            json.dump({
                'last_file': file_path,
                'saved_at': datetime.now().isoformat()
            }, f, indent=2)
    except Exception as e:
        logger.warning("Could not save recent file path", exception=e)


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

        self.setWindowTitle("MyOffer Monitor")
        
        # Start maximized to full screen width
        self.showMaximized()
        
        # Set window icon (logo)
        if LOGO_PATH.exists():
            self.setWindowIcon(QIcon(str(LOGO_PATH)))
        
        # Apply global theme
        self.setStyleSheet(styles.MODERN_STYLESHEET)
        
        # --- Setup Central Widget ---
        central_widget = QWidget()
        central_widget.setObjectName("central_widget")
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Header with Logo ---
        header_widget = QWidget()
        header_widget.setFixedHeight(60)
        header_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {styles.COLORS["bg_white"]};
                border-bottom: none;
                margin-bottom: 3px;
            }}
        """)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        # Logo
        if LOGO_PATH_FLAT.exists():
            logo_label = QLabel()
            logo_pixmap = QPixmap(str(LOGO_PATH_FLAT))
            logo_label.setPixmap(logo_pixmap.scaledToHeight(40, Qt.TransformationMode.SmoothTransformation))
            logo_label.setStyleSheet("background: transparent;border-bottom:none;")
            header_layout.addWidget(logo_label)
        
        # App Title
        title_label = QLabel("MyOffer Monitor")
        title_label.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {styles.COLORS["brand_dark"]};
            background: transparent;
            padding-left: 12px;
            border-bottom: none;
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Version label
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet(f"""
            font-size: 11px;
            color: {styles.COLORS["text_tertiary"]};
            background: transparent;
            border-bottom: none;
        """)
        header_layout.addWidget(version_label)
        
        main_layout.addWidget(header_widget)

        # --- Tab Widget ---
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setDocumentMode(True)
        
        # Make tabs expand to fill width (50/50 split)
        self.tabs.tabBar().setExpanding(True)

        # Initialize the tabs
        self.manager = ManagerTab()
        self.scanner = ScannerTab()

        self.tabs.addTab(self.manager, "  Data Manager")
        self.tabs.addTab(self.scanner, "  Site Scanner")
        
        # Add icons to tabs (using brand color)
        self.tabs.setTabIcon(0, qta.icon('fa5s.table', color=styles.COLORS["brand_primary"]))
        self.tabs.setTabIcon(1, qta.icon('fa5s.robot', color=styles.COLORS["brand_primary"]))
        
        main_layout.addWidget(self.tabs)

        # --- Status Bar ---
        self.status_label = QLabel("Ready")
        self.statusBar().addWidget(self.status_label)
        
        # Add stretch to push count to the right
        self.statusBar().addWidget(QLabel(), 1)  # Spacer
        
        # Active clients count (right side)
        self.client_count_label = QLabel("Active Clients: 0")
        self.client_count_label.setStyleSheet(f"color: {styles.COLORS['text_secondary']};")
        self.statusBar().addWidget(self.client_count_label)

        # --- Signal Connections ---
        self.manager.data_modified.connect(self.sync_data)
        self.scanner.scan_update_signal.connect(self.update_master_record)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # --- Keyboard Shortcuts ---
        save_action = QAction("Save", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.trigger_save)
        self.addAction(save_action)

        # --- Auto-save Timer ---
        if app_settings.auto_save_enabled:
            self.auto_save_timer = QTimer()
            self.auto_save_timer.timeout.connect(self.auto_save)
            self.auto_save_timer.start(app_settings.auto_save_interval * 1000)
            logger.info("Auto-save enabled", interval=app_settings.auto_save_interval)
        
        # --- Load Last Opened File ---
        self.load_last_project()

    def load_last_project(self):
        """Automatically load the most recent project file (manual save or autosave)."""
        import os
        
        # Get the manually saved file (if any)
        manual_file = get_last_opened_file()
        manual_time = 0
        if manual_file and os.path.exists(manual_file):
            manual_time = os.path.getmtime(manual_file)
        
        # Get the most recent autosave (if any)
        autosave_file = None
        autosave_time = 0
        autosaves = sorted(DATA_DIR.glob("autosave_*.csv"), reverse=True)
        if autosaves:
            autosave_file = str(autosaves[0])
            autosave_time = os.path.getmtime(autosave_file)
        
        # Pick the most recent one
        if autosave_time > manual_time:
            last_file = autosave_file
            logger.info("Loading most recent autosave (newer than manual save)", path=last_file)
        elif manual_file:
            last_file = manual_file
            logger.info("Loading last manual save", path=last_file)
        else:
            last_file = None
        
        if last_file:
            try:
                import pandas as pd
                self.manager.df = pd.read_csv(last_file)
                
                # Handle legacy CSV files with single "Provider" column
                # Map it to "Expected Provider" and leave "Detected Provider" empty
                if "Provider" in self.manager.df.columns and "Expected Provider" not in self.manager.df.columns:
                    self.manager.df = self.manager.df.rename(columns={"Provider": "Expected Provider"})
                    logger.info("Mapped legacy 'Provider' column to 'Expected Provider'")
                
                # Also handle case where Provider column exists alongside new columns
                if "Provider" in self.manager.df.columns and "Expected Provider" in self.manager.df.columns:
                    # If Expected Provider is empty but Provider has data, copy it over
                    mask = (self.manager.df["Expected Provider"].isna() | (self.manager.df["Expected Provider"] == "")) & \
                           (self.manager.df["Provider"].notna() & (self.manager.df["Provider"] != ""))
                    self.manager.df.loc[mask, "Expected Provider"] = self.manager.df.loc[mask, "Provider"]
                    logger.info("Copied Provider data to empty Expected Provider fields")
                
                self.manager.df = self.manager.df.reindex(columns=self.manager.columns, fill_value="")
                self.manager.df['Status'] = self.manager.df['Status'].replace("", "PENDING").fillna('PENDING')
                self.manager.df['Active'] = self.manager.df['Active'].replace("", "Yes").fillna('Yes')
                self.manager.file_path = last_file
                self.manager.populate_table()
                self.sync_data()
                
                filename = os.path.basename(last_file)
                self.status_label.setText(f"Loaded: {filename}")
                logger.info("Loaded last project", path=last_file)
            except Exception as e:
                logger.warning("Could not load last project", exception=e)
                self.status_label.setText("Ready - Could not load last project")

    def auto_save(self):
        """Auto-save current state."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            auto_save_path = DATA_DIR / f"autosave_{timestamp}.csv"
            df = self.manager.get_dataframe()
            if df is not None and not df.empty:
                df.to_csv(auto_save_path, index=False)
                logger.info("Auto-save completed", path=str(auto_save_path))
                
                # Clean up old auto-saves (keep only last 5)
                self.cleanup_old_autosaves()
        except Exception as e:
            logger.error("Auto-save failed", exception=e)

    def cleanup_old_autosaves(self):
        """Keep only the 5 most recent auto-saves."""
        try:
            autosaves = sorted(DATA_DIR.glob("autosave_*.csv"), reverse=True)
            for old_file in autosaves[5:]:
                old_file.unlink()
        except Exception as e:
            logger.warning("Could not cleanup old autosaves", exception=e)

    def trigger_save(self):
        """Save the current project."""
        self.manager.save_csv()
        
        # Remember this file for next launch
        if self.manager.file_path:
            save_last_opened_file(self.manager.file_path)
        
        self.status_label.setText("Project Saved")

    def on_tab_changed(self, index):
        """Handle tab switching."""
        if index == 1:  # Scanner tab
            self.manager.table.setSortingEnabled(False)
            self.sync_data()
            self.status_label.setText(" Scanner Mode: Ready to scan")
        else:  # Manager tab
            self.manager.table.setSortingEnabled(True)
            self.status_label.setText(" Manager Mode: Edit your client list")

    def sync_data(self):
        """Sync data from Manager to Scanner."""
        df = self.manager.get_dataframe()
        self.scanner.load_from_dataframe(df)
        count = len(df) if df is not None else 0
        self.status_label.setText(f"Synced {count} records")
        self.update_client_count()

    def update_client_count(self):
        """Update the active clients count in the status bar."""
        active_count = 0
        for row in range(self.manager.table.rowCount()):
            active_item = self.manager.table.item(row, 9)  # Active column
            if active_item and active_item.text() == "Yes":
                active_count += 1
        self.client_count_label.setText(f"Active Clients: {active_count} ")

    def update_master_record(self, original_idx, status, msg, vendor, config):
        """Update the Manager table when Scanner finds a result."""
        try:
            # Update Detected Provider (column 3)
            provider_item = self.manager.table.item(original_idx, 3)
            if provider_item:
                provider_item.setText(vendor if vendor else "")
                
            # Update Config (column 4)
            config_item = self.manager.table.item(original_idx, 4)
            if config_item and config:
                config_item.setText(config)

            # Update Status (column 5)
            status_item = self.manager.table.item(original_idx, 5)
            if status_item:
                status_item.setText(status)
            
            # Update Details (column 6)
            details_item = self.manager.table.item(original_idx, 6)
            if details_item:
                details_item.setText(msg)
            
            # Refresh row styling
            self.manager.update_row_style(original_idx)
            
            self.status_label.setText(f"Updated: {status}")
        except Exception as e:
            logger.error("Failed to update master record", exception=e, row=original_idx)

    def create_backup(self):
        """Create database backup."""
        try:
            db = get_database()
            backup_path = db.create_backup()
            QMessageBox.information(
                self, "Backup Created", 
                f"Database backed up successfully!\n{backup_path}"
            )
            logger.info("Manual backup created", path=str(backup_path))
        except Exception as e:
            logger.error("Backup failed", exception=e)
            QMessageBox.critical(self, "Backup Error", str(e))

    def closeEvent(self, event):
        """Handle app close - save current file path for next launch."""
        if self.manager.file_path:
            save_last_opened_file(self.manager.file_path)
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set app-wide attributes
    app.setApplicationName("MyOffer Monitor")
    app.setApplicationVersion("1.0.0")
    
    # Set app icon
    if LOGO_PATH.exists():
        app.setWindowIcon(QIcon(str(LOGO_PATH)))
    
    window = MainApp()
    window.show()
    sys.exit(app.exec())
