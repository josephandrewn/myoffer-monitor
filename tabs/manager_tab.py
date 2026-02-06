import sys
import pandas as pd
import qtawesome as qta 
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QMessageBox, QFileDialog, QLineEdit, QAbstractItemView, 
                             QFrame, QComboBox, QLabel, QDialog, QTextEdit,
                             QDialogButtonBox, QScrollArea)
from PyQt6.QtGui import (QColor, QFont, QUndoStack, QUndoCommand)
from PyQt6.QtCore import Qt, pyqtSignal

import assets.styles as styles 

from config import DEFAULT_COLUMNS, app_settings
try:
    from config import ENABLE_DATABASE
except ImportError:
    ENABLE_DATABASE = False  # Default to disabled if not defined
from logger import get_logger
from database import get_database
import harvester

logger = get_logger(__name__)

# --- UNDO COMMANDS ---
class CommandEditCell(QUndoCommand):
    def __init__(self, manager, row, col, old_text, new_text):
        super().__init__(f"Edit Cell {row},{col}")
        self.manager = manager
        self.table = manager.table
        self.row = row
        self.col = col
        self.old_text = old_text
        self.new_text = new_text

    def redo(self):
        self.table.blockSignals(True)
        item = self.table.item(self.row, self.col)
        if not item:
            item = QTableWidgetItem()
            self.table.setItem(self.row, self.col, item)
        item.setText(self.new_text)
        self.table.blockSignals(False)
        self.manager.update_row_style(self.row)

    def undo(self):
        self.table.blockSignals(True)
        item = self.table.item(self.row, self.col)
        if item: item.setText(self.old_text)
        self.table.blockSignals(False)
        self.manager.update_row_style(self.row)

class CommandToggleActive(QUndoCommand):
    def __init__(self, manager, row_indices):
        super().__init__("Toggle Active Status")
        self.manager = manager
        self.table = manager.table
        self.row_indices = row_indices
        self.previous_states = {} 

    def redo(self):
        self.table.blockSignals(True)
        for row in self.row_indices:
            item = self.table.item(row, 9)  # Active column is now index 9
            if not item:
                item = QTableWidgetItem("Yes")
                self.table.setItem(row, 9, item)
            current_val = item.text()
            self.previous_states[row] = current_val
            new_val = "No" if current_val == "Yes" else "Yes"
            item.setText(new_val)
            self.manager.update_row_style(row)
        self.table.blockSignals(False)
        self.manager.emit_change()

    def undo(self):
        self.table.blockSignals(True)
        for row, old_val in self.previous_states.items():
            self.table.item(row, 9).setText(old_val)  # Active column is now index 9
            self.manager.update_row_style(row)
        self.table.blockSignals(False)
        self.manager.emit_change()

class CommandAddRow(QUndoCommand):
    def __init__(self, manager, row_idx):
        super().__init__("Add Row")
        self.manager = manager
        self.table = manager.table
        self.row_idx = row_idx

    def redo(self):
        self.table.blockSignals(True)
        self.table.insertRow(self.row_idx)
        
        # Default Empty Row - 10 columns
        self.table.setItem(self.row_idx, 0, QTableWidgetItem("New Client"))  # Client Name
        self.table.setItem(self.row_idx, 1, QTableWidgetItem("https://"))    # URL
        self.table.setItem(self.row_idx, 2, QTableWidgetItem(""))            # Expected Provider
        self.table.setItem(self.row_idx, 3, QTableWidgetItem(""))            # Detected Provider
        self.table.setItem(self.row_idx, 4, QTableWidgetItem(""))            # Config
        self.table.setItem(self.row_idx, 5, QTableWidgetItem("PENDING"))     # Status
        self.table.setItem(self.row_idx, 6, QTableWidgetItem(""))            # Details
        self.table.setItem(self.row_idx, 7, QTableWidgetItem(""))            # Site Map
        self.table.setItem(self.row_idx, 8, QTableWidgetItem(""))            # Offer
        self.table.setItem(self.row_idx, 9, QTableWidgetItem("Yes"))         # Active

        self.manager.update_row_style(self.row_idx)
        self.table.blockSignals(False)
        self.manager.emit_change()

    def undo(self):
        self.table.blockSignals(True)
        self.table.removeRow(self.row_idx)
        self.table.blockSignals(False)
        self.manager.emit_change()

