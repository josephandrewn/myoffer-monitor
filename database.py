"""
Database Layer for MyOffer Monitor
Provides SQLite backend with migration, backup, and query capabilities
"""

import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import shutil
import json

try:
    from config import DATABASE_PATH, BACKUPS_DIR, DEFAULT_COLUMNS
    from logger import get_logger
except ImportError:
    DATABASE_PATH = Path("data/mom_data.db")
    BACKUPS_DIR = Path("backups")
    DEFAULT_COLUMNS = ["Client Name", "URL", "Provider", "Config", "Status", "Details", "Active"]
    get_logger = lambda x: None

logger = get_logger(__name__) if get_logger else None

# ============================================================================
# DATABASE SCHEMA
# ============================================================================

SCHEMA_VERSION = 1

CREATE_SITES_TABLE = """
CREATE TABLE IF NOT EXISTS sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_name TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    provider TEXT DEFAULT '',
    config TEXT DEFAULT '',
    status TEXT DEFAULT 'PENDING',
    details TEXT DEFAULT '',
    active TEXT DEFAULT 'Yes',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_SCAN_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS scan_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    provider TEXT,
    config TEXT,
    details TEXT,
    scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scan_duration REAL,
    FOREIGN KEY (site_id) REFERENCES sites (id) ON DELETE CASCADE
)
"""

