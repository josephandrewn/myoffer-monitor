import sys
import time
import csv
import random
import pandas as pd
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import qtawesome as qta  # <--- NEW ICON LIBRARY
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QFileDialog, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLabel, QProgressBar, QLineEdit, 
                             QMessageBox, QFrame)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QColor, QFont

# Import our new theme file
import styles

# --- 1. LOGIC & HELPERS ---
def detect_provider(soup):
    """
    Analyzes the HTML soup to identify the website platform provider.
    Includes checks for SOKAL, Block pages, and Niche providers.
    """
    text_content = soup.get_text().lower()
    html_str = str(soup).lower()
    
    # --- SOKAL ---
    if "sokal.com" in html_str: return "SOKAL"
    if "go-sokal" in html_str: return "SOKAL"
    if "powered by sokal" in text_content: return "SOKAL"
    if "sokal_assets" in html_str: return "SOKAL"

    # --- MAJOR PROVIDERS ---
    if "dealerinspire.com" in html_str or "assets.dealerinspire" in html_str or "di-uploads" in html_str or 'id="di-root"' in html_str: return "Dealer Inspire"
    if "dealer eprocess" in text_content or "dealereprocess.com" in html_str or "dep_" in html_str: return "Dealer eProcess"
    if "dealer.com" in html_str or "ddc-footer" in html_str or "ddc-wrapper" in html_str: return "Dealer.com"
    if "dealeron" in text_content or "dealeron.com" in html_str: return "DealerOn"
    if "sincrodigital" in html_str or "cdkglobal" in html_str or 'content="sincro"' in html_str: return "Sincro/CDK"
    if "apollo.auto" in html_str or "teamvelocity" in html_str: return "Team Velocity"
    if "fox dealer" in text_content or "foxdealer" in html_str: return "Fox Dealer"

    # --- NICHE / INDEPENDENT ---
    if "dealerfire" in html_str: return "DealerFire"
    if "fusionzone" in html_str: return "FusionZone"
    if "dealercarsearch" in html_str: return "Dealer Car Search"
    if "dlrdmv" in html_str: return "DLRdmv"
    if "automanager" in html_str: return "AutoManager"
    
    # --- BLOCK PAGES (Common WAFs) ---
    if "imperva" in html_str or "_incapsula_" in html_str: return "Security Block (Imperva)"
    if "cloudflare" in html_str: return "Security Block (Cloudflare)"

    return "Other"