class CommandDeleteRow(QUndoCommand):
    def __init__(self, manager, row_idx, row_data):
        super().__init__("Delete Row")
        self.manager = manager
        self.table = manager.table
        self.row_idx = row_idx
        self.row_data = row_data 

    def redo(self):
        self.table.blockSignals(True)
        self.table.removeRow(self.row_idx)
        self.table.blockSignals(False)
        self.manager.emit_change()

    def undo(self):
        self.table.blockSignals(True)
        self.table.insertRow(self.row_idx)
        for col, text in enumerate(self.row_data):
            self.table.setItem(self.row_idx, col, QTableWidgetItem(text))
        self.manager.update_row_style(self.row_idx)
        self.table.blockSignals(False)
        self.manager.emit_change()

class CommandResetStatus(QUndoCommand):
    def __init__(self, manager, row_indices):
        super().__init__("Reset Status")
        self.manager = manager
        self.table = manager.table
        self.row_indices = row_indices
        self.previous_data = {} # {row: {col: text}}

    def redo(self):
        self.table.blockSignals(True)
        for row in self.row_indices:
            # Save state for undo
            self.previous_data[row] = {}
            for col in [4, 5, 6, 9]: # Config, Status, Details, Active (skip Site Map and Offer)
                item = self.table.item(row, col)
                self.previous_data[row][col] = item.text() if item else ""
            
            # Reset values
            self.table.item(row, 4).setText("")          # Config -> Empty
            self.table.item(row, 5).setText("PENDING")   # Status -> PENDING
            self.table.item(row, 6).setText("")          # Details -> Empty
            self.table.item(row, 9).setText("Yes")       # Active -> Yes
            
            self.manager.update_row_style(row)
        self.table.blockSignals(False)
        self.manager.emit_change()

    def undo(self):
        self.table.blockSignals(True)
        for row, cols in self.previous_data.items():
            for col, text in cols.items():
                self.table.item(row, col).setText(text)
            self.manager.update_row_style(row)
        self.table.blockSignals(False)
        self.manager.emit_change()


