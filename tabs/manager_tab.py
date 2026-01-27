import sys
import pandas as pd
import qtawesome as qta 
import pdfplumber
import re
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QMessageBox, QFileDialog, QLineEdit, QAbstractItemView, 
                             QFrame, QComboBox, QLabel)
from PyQt6.QtGui import (QColor, QFont, QUndoStack, QUndoCommand)
from PyQt6.QtCore import Qt, pyqtSignal

import styles

# --- HELPER: PDF EXTRACTION ---
def extract_client_data_from_pdf(pdf_path):
    """
    Parses the Client PDF to extract launch configuration data.
    Uses line-by-line scanning to handle columnar layouts better.
    """
    extracted_data = {
        "client_name": "New Client",
        "website_url": "https://",
        "provider": "",
        "primary_name": "",
        "primary_email": "",
        "gm_name": "",
        "gm_email": "",
        "lead_email": "",
        "crm_email": ""
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            # We focus on Page 1 & 2 mostly
            full_text = ""
            for i, page in enumerate(pdf.pages):
                if i > 2: break # Only need first 3 pages usually
                full_text += page.extract_text() + "\n"
    except Exception as e:
        print(f"PDF Read Error: {e}")
        return extracted_data

    lines = full_text.split('\n')
    
    # --- 1. Client Name Strategy ---
    # Heuristic: The client name often appears before "CONTRACT FOR SERVICE"
    # or is the first non-header line.
    for i, line in enumerate(lines):
        clean_line = line.strip()
        if "CONTRACT FOR SERVICE" in clean_line:
            # Look at the 1-2 lines before this
            if i > 0 and len(lines[i-1].strip()) > 3:
                extracted_data["client_name"] = lines[i-1].strip()
            break
        # Fallback: If we see "Triple Threatt" (header), maybe the NEXT line is the client
        if "TRIPLE" in clean_line and "THREATT" in clean_line:
            # Check upcoming lines
            if i + 2 < len(lines):
                candidate = lines[i+2].strip()
                if candidate and "my OFFER" not in candidate:
                    extracted_data["client_name"] = candidate

    # --- 2. Field Scanning ---
    # We loop through lines. If we find a label, we look ahead for the value.
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Helper to grab next non-empty line
        def get_next_value(start_index):
            for j in range(start_index + 1, min(start_index + 5, len(lines))):
                val = lines[j].strip()
                if val and "_" not in val and ":" not in val: # Avoid empty lines or other labels
                    return val
            return ""

        # URL
        if "website url" in line_lower:
            # First, check if the URL is ON this line
            match = re.search(r"((https?://)?(www\.)?\S+\.\S+)", line)
            
            # CHECK: Is the match valid and not just "https://"?
            if match and len(match.group(1)) > 10: 
                extracted_data["website_url"] = match.group(1)
            else:
                # Look ahead for a URL-like string in the next 5 lines
                for j in range(i + 1, min(i + 6, len(lines))):
                    scan_line = lines[j].strip()
                    url_match = re.search(r"((https?://)?(www\.)?\S+\.\S+)", scan_line)
                    if url_match and len(url_match.group(1)) > 10: # Ensure length > 10
                        extracted_data["website_url"] = url_match.group(1)
                        break

        # Vendor
        if "website vendor" in line_lower:
            # Common vendors list to validate against
            known_vendors = ["Dealer Inspire", "Dealer.com", "Sokal", "DealerOn", "Fox Dealer", "FordDirect", "Shift Digital"]
            
            found_vendor = ""
            # Check current line
            for v in known_vendors:
                if v.lower() in line_lower: found_vendor = v
            
            # Check next lines if not found
            if not found_vendor:
                val = get_next_value(i)
                if val: found_vendor = val
            
            if found_vendor: extracted_data["provider"] = found_vendor

        # Primary Contact Name (Look for "Primary Contact Name" but NOT "Email")
        if "primary contact name" in line_lower:
            parts = line.split(":")
            if len(parts) > 1 and parts[1].strip():
                extracted_data["primary_name"] = parts[1].strip()
            else:
                extracted_data["primary_name"] = get_next_value(i)

        # Primary Email
        if "primary contact email" in line_lower:
            match = re.search(r"(\S+@\S+)", line)
            if match: extracted_data["primary_email"] = match.group(1)
            else:
                # check next line
                val = get_next_value(i)
                if "@" in val: extracted_data["primary_email"] = val

        # GM Name
        if "general manager name" in line_lower:
            parts = line.split(":")
            if len(parts) > 1 and parts[1].strip():
                extracted_data["gm_name"] = parts[1].strip()
            else:
                extracted_data["gm_name"] = get_next_value(i)

        # GM Email
        if "general manager email" in line_lower:
            match = re.search(r"(\S+@\S+)", line)
            if match: extracted_data["gm_email"] = match.group(1)
            else:
                val = get_next_value(i)
                if "@" in val: extracted_data["gm_email"] = val

        # CRM Email
        if "crm destination email" in line_lower:
             match = re.search(r"(\S+@\S+)", line)
             if match: extracted_data["crm_email"] = match.group(1)
             else:
                val = get_next_value(i)
                if "@" in val: extracted_data["crm_email"] = val

    return extracted_data


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
            # Data expected to include hidden columns now
            for col, text in enumerate(self.data):
                self.table.setItem(self.row_idx, col, QTableWidgetItem(text))
        else:
            # Default Empty Row
            self.table.setItem(self.row_idx, 0, QTableWidgetItem("New Client"))
            self.table.setItem(self.row_idx, 1, QTableWidgetItem("https://"))
            self.table.setItem(self.row_idx, 2, QTableWidgetItem("")) 
            self.table.setItem(self.row_idx, 3, QTableWidgetItem("")) 
            self.table.setItem(self.row_idx, 4, QTableWidgetItem("PENDING"))
            self.table.setItem(self.row_idx, 5, QTableWidgetItem("")) 
            self.table.setItem(self.row_idx, 6, QTableWidgetItem("Yes"))
            
            # Initialize Hidden Columns (7-12)
            for c in range(7, 13):
                self.table.setItem(self.row_idx, c, QTableWidgetItem(""))

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
        # Updated columns to include hidden fields for PDF data
        self.columns = [
            "Client Name", "URL", "Provider", "Config", "Status", "Details", "Active",
            "Primary Name", "Primary Email", "GM Name", "GM Email", "Lead Email", "CRM Email"
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
        
        # --- NEW: IMPORT PDF BUTTON ---
        self.btn_import = QPushButton(" Import PDF")
        self.btn_import.setObjectName("btn_primary")
        self.btn_import.setIcon(qta.icon('fa5s.file-pdf', color='white'))
        self.btn_import.clicked.connect(self.import_pdf_dialog)

        self.btn_add = QPushButton(" Add Manual")
        self.btn_add.setIcon(qta.icon('fa5s.plus-circle', color='#555'))
        self.btn_add.clicked.connect(self.add_row)
        
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
        top_layout.addStretch()
        top_layout.addWidget(self.btn_import) # Added here
        top_layout.addWidget(self.btn_add)
        top_layout.addWidget(self.btn_archive) 
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
        self.table.setColumnCount(len(self.columns)) 
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.setSortingEnabled(True)
        
        # Hide the extra data columns
        for i in range(7, 13):
            self.table.setColumnHidden(i, True)

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
            row_data = {}
            for c, col_name in enumerate(self.columns):
                item = self.table.item(r, c)
                row_data[col_name] = item.text() if item else ""
            data.append(row_data)
        return pd.DataFrame(data)

    def update_row_style(self, row):
        if row >= self.table.rowCount(): return

        active_item = self.table.item(row, 6)
        is_active = active_item.text() == "Yes" if active_item else True
        
        status_item = self.table.item(row, 4)
        status_text = status_item.text() if status_item else ""
        
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
                
                # Ensure all columns exist, even if CSV is old format
                for col in self.columns:
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
            # Loop through all columns (visible and hidden)
            for c, col_name in enumerate(self.columns):
                val = str(row[col_name]) if pd.notna(row[col_name]) else ""
                self.table.setItem(i, c, QTableWidgetItem(val))

            self.update_row_style(i)
            
        self.table.blockSignals(False)
        self.table.setSortingEnabled(True)

    def on_item_changed(self, item):
        # We handle edits via UndoStack commands primarily, 
        # but direct edits need to be captured if we want undo support for them.
        # For simplicity in this snippets, we let direct edits happen.
        pass 

    def add_row(self):
        row_idx = self.table.rowCount()
        command = CommandAddRow(self, row_idx) 
        self.undo_stack.push(command)
        self.table.scrollToBottom()

    # --- NEW: IMPORT PDF FUNCTION ---
    def import_pdf_dialog(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Client PDF", "", "PDF Files (*.pdf)")
        if not file_name: return

        data = extract_client_data_from_pdf(file_name)
        
        # Prepare the row data based on our self.columns list
        row_data = [
            data.get("client_name", "New Client"), # 0 Client Name
            data.get("website_url", "https://"),   # 1 URL
            data.get("provider", ""),              # 2 Provider
            "",                                    # 3 Config
            "PENDING",                             # 4 Status
            "Imported from PDF",                   # 5 Details
            "Yes",                                 # 6 Active
            data.get("primary_name", ""),          # 7 Primary Name
            data.get("primary_email", ""),         # 8 Primary Email
            data.get("gm_name", ""),               # 9 GM Name
            data.get("gm_email", ""),              # 10 GM Email
            data.get("lead_email", ""),            # 11 Lead Email
            data.get("crm_email", "")              # 12 CRM Email
        ]

        row_idx = self.table.rowCount()
        command = CommandAddRow(self, row_idx, row_data)
        self.undo_stack.push(command)
        
        self.table.scrollToBottom()
        QMessageBox.information(self, "Import Successful", "Client data extracted and added to list.")

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