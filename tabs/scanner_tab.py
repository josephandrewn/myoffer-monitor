import sys
import time
import csv
import random
import os 
import re 
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Set
import json
import pandas as pd
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import qtawesome as qta 
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QFileDialog, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLabel, QProgressBar, QLineEdit, 
                             QMessageBox, QFrame)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QColor, QFont

import assets.styles as styles 

from config import scanner_config, VENDOR_DETECTION_RULES, BLOCK_DETECTION_PHRASES
from logger import get_logger, LogExecutionTime

logger = get_logger(__name__)

# --- 1. LOGIC & HELPERS ---

# ============================================================================
# BLOCK TRACKER - Manages UNVERIFIABLE status
# ============================================================================

class BlockTracker:
    """
    Tracks blocked sites and determines when they should be marked UNVERIFIABLE.
    Persists data to JSON so it survives app restarts.
    """
    
    BLOCK_THRESHOLD = 3  # Consecutive blocks before UNVERIFIABLE
    HISTORY_DAYS = 7     # Only count blocks within this window
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.history_file = os.path.join(data_dir, "block_history.json")
        self.block_history: Dict[str, List[str]] = {}
        self.known_unverifiable: Set[str] = set()
        self._load()
    
    def _get_domain(self, url: str) -> str:
        """Extract clean domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return url.lower()
    
    def _load(self):
        """Load block history from disk."""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    self.block_history = data.get('history', {})
                    self.known_unverifiable = set(data.get('unverifiable', []))
                    if self.known_unverifiable:
                        print(f"📋 Loaded {len(self.known_unverifiable)} unverifiable sites from history")
        except Exception as e:
            print(f"Warning: Could not load block history: {e}")
            self.block_history = {}
            self.known_unverifiable = set()
    
    def _save(self):
        """Save block history to disk."""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.history_file, 'w') as f:
                json.dump({
                    'history': self.block_history,
                    'unverifiable': sorted(list(self.known_unverifiable)),
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save block history: {e}")
    
    def is_unverifiable(self, url: str) -> bool:
        """Check if a site is marked as unverifiable."""
        domain = self._get_domain(url)
        return domain in self.known_unverifiable
    
    def get_block_count(self, url: str) -> int:
        """Get the current block count for a site."""
        domain = self._get_domain(url)
        if domain not in self.block_history:
            return 0
        cutoff = (datetime.now() - timedelta(days=self.HISTORY_DAYS)).isoformat()
        recent = [t for t in self.block_history[domain] if t > cutoff]
        return len(recent)
    
    def record_block(self, url: str) -> tuple:
        """
        Record a block event. 
        Returns: (consecutive_count, is_now_unverifiable)
        """
        domain = self._get_domain(url)
        now = datetime.now()
        
        if domain not in self.block_history:
            self.block_history[domain] = []
        
        cutoff = (now - timedelta(days=self.HISTORY_DAYS)).isoformat()
        self.block_history[domain] = [
            t for t in self.block_history[domain] if t > cutoff
        ]
        
        self.block_history[domain].append(now.isoformat())
        consecutive = len(self.block_history[domain])
        is_unverifiable = consecutive >= self.BLOCK_THRESHOLD
        
        if is_unverifiable and domain not in self.known_unverifiable:
            self.known_unverifiable.add(domain)
            print(f"⚠️  {domain} marked UNVERIFIABLE after {consecutive} blocks")
        
        self._save()
        return consecutive, is_unverifiable
    
    def record_success(self, url: str):
        """Record a successful scan - clears block history for domain."""
        domain = self._get_domain(url)
        changed = False
        
        if domain in self.block_history:
            del self.block_history[domain]
            changed = True
        
        if domain in self.known_unverifiable:
            self.known_unverifiable.remove(domain)
            print(f"✓ {domain} removed from UNVERIFIABLE (successful scan)")
            changed = True
        
        if changed:
            self._save()
    
    def reset_site(self, url: str):
        """Reset a site's unverifiable status for re-testing."""
        domain = self._get_domain(url)
        changed = False
        
        if domain in self.known_unverifiable:
            self.known_unverifiable.remove(domain)
            changed = True
        
        if domain in self.block_history:
            del self.block_history[domain]
            changed = True
        
        if changed:
            print(f"↻ {domain} reset for re-scanning")
            self._save()
    
    def get_unverifiable_domains(self) -> List[str]:
        """Get list of all unverifiable domains."""
        return sorted(list(self.known_unverifiable))


