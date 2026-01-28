import sys
import qtawesome as qta
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QMessageBox, 
                             QVBoxLayout, QWidget, QLabel, QToolBar)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, QSize 

# --- UPDATED IMPORTS ---
# Removed 'tabs.launchpad_tab'
from tabs.manager_tab import ManagerTab
from tabs.scanner_tab import ScannerTab

import assets.styles as styles 

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

        self.setWindowTitle("MyOffer Dashboard Pro")
        self.resize(1400, 900)
        
        # APPLY GLOBAL THEME
        self.setStyleSheet(styles.MODERN_STYLESHEET)
        
        # --- 1. Global Toolbar ---
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setStyleSheet("QToolBar { background: white; border-bottom: 1px solid #D2D2D7; padding: 10px; }")
        toolbar.setIconSize(QSize(20, 20)) 
        self.addToolBar(toolbar)

        # Save Action
        save_icon = qta.icon('fa5s.save', color=styles.COLORS["text_secondary"])
        save_action = QAction(save_icon, "Save Project", self)
        save_action.setStatusTip("Save the current Master List to CSV")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.trigger_save)
        toolbar.addAction(save_action)

        # --- 2. Setup Central Widget & Tabs ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)

        # Initialize the Sub-Apps (Launchpad Removed)
        self.manager = ManagerTab()
        self.scanner = ScannerTab()

        self.tabs.addTab(self.manager, " Data Manager")
        self.tabs.addTab(self.scanner, " Site Scanner")
        
        # Add icons to Tabs
        self.tabs.setTabIcon(0, qta.icon('fa5s.table', color=styles.COLORS["accent"]))
        self.tabs.setTabIcon(1, qta.icon('fa5s.robot', color=styles.COLORS["accent"]))
        
        main_layout.addWidget(self.tabs)

        # --- 3. Status Bar ---
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"color: {styles.COLORS['text_secondary']}; font-weight: bold;")
        self.statusBar().addWidget(self.status_label)

        # --- 4. Signal Connections ---
        self.manager.data_modified.connect(self.sync_data)
        self.scanner.scan_update_signal.connect(self.update_master_record)
        self.tabs.currentChanged.connect(self.on_tab_changed)

    def trigger_save(self):
        """Redirects the global save button to the Manager's save logic."""
        self.manager.save_csv()
        self.status_label.setText("Project Saved.")

    def on_tab_changed(self, index):
        """
        Handles logic when switching tabs.
        Index 0: Data Manager
        Index 1: Site Scanner
        """
        if index == 1: # Switching TO Scanner
            self.manager.table.setSortingEnabled(False)
            self.sync_data()
            self.status_label.setText("Scanner Mode: Viewing Active Pending Records")
            
        else: # Switching BACK to Manager (Index 0)
            self.manager.table.setSortingEnabled(True)
            self.status_label.setText("Manager Mode: Editing Master List")

    def sync_data(self):
        """Syncs data from Manager to Scanner"""
        df = self.manager.get_dataframe()
        self.scanner.load_from_dataframe(df)
        # Removed Launchpad sync
        
        count = len(df) if df is not None else 0
        self.status_label.setText(f"Synced {count} records.")

    def update_master_record(self, original_idx, status, msg, vendor, config):
        """
        Callback: The Scanner found a result. We must update the Master Manager.
        """
        # 1. Update Provider
        self.manager.table.item(original_idx, 2).setText(vendor if vendor else "Other")
            
        # 2. Update Config
        if config:
            self.manager.table.item(original_idx, 3).setText(config)

        # 3. Update Status
        status_item = self.manager.table.item(original_idx, 4)
        status_item.setText(status)
        
        # 4. Update Details
        self.manager.table.item(original_idx, 5).setText(msg)
        
        # 5. Trigger Color Refresh
        self.manager.update_row_style(original_idx)
        
        self.status_label.setText(f"Updated Record #{original_idx + 1}: {status}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())