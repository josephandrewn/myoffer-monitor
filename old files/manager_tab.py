import sys
import pandas as pd
import qtawesome as qta  # <--- NEW ICON LIBRARY
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QMessageBox, QFileDialog, QLineEdit, QAbstractItemView, 
                             QFrame, QComboBox, QLabel)
from PyQt6.QtGui import (QColor, QFont, QUndoStack, QUndoCommand)
from PyQt6.QtCore import Qt, pyqtSignal

# Import our new theme file
import styles

# --- UNDO COMMANDS (Logic remains identical) ---
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
            item = self.table.item(row, 6)
            if not item:
                item = QTableWidgetItem("Yes")
                self.table.setItem(row, 6, item)
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
            self.table.item(row, 6).setText(old_val)
            self.manager.update_row_style(row)
        self.table.blockSignals(False)
        self.manager.emit_change()

class CommandAddRow(QUndoCommand):
    def __init__(self, manager, row_idx, data=None):
        super().__init__("Add Row")
        self.manager = manager
        self.table = manager.table
        self.row_idx = row_idx
        self.data = data 

    def redo(self):
        self.table.blockSignals(True)
        self.table.insertRow(self.row_idx)
        if self.data:
            for col, text in enumerate(self.data):
                self.table.setItem(self.row_idx, col, QTableWidgetItem(text))
        else:
            self.table.setItem(self.row_idx, 0, QTableWidgetItem("New Client"))
            self.table.setItem(self.row_idx, 1, QTableWidgetItem("https://"))
            self.table.setItem(self.row_idx, 2, QTableWidgetItem("")) 
            self.table.setItem(self.row_idx, 3, QTableWidgetItem("")) 
            self.table.setItem(self.row_idx, 4, QTableWidgetItem("PENDING"))
            self.table.setItem(self.row_idx, 5, QTableWidgetItem("")) 
            self.table.setItem(self.row_idx, 6, QTableWidgetItem("Yes")) 
        
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


