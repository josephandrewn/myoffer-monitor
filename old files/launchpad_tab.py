import sys
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QComboBox, QLabel, QFrame, QMessageBox)
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings, QWebEngineProfile
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, pyqtSignal
import qtawesome as qta
import styles

# --- CUSTOM PAGE TO HANDLE ERRORS ---
class CustomWebPage(QWebEnginePage):
    def certificateError(self, error):
        # Ignore SSL/Certificate errors (prevents some blocking)
        return True

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        # Log JS errors to console but prevent them from crashing the app
        # "Integrity" errors usually show up here.
        if "integrity" in message:
            print(f"[Ignored SRI Error]: {message}")
        else:
            print(f"JS Console: {message}")

class LaunchpadTab(QWidget):
    def __init__(self):
        super().__init__()
        self.clients_data = [] 

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # --- Toolbar ---
        toolbar = QFrame()
        toolbar.setStyleSheet(f"background: {styles.COLORS['bg_white']}; border-bottom: 1px solid {styles.COLORS['border']};")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(10, 10, 10, 10)
        
        # Client Selector
        tb_layout.addWidget(QLabel("Select Client:"))
        self.combo_clients = QComboBox()
        self.combo_clients.setMinimumWidth(250)
        tb_layout.addWidget(self.combo_clients)
        
        # Load URL Button
        self.btn_go = QPushButton(" Open Launch Form")
        self.btn_go.setIcon(qta.icon('fa5s.external-link-alt', color='#555'))
        self.btn_go.clicked.connect(self.load_target_url)
        tb_layout.addWidget(self.btn_go)
        
        tb_layout.addStretch()
        
        # Auto-Fill Button
        self.btn_fill = QPushButton(" ✨ Auto-Fill Form")
        self.btn_fill.setObjectName("btn_primary")
        self.btn_fill.setIcon(qta.icon('fa5s.magic', color='white'))
        self.btn_fill.clicked.connect(self.inject_form_data)
        tb_layout.addWidget(self.btn_fill)

        # Add this near your other buttons in __init__
        self.btn_force = QPushButton(" Force JS Nav")
        self.btn_force.clicked.connect(self.force_js_redirect)
        tb_layout.addWidget(self.btn_force)
        
        layout.addWidget(toolbar)
        
        # --- Web Browser Setup ---
        # Create a profile that ignores cache to avoid stale SRI hashes
        profile = QWebEngineProfile("MyOfferProfile", self)
        profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.NoCache)
        
        self.browser = QWebEngineView()
        
        # USE CUSTOM PAGE
        self.page = CustomWebPage(profile, self.browser)
        self.browser.setPage(self.page)
        
        # Set User Agent to standard Chrome to avoid "unsupported browser" warnings
        profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.browser.setHtml("<h2 style='text-align:center; color:#555; margin-top:50px;'>Select a Client and Click 'Open Launch Form'</h2>")
        layout.addWidget(self.browser)
        
        self.target_url = "https://pureinfluencer.idrove.it/app/launch-request"

    def refresh_client_list(self, df):
        self.combo_clients.clear()
        self.clients_data = []
        if df is None or df.empty: return

        for index, row in df.iterrows():
            name = str(row.get("Client Name", "Unknown"))
            self.clients_data.append(row)
            self.combo_clients.addItem(name)

    def load_target_url(self):
        # 1. Force the URL into the browser
        url = QUrl(self.target_url)
        self.browser.setUrl(url)
        
        # 2. OPTIONAL: If the site fights back, we can execute JS to force the router
        # But usually, setUrl() is enough if we are logged in.
        print(f"Navigating to: {self.target_url}")

    def inject_form_data(self):
        idx = self.combo_clients.currentIndex()
        if idx < 0 or idx >= len(self.clients_data): return
        data = self.clients_data[idx]
        
        website = data.get("URL", "").replace("https://", "").replace("http://", "").strip("/")
        full_website = data.get("URL", "")
        primary_name = data.get("Primary Name", "")
        primary_email = data.get("Primary Email", "")
        gm_name = data.get("GM Name", "")
        gm_email = data.get("GM Email", "")
        lead_email = data.get("Lead Email", "")
        crm_email = data.get("CRM Email", "")
        
        js_code = f"""
        (function() {{
            function setVal(selector, value) {{
                let el = document.querySelector(selector);
                if (el) {{
                    el.value = value;
                    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    el.style.backgroundColor = '#e8f0fe'; 
                }}
            }}
            
            // Try IDroveIt specific names based on standard forms
            setVal('input[name="businessName"]', '{data.get("Client Name", "")}');
            setVal('input[name="websiteUrl"]', '{full_website}');
            
            setVal('input[name="primaryContactName"]', '{primary_name}');
            setVal('input[name="primaryContactEmail"]', '{primary_email}');
            
            setVal('input[name="generalManagerName"]', '{gm_name}');
            setVal('input[name="generalManagerEmail"]', '{gm_email}');
            
            setVal('input[name="crmEmail"]', '{crm_email}');
            
            return "Done";
        }})();
        """
        self.browser.page().runJavaScript(js_code)
    def force_js_redirect(self):
        # This tells the website's internal window to go there, bypassing some router logic
        js = f"window.location.href = '{self.target_url}';"
        self.browser.page().runJavaScript(js)