# ============================================================================
# QUICK HTTP CHECK - Tier 1 scanning (no browser needed)
# ============================================================================

def quick_http_check(url: str) -> Optional[dict]:
    """
    Tier 1: Quick HTTP request to check for script in raw HTML.
    
    Returns:
        - dict with status info if conclusive
        - None if inconclusive (needs browser check)
    """
    SCRIPT_SIGNATURES = [
        'idrove.it/behaviour.spa.js',
        'idrove.it/behaviour.dcom.js',
        'idrove.it/behaviour.bundle.js',
        'idrove.it/behaviour.js',
        'idrove.it/behaviour',
    ]
    
    BOT_DETECTION_PHRASES = [
        'checking your browser',
        'please enable javascript',
        'captcha',
        'access denied',
        'bot detected',
        'security check',
        'please wait while we verify',
        'ray id',
        'cf-browser-verification',
        'challenge-platform',
        'ddos protection',
        'pardon our interruption',
        'just a moment',
        'attention required',
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        
        if response.status_code == 403:
            return None  # Blocked - need browser
        
        if response.status_code >= 400:
            return {
                'status': 'FAIL',
                'vendor': 'HTTP Error',
                'config': 'ERR',
                'msg': f'Status code: {response.status_code}',
                'method': 'http_quick'
            }
        
        html = response.text
        html_lower = html.lower()
        
        # Check for bot detection
        for phrase in BOT_DETECTION_PHRASES:
            if phrase in html_lower:
                return None  # Bot detection present - need browser
        
        # Check for our script signatures
        for sig in SCRIPT_SIGNATURES:
            if sig.lower() in html_lower:
                # Determine config type
                if 'spa.js' in sig:
                    config = 'SPA'
                elif 'dcom.js' in sig:
                    config = 'DCOM'
                elif 'bundle.js' in sig:
                    config = 'BUNDLE'
                else:
                    config = 'STD'
                
                return {
                    'status': 'PASS',
                    'vendor': 'Quick HTTP',
                    'config': config,
                    'msg': f'Found via HTTP: {sig}',
                    'method': 'http_quick'
                }
        
        # Script not found - might be loaded via JS, need browser
        return None
        
    except requests.Timeout:
        # Timeout could mean slow site or protection - try browser
        return None
    except requests.exceptions.SSLError:
        return {
            'status': 'FAIL',
            'vendor': 'SSL Error',
            'config': 'ERR',
            'msg': 'SSL certificate verification failed',
            'method': 'http_quick'
        }
    except requests.exceptions.ConnectionError as e:
        error_str = str(e).lower()
        # DNS failures and connection refused are definite FAILs
        if 'name or service not known' in error_str or 'getaddrinfo failed' in error_str:
            return {
                'status': 'FAIL',
                'vendor': 'DNS Error',
                'config': 'ERR',
                'msg': 'Domain does not resolve',
                'method': 'http_quick'
            }
        if 'connection refused' in error_str:
            return {
                'status': 'FAIL',
                'vendor': 'Connection Refused',
                'config': 'ERR',
                'msg': 'Server refused connection',
                'method': 'http_quick'
            }
        if 'no route to host' in error_str or 'network is unreachable' in error_str:
            return {
                'status': 'FAIL',
                'vendor': 'Network Error',
                'config': 'ERR',
                'msg': 'Site unreachable',
                'method': 'http_quick'
            }
        return None  # Other connection errors - try browser
    except Exception:
        return None


# ============================================================================
# SITES THAT REQUIRE SESSION WARMING
# ============================================================================

PROBLEMATIC_SITES = [
    # Security providers
    'cloudflare',
    'imperva',
    'incapsula',
    'perimeter',
    'distil',
    
    # High-volume dealer groups
    'lithia.com',
    'autonation.com',
    'carmax.com',
    'penske',
    'asbury',
    
    # Specific vendors known for strict security
    'dealer.com',
    'dealertrack',
    'audinorthlake.com',
    'audisouthaustin.com',
    'audiusa',
]

def needs_session_warming(url):
    """Check if a URL needs session warming based on known problematic patterns."""
    url_lower = url.lower()
    for pattern in PROBLEMATIC_SITES:
        if pattern in url_lower:
            return True
    return False


def warm_up_session(driver, target_url):
    """
    Visits the homepage before going to the target page.
    This makes the visit look more natural and less bot-like.
    """
    from urllib.parse import urlparse
    
    try:
        parsed = urlparse(target_url)
        homepage = f"{parsed.scheme}://{parsed.netloc}"
        
        print(f"    → Warming session: visiting {homepage}")
        driver.get(homepage)
        delay = random.uniform(4, 8)
        time.sleep(delay)
        
        try:
            driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(0.5)
        except:
            pass
        
        print(f"    → Session warmed, now visiting target page")
        
    except Exception as e:
        print(f"    ⚠ Session warming failed (continuing anyway): {e}")


def save_evidence_screenshot(driver, client_name, status):
    """Takes a screenshot of the current browser state."""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        base_folder = os.path.join(os.getcwd(), "scans", today)
        if not os.path.exists(base_folder):
            os.makedirs(base_folder)

        safe_name = re.sub(r'[\\/*?:"<>|]', "", client_name)
        safe_name = safe_name.replace(" ", "_")
        
        filename = f"{status}_{safe_name}.png"
        full_path = os.path.join(base_folder, filename)
        
        driver.save_screenshot(full_path)
        return True
    except Exception as e:
        logger.error("Screenshot failed", exception=e, client=client_name)
        return False


def detect_provider(soup):
    text_content = soup.get_text().lower()
    html_str = str(soup).lower()
    
    # --- SOKAL ---
    if "sokal.com" in html_str: return "Sokal"
    if "go-sokal" in html_str: return "Sokal"
    if "powered by sokal" in text_content: return "Sokal"
    if "sokal_assets" in html_str: return "Sokal"

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
    
    # --- BLOCK PAGES ---
    if "imperva" in html_str or "_incapsula_" in html_str: return "Security Block (Imperva)"
    if "cloudflare" in html_str: return "Security Block (Cloudflare)"

    return "Other"


def check_url_rules(driver, url, client_name):
    """
    Double-Tap Logic with Updated Rules for Dealer.com
    """
    TARGET_SPA    = "idrove.it/behaviour.spa.js"      
    TARGET_DCOM   = "idrove.it/behaviour.dcom.js"     
    TARGET_STD    = "idrove.it/behaviour.js"          
    TARGET_BUNDLE = "idrove.it/behaviour.bundle.js" 
    BASE_TARGET   = "idrove.it/behaviour"
    
    MAX_WAIT_TIME = 15 
    SETTLE_TIME = 3
    MAX_ATTEMPTS = 2
    
    with LogExecutionTime(logger, "url_scan", url=url, client=client_name):
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                # Check if this site needs special treatment
                use_warming = needs_session_warming(url)
                if use_warming:
                    print(f"  [WARMING] {client_name} - site requires session warming")
                    warm_up_session(driver, url)
                else:
                    print(f"  [DIRECT] {client_name} - direct access")

                # Now load the actual target page
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

                # --- 1. BLOCK CHECK ---
                block_phrases = [
                    "detected unusual activity", "unusual activity from your ip",
                    "verify you are a human", "verify you are human",
                    "access denied", "security challenge", "please enable cookies",
                    "captcha-delivery", "challenge-platform", "just a moment...",
                    "attention required", "cloudflare"
                ]
                
                is_blocked_text = any(phrase in text_content for phrase in block_phrases)
                is_blocked_title = any(phrase in title_tag for phrase in block_phrases)
                is_blocked_vendor = "Security Block" in detected_vendor
                
                scan_status = "UNKNOWN"
                scan_msg = ""
                scan_config = "NONE"

                if (is_blocked_text or is_blocked_title or is_blocked_vendor) and BASE_TARGET not in html_str:
                    scan_status = 'BLOCKED'
                    scan_msg = 'Bot Detection / CAPTCHA'
                    scan_config = 'ERR'
                    detected_vendor = "Security Block"
                else:
                    # Standard Scan
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
                    
                    # --- LOGIC RULES ---
                    if total_std == 0 and total_dcom == 0 and total_spa == 0 and total_bundle == 0:
                        scan_status, scan_msg, scan_config = 'FAIL', 'No scripts found', 'NONE'
                    
                    elif total_spa > 0:
                        scan_config = 'SPA'
                        if total_spa == 4 and counts["spa"]["head"] == 0: scan_status, scan_msg = 'PASS', 'Perfect (Rule of 4)'
                        else: scan_status, scan_msg = 'WARN', f'Found {total_spa} (Expected 4)'
                    
                    elif total_dcom > 0:
                        scan_config = 'DCOM'
                        if total_dcom == 1 and counts["dcom"]["head"] == 0: scan_status, scan_msg = 'PASS', 'Perfect (Rule of 1)'
                        else: scan_status, scan_msg = 'WARN', f'Found {total_dcom} (Expected 1)'
                    
                    elif total_bundle > 0:
                        scan_config = 'BUNDLE'
                        if total_bundle == 2 and counts["bundle"]["head"] == 0: scan_status, scan_msg = 'PASS', 'Perfect (Rule of 2)'
                        else: scan_status, scan_msg = 'WARN', f'Found {total_bundle} (Expected 2)'
                    
                    elif total_std > 0:
                        scan_config = 'STD'
                        if detected_vendor in ["DealerOn", "Dealer.com"]:
                            if total_std == 1 and counts["std"]["head"] == 0: 
                                scan_status, scan_msg = 'PASS', f'Perfect ({detected_vendor} Rule of 1)'
                            else: 
                                scan_status, scan_msg = 'WARN', f'Found {total_std} ({detected_vendor} expects 1)'
                        else:
                            if total_std == 2 and counts["std"]["head"] == 0: 
                                scan_status, scan_msg = 'PASS', 'Perfect (Rule of 2)'
                            else: 
                                scan_status, scan_msg = 'WARN', f'Found {total_std} (Expected 2)'

                if scan_status == 'PASS':
                    return {
                        'status': scan_status, 
                        'msg': scan_msg, 
                        'config': scan_config, 
                        'vendor': detected_vendor
                    }
                
                if attempt < MAX_ATTEMPTS:
                    print(f"Attempt {attempt} failed ({scan_status}). Retrying...")
                    error_delay = random.uniform(3, 8)
                    time.sleep(error_delay)
                    continue
                
                save_evidence_screenshot(driver, client_name, scan_status)
                scan_msg += " (Saved Img)"

                logger.scan_result(
                    client=client_name,
                    url=url,
                    status=scan_status,
                    vendor=detected_vendor,
                    config=scan_config,
                    details=scan_msg
                )
                
                return {
                    'status': scan_status, 
                    'msg': scan_msg, 
                    'config': scan_config, 
                    'vendor': detected_vendor
                }

            except Exception as e:
                error_msg = str(e).lower()
                
                # Check if this is a "site unreachable" type error that should be FAIL, not ERROR
                fail_indicators = [
                    'timeout', 'timed out',
                    'err_connection', 'connection refused',
                    'err_name_not_resolved', 'dns',
                    'net::err_', 'neterror',
                    'ssl', 'certificate',
                    'unreachable', 'no such host',
                ]
                
                is_site_issue = any(indicator in error_msg for indicator in fail_indicators)
                
                if attempt < MAX_ATTEMPTS:
                    error_delay = random.uniform(3, 8)
                    time.sleep(error_delay)
                    continue
                
                # If it's a site issue, return FAIL (site problem), not ERROR (scanner problem)
                if is_site_issue:
                    return {
                        'status': 'FAIL', 
                        'msg': f'Site unreachable: {str(e)[:100]}', 
                        'config': 'ERR', 
                        'vendor': 'Unreachable'
                    }
                else:
                    return {
                        'status': 'ERROR', 
                        'msg': str(e)[:100], 
                        'config': 'ERR', 
                        'vendor': 'ERR'
                    }
        pass


# ============================================================================
# HUMAN DELAY SIMULATION
# ============================================================================

def human_delay(base_seconds=3):
    """Simulates realistic human delay patterns."""
    rand = random.random()
    
    if rand < 0.70:
        delay = random.uniform(2.0, 5.0)
    elif rand < 0.90:
        delay = random.uniform(0.5, 2.0)
    else:
        delay = random.uniform(5.0, 15.0)
    
    time.sleep(delay)
    return delay


# --- 2. WORKER (With Tiered Scanning) ---
class BatchWorker(QThread):
    progress_signal = pyqtSignal(int)
    result_signal = pyqtSignal(int, dict) 
    finished_signal = pyqtSignal()

    def __init__(self, data_list, block_tracker: BlockTracker = None):
        super().__init__()
        self.data_list = data_list
        self.is_running = True
        self.block_tracker = block_tracker

    def run(self):
        """
        Two-phase scanning:
        Phase 1: Quick HTTP checks (no browser)
        Phase 2: Browser scans for sites that need it
        """
        RESTART_EVERY = 3
        total = len(self.data_list)
        sites_needing_browser = []
        completed = 0
        
        # ================================================================
        # PHASE 1: Quick HTTP checks (fast, no browser needed)
        # ================================================================
        print("\n" + "=" * 60)
        print("PHASE 1: Quick HTTP Checks")
        print("=" * 60)
        
        for item in self.data_list:
            if not self.is_running:
                break
            
            row_idx, client, url, original_idx = item
            
            # Check if UNVERIFIABLE (skip entirely)
            if self.block_tracker and self.block_tracker.is_unverifiable(url):
                result = {
                    'status': 'UNVERIFIABLE',
                    'vendor': 'Manual Required',
                    'config': 'N/A',
                    'msg': 'Site blocks automation. Manual check required.',
                    'original_index': original_idx
                }
                self.result_signal.emit(row_idx, result)
                completed += 1
                self.progress_signal.emit(int((completed / total) * 100))
                print(f"  [SKIP] {client} - UNVERIFIABLE")
                continue
            
            # Try quick HTTP check
            quick_result = quick_http_check(url)
            
            if quick_result is not None:
                # Got conclusive result without browser!
                quick_result['original_index'] = original_idx
                
                if quick_result['status'] == 'PASS' and self.block_tracker:
                    self.block_tracker.record_success(url)
                
                self.result_signal.emit(row_idx, quick_result)
                completed += 1
                self.progress_signal.emit(int((completed / total) * 100))
                print(f"  [QUICK] {client} - {quick_result['status']}")
            else:
                # Needs browser scan
                sites_needing_browser.append(item)
                print(f"  [QUEUE] {client} - needs browser")
        
        # ================================================================
        # PHASE 2: Browser scans (only for sites that need it)
        # ================================================================
        if sites_needing_browser and self.is_running:
            print("\n" + "=" * 60)
            print(f"PHASE 2: Browser Scans ({len(sites_needing_browser)} sites)")
            print("=" * 60)
            
            driver = self.start_driver()
            browser_count = 0
            
            for item in sites_needing_browser:
                if not self.is_running:
                    break
                
                row_idx, client, url, original_idx = item
                
                # Restart browser periodically
                if browser_count > 0 and browser_count % RESTART_EVERY == 0:
                    try:
                        driver.quit()
                    except:
                        pass
                    time.sleep(3)
                    driver = self.start_driver()
                
                try:
                    result = check_url_rules(driver, url, client)
                except Exception as e:
                    try:
                        driver.quit()
                    except:
                        pass
                    driver = self.start_driver()
                    result = {'status': 'ERROR', 'msg': 'Browser crashed/Recovered', 'config': 'ERR', 'vendor': 'ERR'}
                
                # Handle BLOCKED with escalation to UNVERIFIABLE
                if result.get('status') == 'BLOCKED' and self.block_tracker:
                    count, is_unverifiable = self.block_tracker.record_block(url)
                    
                    if is_unverifiable:
                        result = {
                            'status': 'UNVERIFIABLE',
                            'vendor': 'Persistent Block',
                            'config': 'N/A',
                            'msg': f'Blocked {count}x. Manual verification required.'
                        }
                        print(f"  [UNVERIFIABLE] {client} - escalated after {count} blocks")
                    else:
                        result['msg'] = f"{result.get('msg', '')} ({count}/{BlockTracker.BLOCK_THRESHOLD})"
                        print(f"  [BLOCKED] {client} - {count}/{BlockTracker.BLOCK_THRESHOLD}")
                
                elif result.get('status') == 'PASS':
                    if self.block_tracker:
                        self.block_tracker.record_success(url)
                    print(f"  [PASS] {client}")
                
                else:
                    print(f"  [{result.get('status')}] {client}")
                
                result['original_index'] = original_idx
                self.result_signal.emit(row_idx, result)
                completed += 1
                self.progress_signal.emit(int((completed / total) * 100))
                
                browser_count += 1
                
                # Human delay between scans
                if self.is_running:
                    human_delay()
            
            try:
                driver.quit()
            except:
                pass
        
        print("\n" + "=" * 60)
        print("SCAN COMPLETE")
        print("=" * 60)
        
        self.finished_signal.emit()

    def start_driver(self):
        """Creates a stealthy browser instance with randomized fingerprints."""
        last_err = None
        
        for attempt in range(3):
            try: 
                options = uc.ChromeOptions()
                
                # Randomize User Agent
                user_agents = [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                ]
                chosen_ua = random.choice(user_agents)
                options.add_argument(f'--user-agent={chosen_ua}')
                
                # Randomize Window Size
                window_sizes = [
                    (1920, 1080),
                    (1366, 768),
                    (1440, 900),
                    (1536, 864),
                    (1280, 720),
                ]
                width, height = random.choice(window_sizes)
                options.add_argument(f'--window-size={width},{height}')
                
                # Randomize Language
                languages = ['en-US,en', 'en-GB,en', 'en-CA,en']
                options.add_argument(f'--accept-lang={random.choice(languages)}')
                
                # Anti-Detection Arguments
                options.add_argument('--disable-blink-features=AutomationControlled')
                
                # Stability Arguments
                options.add_argument("--disable-popup-blocking")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument("--disable-extensions")
                options.add_argument("--disable-notifications")
                
                # Create Driver
                driver = uc.Chrome(options=options, version_main=144)
                
                # Advanced Stealth (JavaScript Injection)
                driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                    'source': '''
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [1, 2, 3, 4, 5]
                        });
                        Object.defineProperty(navigator, 'languages', {
                            get: () => ['en-US', 'en']
                        });
                        window.chrome = {
                            runtime: {}
                        };
                        const originalQuery = window.navigator.permissions.query;
                        window.navigator.permissions.query = (parameters) => (
                            parameters.name === 'notifications' ?
                                Promise.resolve({ state: Notification.permission }) :
                                originalQuery(parameters)
                        );
                    '''
                })
                
                driver.set_page_load_timeout(30)
                
                print(f"✓ Browser started (UA: {chosen_ua[:50]}..., Size: {width}x{height})")
                return driver
                
            except Exception as e:
                last_err = e
                print(f"Browser start attempt {attempt + 1} failed: {e}")
                time.sleep(2)
        
        raise Exception(f"Failed to start browser after 3 attempts: {last_err}")

    def stop(self):
        self.is_running = False