CREATE_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_CHANGE_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS change_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    record_id INTEGER NOT NULL,
    operation TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_note TEXT
)
"""

# Indexes for performance
CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_sites_status ON sites(status)",
    "CREATE INDEX IF NOT EXISTS idx_sites_active ON sites(active)",
    "CREATE INDEX IF NOT EXISTS idx_sites_url ON sites(url)",
    "CREATE INDEX IF NOT EXISTS idx_scan_history_site_id ON scan_history(site_id)",
    "CREATE INDEX IF NOT EXISTS idx_scan_history_date ON scan_history(scan_date)",
]

# ============================================================================
# DATABASE CLASS
# ============================================================================

class Database:
    """Database manager for MyOffer Monitor"""
    
    def __init__(self, db_path: Path = DATABASE_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Create tables and indexes if they don't exist"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create tables
                cursor.execute(CREATE_SITES_TABLE)
                cursor.execute(CREATE_SCAN_HISTORY_TABLE)
                cursor.execute(CREATE_SETTINGS_TABLE)
                cursor.execute(CREATE_CHANGE_LOG_TABLE)
                
                # Create indexes
                for index_sql in CREATE_INDEXES:
                    cursor.execute(index_sql)
                
                # Set schema version
                cursor.execute(
                    "INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)",
                    ('schema_version', str(SCHEMA_VERSION))
                )
                
                conn.commit()
                
                if logger:
                    logger.info("Database initialized", path=str(self.db_path))
        
        except Exception as e:
            if logger:
                logger.error("Failed to initialize database", exception=e)
            raise
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # ========================================================================
    # SITE OPERATIONS
    # ========================================================================
    
    def add_site(self, client_name: str, url: str, **kwargs) -> int:
        """
        Add a new site to the database
        
        Returns:
            Site ID
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build insert query
                fields = ['client_name', 'url']
                values = [client_name, url]
                
                for key in ['provider', 'config', 'status', 'details', 'active']:
                    if key in kwargs:
                        fields.append(key)
                        values.append(kwargs[key])
                
                placeholders = ','.join(['?' for _ in fields])
                fields_str = ','.join(fields)
                
                cursor.execute(
                    f"INSERT INTO sites ({fields_str}) VALUES ({placeholders})",
                    values
                )
                
                site_id = cursor.lastrowid
                conn.commit()
                
                if logger:
                    logger.info("Site added", client=client_name, url=url, id=site_id)
                
                return site_id
        
        except sqlite3.IntegrityError:
            if logger:
                logger.warning("Site already exists", url=url)
            # Return existing site ID
            return self.get_site_by_url(url)['id']
        
        except Exception as e:
            if logger:
                logger.error("Failed to add site", exception=e, url=url)
            raise
    
    def update_site(self, site_id: int, **kwargs):
        """Update site fields"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build update query
                updates = []
                values = []
                
                for key in ['client_name', 'url', 'provider', 'config', 'status', 'details', 'active']:
                    if key in kwargs:
                        updates.append(f"{key} = ?")
                        values.append(kwargs[key])
                
                if not updates:
                    return
                
                updates.append("updated_at = CURRENT_TIMESTAMP")
                values.append(site_id)
                
                cursor.execute(
                    f"UPDATE sites SET {', '.join(updates)} WHERE id = ?",
                    values
                )
                
                conn.commit()
                
                if logger:
                    logger.debug("Site updated", id=site_id, fields=list(kwargs.keys()))
        
        except Exception as e:
            if logger:
                logger.error("Failed to update site", exception=e, id=site_id)
            raise
    
    def delete_site(self, site_id: int):
        """Delete a site (also deletes scan history via CASCADE)"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM sites WHERE id = ?", (site_id,))
                conn.commit()
                
                if logger:
                    logger.info("Site deleted", id=site_id)
        
        except Exception as e:
            if logger:
                logger.error("Failed to delete site", exception=e, id=site_id)
            raise
    
    def get_site(self, site_id: int) -> Optional[Dict[str, Any]]:
        """Get site by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM sites WHERE id = ?", (site_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            if logger:
                logger.error("Failed to get site", exception=e, id=site_id)
            return None
    
    def get_site_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Get site by URL"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM sites WHERE url = ?", (url,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            if logger:
                logger.error("Failed to get site by URL", exception=e, url=url)
            return None
    
    def get_all_sites(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """Get all sites"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if active_only:
                    cursor.execute("SELECT * FROM sites WHERE active = 'Yes' ORDER BY id")
                else:
                    cursor.execute("SELECT * FROM sites ORDER BY id")
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            if logger:
                logger.error("Failed to get all sites", exception=e)
            return []
    
    def search_sites(self, query: str) -> List[Dict[str, Any]]:
        """Search sites by name or URL"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                search_pattern = f"%{query}%"
                cursor.execute(
                    "SELECT * FROM sites WHERE client_name LIKE ? OR url LIKE ? ORDER BY id",
                    (search_pattern, search_pattern)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            if logger:
                logger.error("Failed to search sites", exception=e, query=query)
            return []
    
    # ========================================================================
    # SCAN HISTORY
    # ========================================================================
    
    def add_scan_result(self, site_id: int, status: str, provider: str = "",
                       config: str = "", details: str = "", duration: float = 0.0):
        """Record a scan result"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO scan_history 
                       (site_id, status, provider, config, details, scan_duration)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (site_id, status, provider, config, details, duration)
                )
                conn.commit()
                
                if logger:
                    logger.debug("Scan result recorded", site_id=site_id, status=status)
        
        except Exception as e:
            if logger:
                logger.error("Failed to record scan result", exception=e, site_id=site_id)
    
    def get_scan_history(self, site_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get scan history for a site"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT * FROM scan_history 
                       WHERE site_id = ? 
                       ORDER BY scan_date DESC 
                       LIMIT ?""",
                    (site_id, limit)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            if logger:
                logger.error("Failed to get scan history", exception=e, site_id=site_id)
            return []
    
    def get_scan_statistics(self) -> Dict[str, Any]:
        """Get overall scan statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Total scans
                cursor.execute("SELECT COUNT(*) as count FROM scan_history")
                stats['total_scans'] = cursor.fetchone()['count']
                
                # Scans by status
                cursor.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM scan_history 
                    GROUP BY status
                """)
                stats['by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
                
                # Average scan duration
                cursor.execute("SELECT AVG(scan_duration) as avg_duration FROM scan_history")
                stats['avg_duration'] = cursor.fetchone()['avg_duration'] or 0
                
                # Last scan date
                cursor.execute("SELECT MAX(scan_date) as last_scan FROM scan_history")
                stats['last_scan'] = cursor.fetchone()['last_scan']
                
                return stats
        
        except Exception as e:
            if logger:
                logger.error("Failed to get scan statistics", exception=e)
            return {}
    
    # ========================================================================
    # DATAFRAME OPERATIONS
    # ========================================================================
    
    def to_dataframe(self, active_only: bool = False) -> pd.DataFrame:
        """Export sites to pandas DataFrame"""
        sites = self.get_all_sites(active_only)
        
        if not sites:
            return pd.DataFrame(columns=DEFAULT_COLUMNS)
        
        # Convert to DataFrame with correct column names
        df = pd.DataFrame(sites)
        df = df.rename(columns={
            'client_name': 'Client Name',
            'url': 'URL',
            'provider': 'Provider',
            'config': 'Config',
            'status': 'Status',
            'details': 'Details',
            'active': 'Active'
        })
        
        # Select only the columns we need
        return df[DEFAULT_COLUMNS]
    
    def from_dataframe(self, df: pd.DataFrame, replace: bool = False):
        """Import sites from pandas DataFrame"""
        try:
            if replace:
                # Clear existing data
                with self.get_connection() as conn:
                    conn.execute("DELETE FROM sites")
                    conn.commit()
            
            # Add each site
            for _, row in df.iterrows():
                try:
                    self.add_site(
                        client_name=str(row.get('Client Name', '')),
                        url=str(row.get('URL', '')),
                        provider=str(row.get('Provider', '')),
                        config=str(row.get('Config', '')),
                        status=str(row.get('Status', 'PENDING')),
                        details=str(row.get('Details', '')),
                        active=str(row.get('Active', 'Yes'))
                    )
                except Exception as e:
                    if logger:
                        logger.warning("Skipped duplicate site", url=row.get('URL'), exception=e)
            
            if logger:
                logger.info("Imported sites from DataFrame", count=len(df))
        
        except Exception as e:
            if logger:
                logger.error("Failed to import from DataFrame", exception=e)
            raise
    
    # ========================================================================
    # BACKUP & RESTORE
    # ========================================================================
    
    def create_backup(self, backup_name: Optional[str] = None) -> Path:
        """Create a backup of the database"""
        try:
            if not backup_name:
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
            backup_path = BACKUPS_DIR / backup_name
            BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
            
            # Close connection if open
            if self.conn:
                self.conn.close()
                self.conn = None
            
            # Copy database file
            shutil.copy2(self.db_path, backup_path)
            
            if logger:
                logger.info("Database backup created", path=str(backup_path))
            
            return backup_path
        
        except Exception as e:
            if logger:
                logger.error("Failed to create backup", exception=e)
            raise
    
    def restore_backup(self, backup_path: Path):
        """Restore database from backup"""
        try:
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            # Close connection if open
            if self.conn:
                self.conn.close()
                self.conn = None
            
            # Create backup of current database first
            current_backup = self.db_path.parent / f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            if self.db_path.exists():
                shutil.copy2(self.db_path, current_backup)
            
            # Restore from backup
            shutil.copy2(backup_path, self.db_path)
            
            if logger:
                logger.info("Database restored from backup", backup=str(backup_path))
        
        except Exception as e:
            if logger:
                logger.error("Failed to restore backup", exception=e, backup=str(backup_path))
            raise
    
    def cleanup_old_backups(self, keep_count: int = 7):
        """Keep only the most recent N backups"""
        try:
            backups = sorted(BACKUPS_DIR.glob("backup_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
            
            for backup in backups[keep_count:]:
                backup.unlink()
                if logger:
                    logger.debug("Deleted old backup", path=str(backup))
        
        except Exception as e:
            if logger:
                logger.error("Failed to cleanup old backups", exception=e)
    
    # ========================================================================
    # MAINTENANCE
    # ========================================================================
    
    def vacuum(self):
        """Optimize database (reclaim space, rebuild indexes)"""
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                conn.commit()
                
                if logger:
                    logger.info("Database vacuumed")
        
        except Exception as e:
            if logger:
                logger.error("Failed to vacuum database", exception=e)
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_db_instance: Optional[Database] = None

def get_database() -> Database:
    """Get or create singleton database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
