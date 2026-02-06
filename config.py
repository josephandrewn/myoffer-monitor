"""
Configuration Management for MyOffer Monitor
Centralizes all application settings and constants
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict
import json

# ============================================================================
# PATHS
# ============================================================================

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
SCANS_DIR = BASE_DIR / "scans"
BACKUPS_DIR = BASE_DIR / "backups"

# Ensure directories exist
for directory in [DATA_DIR, LOGS_DIR, SCANS_DIR, BACKUPS_DIR]:
    directory.mkdir(exist_ok=True)

# ============================================================================
# DATABASE
# ============================================================================

DATABASE_PATH = DATA_DIR / "mom_data.db"
ENABLE_DATABASE = True  # Set to False to use CSV-only mode

# ============================================================================
# SCANNER CONFIGURATION
# ============================================================================

@dataclass
class ScannerConfig:
    """Scanner behavior configuration"""
    
    # Timing
    max_wait_time: int = 15  # seconds to wait for page load
    settle_time: int = 3     # seconds to wait after script detection
    max_attempts: int = 2    # number of retry attempts per site
    
    # Delays (anti-detection)
    min_delay_between_scans: float = 2.0  # minimum seconds between sites
    max_delay_between_scans: float = 5.0  # maximum seconds between sites
    page_load_timeout: int = 30           # browser timeout
    
    # Browser
    headless_mode: bool = True            # run browser in background
    browser_window_size: tuple = (1920, 1080)
    user_agent: str = ""                  # empty = use default
    
    # Concurrent scanning
    max_concurrent_scans: int = 1         # number of parallel browser instances
    
    # Screenshot
    take_screenshots: bool = True         # save evidence screenshots
    screenshot_on_fail_only: bool = False # only save on failures
    
    # Detection
    target_scripts: Dict[str, str] = field(default_factory=lambda: {
        "SPA": "idrove.it/behaviour.spa.js",
        "DCOM": "idrove.it/behaviour.dcom.js",
        "STD": "idrove.it/behaviour.js",
        "BUNDLE": "idrove.it/behaviour.bundle.js",
    })
    
    # Expected counts for each config type
    expected_counts: Dict[str, int] = field(default_factory=lambda: {
        "SPA": 4,
        "DCOM": 1,
        "BUNDLE": 2,
        "STD": 1,
    })
    
    # Vendor-specific rules
    vendor_rules: Dict[str, Dict] = field(default_factory=lambda: {
        "DealerOn": {"config": "STD", "count": 1, "allow_head": False},
        "Dealer.com": {"config": "STD", "count": 1, "allow_head": False},
        "Dealer Inspire": {"config": "STD", "count": 2, "allow_head": True},
    })

# ============================================================================
# APPLICATION SETTINGS
# ============================================================================

@dataclass
class AppSettings:
    """Application-wide settings"""
    
    # Auto-save
    auto_save_enabled: bool = True
    auto_save_interval: int = 300  # seconds (5 minutes)
    
    # Backups
    auto_backup_enabled: bool = True
    backup_interval_hours: int = 24
    max_backups_to_keep: int = 7
    
    # UI
    window_width: int = 1400
    window_height: int = 900
    remember_window_size: bool = True
    
    # Data
    default_csv_path: str = ""
    recent_files: List[str] = field(default_factory=list)
    max_recent_files: int = 10
    
    # Notifications
    show_scan_complete_notification: bool = True
    play_sound_on_complete: bool = False
    
    # Advanced
    enable_debug_mode: bool = False
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': str(LOGS_DIR / 'mom.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8',
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'detailed',
            'filename': str(LOGS_DIR / 'mom_errors.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'urllib3': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': False
        },
        'selenium': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': False
        },
    }
}

# ============================================================================
# VENDOR DETECTION RULES
# ============================================================================

VENDOR_DETECTION_RULES = {
    "SOKAL": [
        ("html", "sokal.com"),
        ("html", "go-sokal"),
        ("text", "powered by sokal"),
        ("html", "sokal_assets"),
    ],
    "Dealer Inspire": [
        ("html", "dealerinspire.com"),
        ("html", "assets.dealerinspire"),
        ("html", "di-uploads"),
        ("html", 'id="di-root"'),
    ],
    "Dealer eProcess": [
        ("text", "dealer eprocess"),
        ("html", "dealereprocess.com"),
        ("html", "dep_"),
    ],
    "Dealer.com": [
        ("html", "dealer.com"),
        ("html", "ddc-footer"),
        ("html", "ddc-wrapper"),
    ],
    "DealerOn": [
        ("text", "dealeron"),
        ("html", "dealeron.com"),
    ],
    "Sincro/CDK": [
        ("html", "sincrodigital"),
        ("html", "cdkglobal"),
        ("html", 'content="sincro"'),
    ],
    "Team Velocity": [
        ("html", "apollo.auto"),
        ("html", "teamvelocity"),
    ],
    "Fox Dealer": [
        ("text", "fox dealer"),
        ("html", "foxdealer"),
    ],
    "DealerFire": [("html", "dealerfire")],
    "FusionZone": [("html", "fusionzone")],
    "Dealer Car Search": [("html", "dealercarsearch")],
    "DLRdmv": [("html", "dlrdmv")],
    "AutoManager": [("html", "automanager")],
    "Security Block (Imperva)": [
        ("html", "imperva"),
        ("html", "_incapsula_"),
    ],
    "Security Block (Cloudflare)": [("html", "cloudflare")],
}

BLOCK_DETECTION_PHRASES = [
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
    "cloudflare",
]

# ============================================================================
# DEFAULT TABLE COLUMNS
# ============================================================================

DEFAULT_COLUMNS = [
    "Client Name",
    "URL",
    "Provider",
    "Config",
    "Status",
    "Details",
    "Active"
]

# Status values
STATUS_VALUES = ["PENDING", "PASS", "FAIL", "WARN", "BLOCKED", "ERROR", "ARCHIVED"]

# ============================================================================
# SETTINGS PERSISTENCE
# ============================================================================

SETTINGS_FILE = DATA_DIR / "settings.json"

def load_settings() -> AppSettings:
    """Load settings from JSON file"""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                return AppSettings(**data)
        except Exception as e:
            print(f"Error loading settings: {e}")
    return AppSettings()

def save_settings(settings: AppSettings):
    """Save settings to JSON file"""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            # Convert dataclass to dict
            settings_dict = {
                'auto_save_enabled': settings.auto_save_enabled,
                'auto_save_interval': settings.auto_save_interval,
                'auto_backup_enabled': settings.auto_backup_enabled,
                'backup_interval_hours': settings.backup_interval_hours,
                'max_backups_to_keep': settings.max_backups_to_keep,
                'window_width': settings.window_width,
                'window_height': settings.window_height,
                'remember_window_size': settings.remember_window_size,
                'default_csv_path': settings.default_csv_path,
                'recent_files': settings.recent_files,
                'max_recent_files': settings.max_recent_files,
                'show_scan_complete_notification': settings.show_scan_complete_notification,
                'play_sound_on_complete': settings.play_sound_on_complete,
                'enable_debug_mode': settings.enable_debug_mode,
                'log_level': settings.log_level,
            }
            json.dump(settings_dict, f, indent=2)
    except Exception as e:
        print(f"Error saving settings: {e}")

# ============================================================================
# SCANNER SETTINGS PERSISTENCE
# ============================================================================

SCANNER_SETTINGS_FILE = DATA_DIR / "scanner_settings.json"

def load_scanner_config() -> ScannerConfig:
    """Load scanner configuration from JSON file"""
    if SCANNER_SETTINGS_FILE.exists():
        try:
            with open(SCANNER_SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                return ScannerConfig(**data)
        except Exception as e:
            print(f"Error loading scanner settings: {e}")
    return ScannerConfig()

def save_scanner_config(config: ScannerConfig):
    """Save scanner configuration to JSON file"""
    try:
        with open(SCANNER_SETTINGS_FILE, 'w') as f:
            # Convert dataclass to dict
            config_dict = {
                'max_wait_time': config.max_wait_time,
                'settle_time': config.settle_time,
                'max_attempts': config.max_attempts,
                'min_delay_between_scans': config.min_delay_between_scans,
                'max_delay_between_scans': config.max_delay_between_scans,
                'page_load_timeout': config.page_load_timeout,
                'headless_mode': config.headless_mode,
                'browser_window_size': list(config.browser_window_size),
                'user_agent': config.user_agent,
                'max_concurrent_scans': config.max_concurrent_scans,
                'take_screenshots': config.take_screenshots,
                'screenshot_on_fail_only': config.screenshot_on_fail_only,
                'target_scripts': config.target_scripts,
                'expected_counts': config.expected_counts,
                'vendor_rules': config.vendor_rules,
            }
            json.dump(config_dict, f, indent=2)
    except Exception as e:
        print(f"Error saving scanner settings: {e}")

# ============================================================================
# INITIALIZATION
# ============================================================================

# Load settings on import
app_settings = load_settings()
scanner_config = load_scanner_config()