def check_url_rules(driver, url):
    """
    Navigates to a URL and counts occurrences of specific JS files.
    """
    TARGET_SPA    = "idrove.it/behaviour.spa.js"      
    TARGET_DCOM   = "idrove.it/behaviour.dcom.js"     
    TARGET_STD    = "idrove.it/behaviour.js"          
    TARGET_BUNDLE = "idrove.it/behaviour.bundle.js" 
    BASE_TARGET   = "idrove.it/behaviour"
    
    MAX_WAIT_TIME = 20 
    SETTLE_TIME = 4

    try:
        driver.get(url)
        
        start_time = time.time()
        while (time.time() - start_time) < MAX_WAIT_TIME:
            if BASE_TARGET in driver.page_source:
                time.sleep(SETTLE_TIME)
                break
            time.sleep(1)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        text_content = soup.get_text().lower()
        html_str = str(soup).lower()
        title_tag = soup.title.string.lower() if soup.title else ""
        
        detected_vendor = detect_provider(soup)
        if not detected_vendor: detected_vendor = "Other"

        # --- SECURITY BLOCK CHECK ---
        block_phrases = [
            "detected unusual activity",
            "unusual activity from your ip",
            "verify you are a human",
            "verify you are human",
            "access denied",
            "security challenge",
            "please enable cookies",
            "captcha-delivery",
            "challenge-platform",
            "just a moment...",
            "attention required",
            "cloudflare"
        ]
        
        is_blocked_text = any(phrase in text_content for phrase in block_phrases)
        is_blocked_title = any(phrase in title_tag for phrase in block_phrases)
        is_blocked_vendor = "Security Block" in detected_vendor
        
        if (is_blocked_text or is_blocked_title or is_blocked_vendor) and BASE_TARGET not in html_str:
            return {
                'status': 'BLOCKED', 
                'msg': 'Bot Detection / CAPTCHA', 
                'config': 'ERR', 
                'vendor': detected_vendor if detected_vendor != "Other" else "Security Block"
            }

        # --- STANDARD SCANNING ---
        counts = {
            "std":    {"head": 0, "body": 0},
            "dcom":   {"head": 0, "body": 0},
            "spa":    {"head": 0, "body": 0},
            "bundle": {"head": 0, "body": 0} 
        }

        def scan_section(section, name):
            if not section: return
            for script in section.find_all('script'):
                s = str(script)
                if TARGET_SPA in s: counts["spa"][name] += 1
                elif TARGET_DCOM in s: counts["dcom"][name] += 1
                elif TARGET_BUNDLE in s: counts["bundle"][name] += 1
                elif TARGET_STD in s: counts["std"][name] += 1

        scan_section(soup.find('head'), "head")
        scan_section(soup.find('body'), "body")

        total_std    = counts["std"]["head"] + counts["std"]["body"]
        total_dcom   = counts["dcom"]["head"] + counts["dcom"]["body"]
        total_spa    = counts["spa"]["head"] + counts["spa"]["body"]
        total_bundle = counts["bundle"]["head"] + counts["bundle"]["body"]
        
        def make_result(status, msg, config):
            return {
                'status': status, 
                'msg': msg, 
                'config': config, 
                'vendor': detected_vendor
            }

        # --- LOGIC RULES ---
        if total_std == 0 and total_dcom == 0 and total_spa == 0 and total_bundle == 0:
            return make_result('FAIL', 'No scripts found', 'NONE')

        if total_spa > 0:
            if total_spa == 4 and counts["spa"]["head"] == 0:
                return make_result('PASS', 'Perfect (Rule of 4)', 'SPA')
            else:
                return make_result('WARN', f'Found {total_spa} (Expected 4)', 'SPA')

        if total_dcom > 0:
            if total_dcom == 1 and counts["dcom"]["head"] == 0:
                return make_result('PASS', 'Perfect (Rule of 1)', 'DCOM')
            else:
                return make_result('WARN', f'Found {total_dcom} (Expected 1)', 'DCOM')

        if total_bundle > 0:
            if total_bundle == 2 and counts["bundle"]["head"] == 0:
                return make_result('PASS', 'Perfect (Rule of 2)', 'BUNDLE')
            elif total_bundle == 1:
                return make_result('WARN', 'Found 1 (Expected 2)', 'BUNDLE')
            else:
                return make_result('WARN', f'Found {total_bundle} (Expected 2)', 'BUNDLE')

        if total_std > 0:
            if detected_vendor == "DealerOn":
                if total_std == 1 and counts["std"]["head"] == 0:
                    return make_result('PASS', 'Perfect (DealerOn Rule of 1)', 'STD')
                else:
                    return make_result('WARN', f'Found {total_std} (DealerOn expects 1)', 'STD')

            if total_std == 2 and counts["std"]["head"] == 0:
                return make_result('PASS', 'Perfect (Rule of 2)', 'STD')
            elif total_std == 1:
                return make_result('WARN', 'Found 1 (Expected 2)', 'STD')
            else:
                return make_result('WARN', f'Found {total_std} (Expected 2)', 'STD')
        
        return make_result('WARN', 'Unknown Logic State', 'UNKNOWN')

    except Exception as e:
        return {'status': 'ERROR', 'msg': str(e), 'config': 'ERR', 'vendor': 'ERR'}


# --- 2. WORKER (Unchanged) ---
class BatchWorker(QThread):
    progress_signal = pyqtSignal(int)
    result_signal = pyqtSignal(int, dict) 
    finished_signal = pyqtSignal()

    def __init__(self, data_list):
        super().__init__()
        self.data_list = data_list
        self.is_running = True

    def run(self):
        RESTART_EVERY = 25
        driver = self.start_driver()
        total = len(self.data_list)

        for i, item in enumerate(self.data_list):
            if not self.is_running: break
            
            if i > 0 and i % RESTART_EVERY == 0:
                try: driver.quit()
                except: pass
                time.sleep(3)
                driver = self.start_driver()

            row_idx, client, url, original_idx = item 
            
            try:
                result = check_url_rules(driver, url)
            except Exception:
                try: driver.quit()
                except: pass
                driver = self.start_driver()
                result = {'status': 'ERROR', 'msg': 'Browser crashed/Recovered', 'config': 'ERR', 'vendor': 'ERR'}

            result['original_index'] = original_idx 
            self.result_signal.emit(row_idx, result)
            self.progress_signal.emit(int(((i + 1) / total) * 100))
            
            time.sleep(random.uniform(3, 6))

        try: driver.quit()
        except: pass
        self.finished_signal.emit()

    def start_driver(self):
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        # options.add_argument("--headless") 
        for attempt in range(3):
            try: return uc.Chrome(options=options)
            except: time.sleep(3)
        raise Exception("Could not launch Chrome")

    def stop(self):
        self.is_running = False