# --- MAIN WIDGET ---
class ManagerTab(QWidget):
    data_modified = pyqtSignal()
    
    # List of known providers for dropdown
    PROVIDER_OPTIONS = ["", "DealerOn", "Dealer.com", "Dealer Inspire", "DealerSocket", "Sokal", "Other"]
    
    def __init__(self):
        super().__init__()
        
        self.file_path = None
        self.columns = [
            "Client Name", "URL", "Expected Provider", "Detected Provider", 
            "Config", "Status", "Details", "Site Map", "Offer", "Active"
        ]
        self.df = pd.DataFrame(columns=self.columns)
        self.undo_stack = QUndoStack(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # --- Top Controls Frame ---
        top_frame = QFrame()
        top_frame.setObjectName("top_control_frame")
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(15, 15, 15, 15)
        top_layout.setSpacing(12)

        # Buttons
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
        
        self.btn_sitemap = QPushButton(" View Site Map")
        self.btn_sitemap.setIcon(qta.icon('fa5s.sitemap', color='#555'))
        self.btn_sitemap.clicked.connect(self.view_site_map)

        self.undo_stack.indexChanged.connect(self.emit_change)

        # Layout Order
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
        self.search_bar.textChanged.connect(self.filter_table)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Statuses", "PENDING", "PASS", "FAIL", "WARN", "BLOCKED", "N/A", "ERROR", "ARCHIVED"])
        self.filter_combo.currentTextChanged.connect(self.filter_table)
        
        # Add arrow indicator label (workaround for CSS arrow not rendering)
        arrow_label = QLabel("▼")
        arrow_label.setStyleSheet(f"color: {styles.COLORS['text_secondary']}; font-size: 10px; background: transparent; margin-left: -20px;")

        filter_layout.addWidget(self.search_bar)
        filter_layout.addWidget(QLabel("Filter by:"))
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addWidget(arrow_label)
        layout.addLayout(filter_layout)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns)) 
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.setSortingEnabled(True)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # URL
        
        # Column widths - 10 columns
        # 0: Client Name, 1: URL (stretch), 2: Expected Provider, 3: Detected Provider
        # 4: Config, 5: Status, 6: Details, 7: Site Map, 8: Offer, 9: Active
        self.table.setColumnWidth(0, 300)   # Client Name
        self.table.setColumnWidth(2, 150)   # Expected Provider
        self.table.setColumnWidth(3, 150)   # Detected Provider
        self.table.setColumnWidth(4, 70)    # Config
        self.table.setColumnWidth(5, 110)   # Status
        self.table.setColumnWidth(6, 120)   # Details
        self.table.setColumnWidth(7, 80)    # Site Map
        self.table.setColumnWidth(8, 180)   # Offer
        self.table.setColumnWidth(9, 65)    # Active
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.itemChanged.connect(self.on_item_changed)
        
        layout.addWidget(self.table)
    
    def emit_change(self):
        self.data_modified.emit()

    def get_dataframe(self):
        data = []
        for r in range(self.table.rowCount()):
            row_data = {}
            for c, col_name in enumerate(self.columns):
                item = self.table.item(r, c)
                row_data[col_name] = item.text() if item else ""
            data.append(row_data)
        return pd.DataFrame(data)

    def update_row_style(self, row):
        if row >= self.table.rowCount(): return

        # Active column is now index 9
        active_item = self.table.item(row, 9)
        is_active = active_item.text() == "Yes" if active_item else True
        
        # Status column is index 5
        status_item = self.table.item(row, 5)
        if status_item:
            status_text = status_item.data(Qt.ItemDataRole.UserRole)
            if status_text is None:
                status_text = status_item.text().replace("📋", "").strip()
        else:
            status_text = ""
        
        bg_color = QColor(styles.COLORS["row_pending_bg"])
        text_color = QColor(styles.COLORS["row_pending_text"])

        if not is_active:
            bg_color = QColor(styles.COLORS["row_inactive_bg"])
            text_color = QColor(styles.COLORS["row_inactive_text"])
        else:
            if status_text == 'PASS':
                bg_color = QColor(styles.COLORS["row_pass_bg"])
                text_color = QColor(styles.COLORS["row_pass_text"])
            elif status_text in ['WARN', 'BLOCKED']:
                bg_color = QColor(styles.COLORS["row_warn_bg"])
                text_color = QColor(styles.COLORS["row_warn_text"])
            elif status_text in ['FAIL', 'ERROR']:
                bg_color = QColor(styles.COLORS["row_fail_bg"])
                text_color = QColor(styles.COLORS["row_fail_text"])
            elif status_text in ['UNVERIFIABLE', 'N/A']:
                bg_color = QColor(styles.COLORS["row_unverifiable_bg"])
                text_color = QColor(styles.COLORS["row_unverifiable_text"])
            elif status_text == 'PENDING':
                bg_color = QColor(styles.COLORS["row_pending_bg"])
                text_color = QColor(styles.COLORS["row_pending_text"])

        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                item.setBackground(bg_color)
                item.setForeground(text_color)
                
                # Status (5), Site Map (7), and Active (9) columns get centered bold text
                if col in [5, 7, 9]: 
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setFont(QFont("Arial", 10, QFont.Weight.Bold))

    def load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if path:
            self.file_path = path
            try:
                self.df = pd.read_csv(path)
                
                # Handle legacy CSV files with single "Provider" column
                # Map it to "Expected Provider" and leave "Detected Provider" empty
                if "Provider" in self.df.columns and "Expected Provider" not in self.df.columns:
                    self.df = self.df.rename(columns={"Provider": "Expected Provider"})
                    logger.info("Mapped legacy 'Provider' column to 'Expected Provider'")
                
                # Also handle case where Provider column exists alongside new columns
                # (in case of partial migration)
                if "Provider" in self.df.columns and "Expected Provider" in self.df.columns:
                    # If Expected Provider is empty but Provider has data, copy it over
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

    def populate_table(self):
        self.table.setSortingEnabled(False)
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        
        for i, row in self.df.iterrows():
            self.table.insertRow(i)
            
            # Get URL for site map check
            url = str(row.get('URL', '')) if pd.notna(row.get('URL', '')) else ""
            check_url = url if url.startswith('http') else f"https://{url}"
            has_sitemap = url and harvester.has_site_map(check_url)
            
            for c, col_name in enumerate(self.columns):
                val = str(row[col_name]) if pd.notna(row[col_name]) else ""
                
                # For Status column, clean any legacy icons
                if c == 5:  # Status column
                    val = val.replace('📋', '').strip()
                
                # For Site Map column, set based on whether site map exists
                if c == 7:  # Site Map column
                    val = "Yes" if has_sitemap else ""
                
                item = QTableWidgetItem(val)
                
                # Store actual status in UserRole for Status column
                if c == 5:
                    item.setData(Qt.ItemDataRole.UserRole, val)
                
                self.table.setItem(i, c, item)

            self.update_row_style(i)
            
        self.table.blockSignals(False)
        self.table.setSortingEnabled(True)

    def on_item_changed(self, item):
        pass 

    def add_row(self):
        row_idx = self.table.rowCount()
        command = CommandAddRow(self, row_idx) 
        self.undo_stack.push(command)
        self.table.scrollToBottom()

    def delete_row(self):
        rows = sorted(set(index.row() for index in self.table.selectedIndexes()), reverse=True)
        if not rows: return
        self.undo_stack.beginMacro("Delete Rows")
        for row_idx in rows:
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row_idx, col)
                row_data.append(item.text() if item else "")
            command = CommandDeleteRow(self, row_idx, row_data)
            self.undo_stack.push(command)
        self.undo_stack.endMacro()
        
    def toggle_archive(self):
        rows = sorted(set(index.row() for index in self.table.selectedIndexes()))
        if not rows: return
        command = CommandToggleActive(self, rows)
        self.undo_stack.push(command)

    def reset_status(self):
        rows = sorted(set(index.row() for index in self.table.selectedIndexes()))
        if not rows: 
            QMessageBox.information(self, "Select Rows", "Please select rows to reset.")
            return
            
        command = CommandResetStatus(self, rows)
        self.undo_stack.push(command)

    def save_csv(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        default_name = f"sites_{timestamp}.csv"
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Snapshot", default_name, "CSV Files (*.csv)")
        
        if not file_path: return

        new_df = self.get_dataframe()
        try:
            new_df.to_csv(file_path, index=False)
            QMessageBox.information(self, "Saved", f"Snapshot saved successfully!\n{file_path}")
            self.undo_stack.setClean() 
            self.file_path = file_path
            self.sync_to_database()
        except Exception as e:
            QMessageBox.critical(self, "Error Saving", str(e))

    def import_offers(self):
        """Import offers from a CSV file with Client Name and Offer columns."""
        path, _ = QFileDialog.getOpenFileName(
            self, 
            "Import Offers CSV", 
            "", 
            "CSV Files (*.csv)"
        )
        if not path:
            return
        
        try:
            import_df = pd.read_csv(path)
            
            # Validate required columns
            if 'Client Name' not in import_df.columns:
                QMessageBox.warning(
                    self, 
                    "Invalid CSV", 
                    "CSV must contain a 'Client Name' column."
                )
                return
            
            if 'Offer' not in import_df.columns:
                QMessageBox.warning(
                    self, 
                    "Invalid CSV", 
                    "CSV must contain an 'Offer' column."
                )
                return
            
            # Build lookup from current table (Client Name -> row index)
            client_to_row = {}
            for row in range(self.table.rowCount()):
                client_item = self.table.item(row, 0)
                if client_item:
                    client_name = client_item.text().strip()
                    client_to_row[client_name] = row
            
            # Process imports
            updated = 0
            not_found = []
            
            self.table.blockSignals(True)
            
            for _, import_row in import_df.iterrows():
                client_name = str(import_row['Client Name']).strip()
                offer_value = str(import_row['Offer']).strip() if pd.notna(import_row['Offer']) else ""
                
                if client_name in client_to_row:
                    row_idx = client_to_row[client_name]
                    # Update Offer column (index 8)
                    offer_item = self.table.item(row_idx, 8)
                    if offer_item:
                        offer_item.setText(offer_value)
                    else:
                        self.table.setItem(row_idx, 8, QTableWidgetItem(offer_value))
                    updated += 1
                else:
                    not_found.append(client_name)
            
            self.table.blockSignals(False)
            self.emit_change()
            
            # Show summary
            message = f"Updated {updated} offer(s)."
            
            if not_found:
                message += f"\n\n⚠️ {len(not_found)} client(s) not found:\n"
                # Show first 10 not found
                for name in not_found[:10]:
                    message += f"  • {name}\n"
                if len(not_found) > 10:
                    message += f"  ... and {len(not_found) - 10} more"
            
            QMessageBox.information(self, "Import Complete", message)
            
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Error importing offers:\n{str(e)}")

    def filter_table(self):
        search_text = self.search_bar.text().lower()
        status_filter = self.filter_combo.currentText()
        
        for r in range(self.table.rowCount()):
            item_name = self.table.item(r, 0)
            item_url = self.table.item(r, 1)
            text_match = False
            if (item_name and search_text in item_name.text().lower()) or \
               (item_url and search_text in item_url.text().lower()):
                text_match = True
            
            status_match = True
            item_status = self.table.item(r, 5)   # Status column is 5
            item_active = self.table.item(r, 9)   # Active column is now 9
            
            if status_filter == "ARCHIVED":
                if item_active.text() == "Yes": status_match = False
            elif status_filter == "N/A":
                # N/A filter matches both "N/A" display and "UNVERIFIABLE" data
                if item_active.text() == "No":
                    status_match = False
                elif item_status.text() not in ["N/A", "UNVERIFIABLE"]:
                    status_match = False
            elif status_filter != "All Statuses":
                if item_active.text() == "No": 
                    status_match = False 
                elif item_status.text() != status_filter:
                    status_match = False

            self.table.setRowHidden(r, not (text_match and status_match))

    def sync_to_database(self):
        """Sync current table data to database"""
        if not ENABLE_DATABASE:
            return
        
        try:
            db = get_database()
            df = self.get_dataframe()
            db.from_dataframe(df, replace=True)
            logger.info("Data synced to database", records=len(df))
        except Exception as e:
            logger.error("Failed to sync to database", exception=e)
            QMessageBox.warning(self, "Database Sync Error", 
                            f"Could not sync to database: {str(e)}")

    def view_site_map(self):
        """Show site map dialog for selected row."""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.information(self, "No Selection", "Please select a row to view its site map.")
            return
        
        row = selected[0].row()
        client_name = self.table.item(row, 0).text() if self.table.item(row, 0) else "Unknown"
        url = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
        provider = self.table.item(row, 2).text() if self.table.item(row, 2) else ""  # Expected Provider
        
        if not url:
            QMessageBox.warning(self, "No URL", "Selected row has no URL.")
            return
        
        # Get site map data
        site_map = harvester.get_site_map_summary(url)
        
        # Show dialog
        dialog = SiteMapDialog(self, client_name, url, provider, site_map)
        dialog.exec()


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
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {styles.COLORS['bg_white']};
            }}
        """)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(8)
        
        if site_map and site_map.get("links"):
            links = site_map.get("links", {})
            
            for category in harvester.CATEGORY_ORDER:
                urls = links.get(category, [])
                
                # Category label (bold)
                cat_label = QLabel(f"<b>{category}</b>")
                cat_label.setStyleSheet("background: transparent; margin-top: 8px;")
                content_layout.addWidget(cat_label)
                
                if urls:
                    for url_item in urls:
                        url_label = QLabel(url_item)
                        url_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                        url_label.setWordWrap(True)
                        url_label.setStyleSheet(f"""
                            color: {styles.COLORS['brand_primary']}; 
                            background: transparent;
                            padding-left: 10px;
                        """)
                        content_layout.addWidget(url_label)
                else:
                    not_found = QLabel("Not found")
                    not_found.setStyleSheet(f"""
                        color: {styles.COLORS['text_tertiary']}; 
                        font-style: italic;
                        background: transparent;
                        padding-left: 10px;
                    """)
                    content_layout.addWidget(not_found)
            
            # Other links section
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
            # No data message
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
        refresh_btn.setEnabled(False)  # TODO: Implement refresh (requires browser)
        refresh_btn.setToolTip("Refresh requires running from Scanner tab")
        button_layout.addWidget(refresh_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setObjectName("btn_primary")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def refresh_site_map(self):
        """Refresh site map - placeholder for future implementation."""
        QMessageBox.information(
            self, 
            "Refresh", 
            "To refresh the site map, use 'Check Site Map' in the Scanner tab.\n"
            "This will re-harvest the navigation links from the website."
        )