# --- 3. SCANNER WIDGET ---
class ScannerTab(QWidget):
    scan_update_signal = pyqtSignal(int, str, str, str, str)

    def __init__(self):
        super().__init__()
        self.worker = None
        
        # Initialize block tracker for UNVERIFIABLE status
        self.block_tracker = BlockTracker(data_dir="data")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Top Controls Frame
        top_frame = QFrame()
        top_frame.setObjectName("top_control_frame") 
        
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(15, 15, 15, 15)
        top_layout.setSpacing(12)
        
        self.btn_run = QPushButton(" Run Batch")
        self.btn_run.setObjectName("btn_primary") 
        self.btn_run.setIcon(qta.icon('fa5s.play', color='white'))
        self.btn_run.setEnabled(False)
        self.btn_run.clicked.connect(self.start_batch)

        self.btn_stop = QPushButton(" Stop")
        self.btn_stop.setObjectName("btn_danger")
        self.btn_stop.setIcon(qta.icon('fa5s.stop', color='white'))
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_batch)

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
        self.table.setSortingEnabled(True) 
        
        layout.addWidget(self.table)

    def load_from_dataframe(self, df):
        if df is None or df.empty:
            self.table.setRowCount(0)
            self.btn_run.setEnabled(False)
            return

        self.table.setSortingEnabled(False)
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
        self.table.setSortingEnabled(True)

    def color_status(self, item, status_txt):
        """Apply color coding to status cells."""
        # Map UNVERIFIABLE to display as "N/A" for better fit
        display_text = "N/A" if status_txt == 'UNVERIFIABLE' else status_txt
        item.setText(display_text)
        
        if status_txt == 'PASS':
            item.setBackground(QColor(styles.COLORS["row_pass_bg"]))
            item.setForeground(QColor(styles.COLORS["row_pass_text"]))
        elif status_txt == 'WARN' or status_txt == 'BLOCKED':
            item.setBackground(QColor(styles.COLORS["row_warn_bg"]))
            item.setForeground(QColor(styles.COLORS["row_warn_text"]))
        elif status_txt == 'FAIL' or status_txt == 'ERROR':
            item.setBackground(QColor(styles.COLORS["row_fail_bg"]))
            item.setForeground(QColor(styles.COLORS["row_fail_text"]))
        elif status_txt == 'UNVERIFIABLE':
            item.setBackground(QColor(styles.COLORS["row_unverifiable_bg"]))
            item.setForeground(QColor(styles.COLORS["row_unverifiable_text"]))
        elif status_txt == 'PENDING':
            item.setBackground(QColor(styles.COLORS["row_pending_bg"]))
            item.setForeground(QColor(styles.COLORS["row_pending_text"]))
        else:
            item.setBackground(QColor(styles.COLORS["row_pending_bg"]))

    def start_batch(self):
        if self.worker is not None and self.worker.isRunning():
            return
        
        self.table.setSortingEnabled(False)

        data_payload = []
        for i in range(self.table.rowCount()):
            status_item = self.table.item(i, 4)
            status_text = status_item.text() if status_item else ""
            
            # FILTER: Only scan PENDING items
            # Skip PASS, FAIL, WARN, BLOCKED, ERROR, UNVERIFIABLE (displayed as N/A)
            if status_text != "PENDING" and status_text != "" and status_text != "N/A":
                continue
            
            # Also skip N/A (UNVERIFIABLE) items
            if status_text == "N/A":
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
            QMessageBox.information(self, "Info", "No PENDING items to scan.")
            self.table.setSortingEnabled(True)
            return

        # Pass block_tracker to worker for tiered scanning
        self.worker = BatchWorker(data_payload, block_tracker=self.block_tracker)
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
        self.btn_stop.setText(" Stop") 
        self.table.setSortingEnabled(True)
        
        # Show summary with UNVERIFIABLE count (displayed as N/A)
        unverifiable_count = sum(
            1 for i in range(self.table.rowCount())
            if self.table.item(i, 4) and self.table.item(i, 4).text() == 'N/A'
        )
        
        if unverifiable_count > 0:
            QMessageBox.information(
                self, 
                "Done", 
                f"Batch Scan Complete!\n\n"
                f"🟠 {unverifiable_count} site(s) marked N/A (unverifiable).\n"
                f"These require manual verification."
            )
        else:
            QMessageBox.information(self, "Done", "Batch Scan Complete!")

    def update_row(self, row_idx, result):
        self.table.setItem(row_idx, 2, QTableWidgetItem(result.get('vendor', 'Unknown')))
        self.table.setItem(row_idx, 3, QTableWidgetItem(result['config']))
        
        status_item = QTableWidgetItem(result['status'])
        status_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.color_status(status_item, result['status'])
        
        self.table.setItem(row_idx, 4, status_item)
        self.table.setItem(row_idx, 5, QTableWidgetItem(result['msg']))
        self.table.scrollToItem(status_item)

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
        if not url:
            return
        
        if not url.startswith("http"):
            full_url = "https://" + url
        else:
            full_url = url
            
        display_url = full_url.replace("https://", "").replace("http://", "").rstrip("/")
        
        self.table.insertRow(0)
        self.table.setItem(0, 0, QTableWidgetItem("Manual Check"))
        self.table.setItem(0, 1, QTableWidgetItem(display_url)) 
        self.table.setItem(0, 4, QTableWidgetItem("CHECKING..."))
        
        self.worker = BatchWorker([(0, "Manual", full_url, None)], block_tracker=self.block_tracker)
        self.worker.result_signal.connect(self.update_row)
        self.worker.start()

    def export_report(self):
        timestamp = time.strftime("%Y-%m-%d_%H-%M")
        default_name = f"scan_report_{timestamp}.csv"

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Report", default_name, "CSV Files (*.csv)")
        if not file_path:
            return
        
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
    
    def reset_unverifiable_site(self, url: str):
        """Reset a site's UNVERIFIABLE status for re-scanning."""
        self.block_tracker.reset_site(url)
    
    def get_unverifiable_sites(self) -> List[str]:
        """Get list of all domains marked as UNVERIFIABLE."""
        return self.block_tracker.get_unverifiable_domains()