# --- 3. SCANNER WIDGET (Modernized) ---
class ScannerTab(QWidget):
    scan_update_signal = pyqtSignal(int, str, str, str, str)

    def __init__(self):
        super().__init__()
        self.worker = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Top Controls Frame
        top_frame = QFrame()
        top_frame.setObjectName("top_control_frame") # White Card Style
        
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(15, 15, 15, 15)
        top_layout.setSpacing(12)
        
        # Run Button (Primary Blue)
        self.btn_run = QPushButton(" Run Batch")
        self.btn_run.setObjectName("btn_primary") 
        self.btn_run.setIcon(qta.icon('fa5s.play', color='white'))
        self.btn_run.setEnabled(False)
        self.btn_run.clicked.connect(self.start_batch)

        # Stop Button (Danger Red)
        self.btn_stop = QPushButton(" Stop")
        self.btn_stop.setObjectName("btn_danger")
        self.btn_stop.setIcon(qta.icon('fa5s.stop', color='white'))
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_batch)

        # Export Button (Success Green)
        self.btn_export = QPushButton(" Export Report")
        self.btn_export.setObjectName("btn_success")
        self.btn_export.setIcon(qta.icon('fa5s.file-export', color='white'))
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self.export_report)
        
        top_layout.addWidget(self.btn_run)
        top_layout.addWidget(self.btn_stop)
        top_layout.addWidget(self.btn_export)
        layout.addWidget(top_frame)

        # Manual Check Input
        manual_layout = QHBoxLayout()
        self.input_manual = QLineEdit()
        self.input_manual.setPlaceholderText("Enter single URL for quick check...")
        
        # Manual Check Button (Primary Blue)
        self.btn_manual = QPushButton(" Check Single")
        self.btn_manual.setObjectName("btn_primary")
        self.btn_manual.setIcon(qta.icon('fa5s.search', color='white'))
        self.btn_manual.clicked.connect(self.run_manual_check)
        
        manual_layout.addWidget(self.input_manual)
        manual_layout.addWidget(self.btn_manual)
        layout.addLayout(manual_layout)

        # Progress Bar
        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        # Data Table
        self.table = QTableWidget()
        self.table.setColumnCount(7) 
        self.table.setHorizontalHeaderLabels(["Client Name", "URL", "Provider", "Config", "Status", "Details", "Active"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) 
        
        self.table.setColumnWidth(0, 180)
        self.table.setColumnWidth(2, 130)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 100)
        self.table.setSortingEnabled(True) # Enable sorting for UI
        
        layout.addWidget(self.table)

    def load_from_dataframe(self, df):
        if df is None or df.empty:
            self.table.setRowCount(0)
            self.btn_run.setEnabled(False)
            return

        self.table.setSortingEnabled(False) # Disable while loading
        self.table.setRowCount(0)
        row_count = 0
        
        for original_idx, row in df.iterrows():
            active_val = str(row.get('Active', 'Yes'))
            if active_val == "No":
                continue

            self.table.insertRow(row_count)
            
            full_url = str(row.get('URL', ''))
            display_url = full_url.replace("https://", "").replace("http://", "").rstrip("/")
            
            item_name = QTableWidgetItem(str(row.get('Client Name', '')))
            item_name.setData(Qt.ItemDataRole.UserRole, original_idx)
            
            self.table.setItem(row_count, 0, item_name)
            self.table.setItem(row_count, 1, QTableWidgetItem(display_url)) 
            self.table.setItem(row_count, 2, QTableWidgetItem(str(row.get('Provider', '')))) 
            self.table.setItem(row_count, 3, QTableWidgetItem(str(row.get('Config', '')))) 
            
            status_txt = str(row.get('Status', 'PENDING'))
            status_item = QTableWidgetItem(status_txt)
            status_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.color_status(status_item, status_txt)
            self.table.setItem(row_count, 4, status_item)
            
            self.table.setItem(row_count, 5, QTableWidgetItem(str(row.get('Details', ''))))
            self.table.setItem(row_count, 6, QTableWidgetItem(active_val))
            
            row_count += 1
            
        self.btn_run.setEnabled(True)
        self.btn_export.setEnabled(True)
        self.progress.setValue(0)
        self.table.setSortingEnabled(True) # Re-enable

    def color_status(self, item, status_txt):
        # Use Colors from styles.py
        if status_txt == 'PASS':
            item.setBackground(QColor(styles.COLORS["row_pass_bg"]))
            item.setForeground(QColor(styles.COLORS["row_pass_text"]))
        elif status_txt == 'WARN' or status_txt == 'BLOCKED':
            item.setBackground(QColor(styles.COLORS["row_warn_bg"]))
            item.setForeground(QColor(styles.COLORS["row_warn_text"]))
        elif status_txt == 'FAIL' or status_txt == 'ERROR':
            item.setBackground(QColor(styles.COLORS["row_fail_bg"]))
            item.setForeground(QColor(styles.COLORS["row_fail_text"]))
        elif status_txt == 'PENDING':
            item.setBackground(QColor(styles.COLORS["row_pending_bg"]))
            item.setForeground(QColor(styles.COLORS["row_pending_text"]))
        else:
            item.setBackground(QColor(styles.COLORS["row_pending_bg"]))

    def start_batch(self):
        if self.worker is not None and self.worker.isRunning(): return
        
        # Disable sorting so rows don't jump around during scan
        self.table.setSortingEnabled(False)

        data_payload = []
        for i in range(self.table.rowCount()):
            status_item = self.table.item(i, 4)
            if status_item and status_item.text() in ["PASS", "WARN", "FAIL", "ERROR", "BLOCKED"]:
                continue
            
            item_name = self.table.item(i, 0)
            original_idx = item_name.data(Qt.ItemDataRole.UserRole)

            raw_url = self.table.item(i, 1).text().strip()
            if not raw_url.lower().startswith(("http://", "https://")):
                url = "https://" + raw_url
            else:
                url = raw_url

            client = item_name.text()
            data_payload.append((i, client, url, original_idx))

        if not data_payload:
            QMessageBox.information(self, "Info", "No valid PENDING items to scan.")
            self.table.setSortingEnabled(True) # Re-enable if we aren't running
            return

        self.worker = BatchWorker(data_payload)
        self.worker.progress_signal.connect(self.progress.setValue)
        self.worker.result_signal.connect(self.update_row)
        self.worker.finished_signal.connect(self.batch_finished)
        
        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.worker.start()

    def stop_batch(self):
        if self.worker:
            self.worker.stop()
            self.btn_stop.setText("Stopping...")

    def batch_finished(self):
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setText(" Stop") # Reset text
        
        # Re-enable sorting now that scan is done
        self.table.setSortingEnabled(True)
        
        QMessageBox.information(self, "Done", "Batch Scan Complete!")

    def update_row(self, row_idx, result):
        # Update Local Table
        self.table.setItem(row_idx, 2, QTableWidgetItem(result.get('vendor', 'Unknown')))
        self.table.setItem(row_idx, 3, QTableWidgetItem(result['config']))
        
        status_item = QTableWidgetItem(result['status'])
        status_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.color_status(status_item, result['status'])
        
        self.table.setItem(row_idx, 4, status_item)
        self.table.setItem(row_idx, 5, QTableWidgetItem(result['msg']))
        self.table.scrollToItem(status_item)

        # Emit Signal to Main Window
        original_idx = result.get('original_index')
        if original_idx is not None:
            self.scan_update_signal.emit(
                original_idx, 
                result['status'], 
                result['msg'], 
                result.get('vendor', ''), 
                result['config']
            )

    def run_manual_check(self):
        url = self.input_manual.text().strip()
        if not url: return
        
        if not url.startswith("http"): full_url = "https://" + url
        else: full_url = url
            
        display_url = full_url.replace("https://", "").replace("http://", "").rstrip("/")
        
        # Insert row at top
        self.table.insertRow(0)
        self.table.setItem(0, 0, QTableWidgetItem("Manual Check"))
        self.table.setItem(0, 1, QTableWidgetItem(display_url)) 
        self.table.setItem(0, 4, QTableWidgetItem("CHECKING..."))
        
        self.worker = BatchWorker([(0, "Manual", full_url, None)])
        self.worker.result_signal.connect(self.update_row)
        self.worker.start()

    def export_report(self):
        timestamp = time.strftime("%Y-%m-%d_%H-%M")
        default_name = f"scan_report_{timestamp}.csv"

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Report", default_name, "CSV Files (*.csv)")
        if not file_path: return
        
        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
                writer.writerow(headers)
                for row in range(self.table.rowCount()):
                    row_data = []
                    for col in range(self.table.columnCount()):
                        item = self.table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            QMessageBox.information(self, "Success", f"Report saved to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))