# --- MAIN WIDGET ---
class ManagerTab(QWidget):
    data_modified = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        self.file_path = None
        self.df = pd.DataFrame(columns=["Client Name", "URL", "Provider", "Config", "Status", "Details", "Active"])
        self.undo_stack = QUndoStack(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # --- Top Controls Frame ---
        top_frame = QFrame()
        top_frame.setObjectName("top_control_frame") # Uses the White Card style from styles.py
        
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(15, 15, 15, 15)
        top_layout.setSpacing(12)

        # --- BUTTONS WITH ICONS ---
        
        # Load
        self.btn_load = QPushButton(" Load List")
        self.btn_load.setIcon(qta.icon('fa5s.folder-open', color='#555'))
        self.btn_load.clicked.connect(self.load_csv)
        
        # Save (Green)
        self.btn_save = QPushButton(" Save Changes")
        self.btn_save.setObjectName("btn_success") # Triggers Green Style
        self.btn_save.setIcon(qta.icon('fa5s.save', color='white'))
        self.btn_save.clicked.connect(self.save_csv)

        # Undo
        self.btn_undo = QPushButton(" Undo")
        self.btn_undo.setIcon(qta.icon('fa5s.undo-alt', color='#555'))
        self.btn_undo.clicked.connect(self.undo_stack.undo)
        self.btn_undo.setEnabled(False)
        self.undo_stack.canUndoChanged.connect(self.btn_undo.setEnabled)
        
        # Add (Blue)
        self.btn_add = QPushButton(" Add Client")
        self.btn_add.setObjectName("btn_primary") # Triggers Blue Style
        self.btn_add.setIcon(qta.icon('fa5s.plus-circle', color='white'))
        self.btn_add.clicked.connect(self.add_row)
        
        # Archive
        self.btn_archive = QPushButton(" Archive")
        self.btn_archive.setIcon(qta.icon('fa5s.archive', color='#555'))
        self.btn_archive.setToolTip("Toggle selected clients between Active and Archived")
        self.btn_archive.clicked.connect(self.toggle_archive)
        
        # Reset
        self.btn_reset = QPushButton(" Reset Status")
        self.btn_reset.setIcon(qta.icon('fa5s.sync-alt', color='#555'))
        self.btn_reset.clicked.connect(self.reset_status)

        # Delete (Red)
        self.btn_del = QPushButton(" Delete")
        self.btn_del.setObjectName("btn_danger") # Triggers Red Style
        self.btn_del.setIcon(qta.icon('fa5s.trash-alt', color='white'))
        self.btn_del.clicked.connect(self.delete_row)

        self.undo_stack.indexChanged.connect(self.emit_change)

        # Add buttons to layout
        top_layout.addWidget(self.btn_load)
        top_layout.addWidget(self.btn_save)
        top_layout.addWidget(self.btn_undo)
        top_layout.addStretch()
        top_layout.addWidget(self.btn_add)
        top_layout.addWidget(self.btn_archive) 
        top_layout.addWidget(self.btn_reset)
        top_layout.addWidget(self.btn_del)
        layout.addWidget(top_frame)

        # --- Filter Bar ---
        filter_layout = QHBoxLayout()
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Search Client or URL...")
        self.search_bar.textChanged.connect(self.filter_table)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Statuses", "PENDING", "PASS", "FAIL", "WARN", "BLOCKED", "ERROR", "ARCHIVED"])
        self.filter_combo.currentTextChanged.connect(self.filter_table)

        filter_layout.addWidget(self.search_bar)
        filter_layout.addWidget(QLabel("Filter by:"))
        filter_layout.addWidget(self.filter_combo)
        layout.addLayout(filter_layout)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(7) 
        self.table.setHorizontalHeaderLabels(["Client Name", "URL", "Provider", "Config", "Status", "Details", "Active"])
        self.table.setSortingEnabled(True) # Enabled by default for Manager
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        self.table.setColumnWidth(0, 180)
        self.table.setColumnWidth(2, 130)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(6, 60) 
        
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.itemChanged.connect(self.on_item_changed)
        
        layout.addWidget(self.table)
    
    def emit_change(self):
        self.data_modified.emit()

    def get_dataframe(self):
        data = []
        for r in range(self.table.rowCount()):
            def get_text(col):
                item = self.table.item(r, col)
                return item.text() if item else ""

            row_data = {
                "Client Name": get_text(0),
                "URL": get_text(1),
                "Provider": get_text(2),
                "Config": get_text(3),
                "Status": get_text(4),
                "Details": get_text(5),
                "Active": get_text(6), 
            }
            data.append(row_data)
        return pd.DataFrame(data)

    def update_row_style(self, row):
        if row >= self.table.rowCount(): return

        active_item = self.table.item(row, 6)
        is_active = active_item.text() == "Yes" if active_item else True
        
        status_item = self.table.item(row, 4)
        status_text = status_item.text() if status_item else ""
        
        # Use Colors from styles.py
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
            elif status_text == 'PENDING':
                bg_color = QColor(styles.COLORS["row_pending_bg"])
                text_color = QColor(styles.COLORS["row_pending_text"])

        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                item.setBackground(bg_color)
                item.setForeground(text_color)
                
                if col in [4, 6]: 
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setFont(QFont("Arial", 10, QFont.Weight.Bold))

    def load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if path:
            self.file_path = path
            try:
                self.df = pd.read_csv(path)
                required = ["Client Name", "URL", "Provider", "Config", "Status", "Details", "Active"]
                for col in required:
                    if col not in self.df.columns:
                        if col == "Active": val = "Yes"
                        elif col == "Status": val = "PENDING"
                        else: val = ""
                        self.df[col] = val
                
                self.df['Status'] = self.df['Status'].fillna('PENDING')
                self.df['Active'] = self.df['Active'].fillna('Yes')
                
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
            self.table.setItem(i, 0, QTableWidgetItem(str(row['Client Name'])))
            self.table.setItem(i, 1, QTableWidgetItem(str(row['URL'])))
            self.table.setItem(i, 2, QTableWidgetItem(str(row['Provider']) if pd.notna(row['Provider']) else ""))
            self.table.setItem(i, 3, QTableWidgetItem(str(row['Config']) if pd.notna(row['Config']) else ""))
            self.table.setItem(i, 4, QTableWidgetItem(str(row['Status']) if pd.notna(row['Status']) else "PENDING"))
            self.table.setItem(i, 5, QTableWidgetItem(str(row['Details']) if pd.notna(row['Details']) else ""))
            
            active_val = str(row['Active']) if pd.notna(row['Active']) else "Yes"
            self.table.setItem(i, 6, QTableWidgetItem(active_val))

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
        if not rows: return
        
        # 1. LOCK SORTING (Prevents rows from jumping while we edit them)
        self.table.setSortingEnabled(False) 
        
        self.undo_stack.beginMacro("Reset Status")
        for row in rows:
            def push_edit(col, new_val):
                item = self.table.item(row, col)
                old_val = item.text() if item else ""
                if old_val != new_val:
                    cmd = CommandEditCell(self, row, col, old_val, new_val)
                    self.undo_stack.push(cmd)
            
            # CLEAR EVERYTHING
            push_edit(2, "")        # Provider
            push_edit(3, "")        # Config
            push_edit(4, "PENDING") # Status
            push_edit(5, "")        # Details
            
        self.undo_stack.endMacro()
        
        # 2. UNLOCK SORTING (Restores order)
        self.table.setSortingEnabled(True)

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
        except Exception as e:
            QMessageBox.critical(self, "Error Saving", str(e))

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
            item_status = self.table.item(r, 4)
            item_active = self.table.item(r, 6)
            
            if status_filter == "ARCHIVED":
                if item_active.text() == "Yes": status_match = False
            elif status_filter != "All Statuses":
                if item_active.text() == "No": 
                    status_match = False 
                elif item_status.text() != status_filter:
                    status_match = False

            self.table.setRowHidden(r, not (text_match and status_match))