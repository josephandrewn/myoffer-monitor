"""
Test script for database system
Run this with: python test_database.py
"""

from database import get_database
import pandas as pd
from pathlib import Path

def test_database_connection():
    """Test basic database connection"""
    print("=" * 60)
    print("TESTING DATABASE CONNECTION")
    print("=" * 60)
    
    print("\n→ Getting database instance...")
    db = get_database()
    print(f"✓ Database connected: {db.db_path}")
    
    # Check if database file exists
    if db.db_path.exists():
        size = db.db_path.stat().st_size
        print(f"✓ Database file exists ({size} bytes)")
    else:
        print("✗ Database file not created!")
        return False
    
    return True

def test_add_site():
    """Test adding sites"""
    print("\n" + "=" * 60)
    print("TESTING ADD SITE")
    print("=" * 60)
    
    db = get_database()
    
    print("\n→ Adding test site...")
    site_id = db.add_site(
        client_name="Test Client",
        url="https://testclient.com",
        provider="Test Provider",
        config="STD",
        status="PENDING",
        details="Test site for validation",
        active="Yes"
    )
    
    print(f"✓ Site added with ID: {site_id}")
    return site_id

def test_get_site(site_id):
    """Test retrieving a site"""
    print("\n" + "=" * 60)
    print("TESTING GET SITE")
    print("=" * 60)
    
    db = get_database()
    
    print(f"\n→ Retrieving site with ID {site_id}...")
    site = db.get_site(site_id)
    
    if site:
        print("✓ Site retrieved successfully!")
        print(f"  Client: {site['client_name']}")
        print(f"  URL: {site['url']}")
        print(f"  Provider: {site['provider']}")
        print(f"  Status: {site['status']}")
        return True
    else:
        print("✗ Site not found!")
        return False

def test_update_site(site_id):
    """Test updating a site"""
    print("\n" + "=" * 60)
    print("TESTING UPDATE SITE")
    print("=" * 60)
    
    db = get_database()
    
    print(f"\n→ Updating site {site_id} status to PASS...")
    db.update_site(
        site_id,
        status="PASS",
        config="STD",
        details="Test scan completed successfully"
    )
    print("✓ Site updated!")
    
    # Verify update
    site = db.get_site(site_id)
    if site['status'] == "PASS":
        print("✓ Update verified!")
        return True
    else:
        print("✗ Update not reflected!")
        return False

def test_search_sites():
    """Test searching sites"""
    print("\n" + "=" * 60)
    print("TESTING SEARCH SITES")
    print("=" * 60)
    
    db = get_database()
    
    print("\n→ Searching for 'Test'...")
    results = db.search_sites("Test")
    
    if results:
        print(f"✓ Found {len(results)} matching site(s)")
        for site in results:
            print(f"  - {site['client_name']}: {site['url']}")
        return True
    else:
        print("✗ No sites found!")
        return False

def test_scan_history(site_id):
    """Test scan history tracking"""
    print("\n" + "=" * 60)
    print("TESTING SCAN HISTORY")
    print("=" * 60)
    
    db = get_database()
    
    print(f"\n→ Adding scan result for site {site_id}...")
    db.add_scan_result(
        site_id=site_id,
        status="PASS",
        provider="Test Provider",
        config="STD",
        details="Perfect (Rule of 1)",
        duration=2.5
    )
    print("✓ Scan result added!")
    
    print("\n→ Retrieving scan history...")
    history = db.get_scan_history(site_id, limit=5)
    
    if history:
        print(f"✓ Retrieved {len(history)} scan(s)")
        for scan in history:
            print(f"  - {scan['scan_date']}: {scan['status']} ({scan['scan_duration']}s)")
        return True
    else:
        print("✗ No scan history found!")
        return False

def test_dataframe_export():
    """Test exporting to DataFrame"""
    print("\n" + "=" * 60)
    print("TESTING DATAFRAME EXPORT")
    print("=" * 60)
    
    db = get_database()
    
    print("\n→ Exporting all sites to DataFrame...")
    df = db.to_dataframe()
    
    if not df.empty:
        print(f"✓ Exported {len(df)} rows")
        print(f"✓ Columns: {list(df.columns)}")
        print("\nFirst row:")
        print(df.head(1).to_string())
        return True
    else:
        print("⚠️  DataFrame is empty (no sites in database yet)")
        return True  # Not an error if database is new

def test_backup_creation():
    """Test database backup"""
    print("\n" + "=" * 60)
    print("TESTING BACKUP CREATION")
    print("=" * 60)
    
    db = get_database()
    
    print("\n→ Creating backup...")
    backup_path = db.create_backup()
    
    if backup_path.exists():
        size = backup_path.stat().st_size
        print(f"✓ Backup created: {backup_path}")
        print(f"✓ Backup size: {size} bytes")
        return True
    else:
        print("✗ Backup file not found!")
        return False

def test_statistics():
    """Test scan statistics"""
    print("\n" + "=" * 60)
    print("TESTING SCAN STATISTICS")
    print("=" * 60)
    
    db = get_database()
    
    print("\n→ Getting scan statistics...")
    stats = db.get_scan_statistics()
    
    if stats:
        print("✓ Statistics retrieved:")
        print(f"  Total scans: {stats.get('total_scans', 0)}")
        print(f"  Average duration: {stats.get('avg_duration', 0):.2f}s")
        print(f"  Last scan: {stats.get('last_scan', 'Never')}")
        if 'by_status' in stats:
            print("  Scans by status:")
            for status, count in stats['by_status'].items():
                print(f"    {status}: {count}")
        return True
    else:
        print("⚠️  No statistics available yet")
        return True  # Not an error if database is new

def cleanup_test_data():
    """Clean up test data (optional)"""
    print("\n" + "=" * 60)
    print("CLEANUP (Optional)")
    print("=" * 60)
    
    response = input("\nDo you want to delete the test site? (y/n): ")
    
    if response.lower() == 'y':
        db = get_database()
        # Find and delete test site
        results = db.search_sites("Test Client")
        if results:
            for site in results:
                db.delete_site(site['id'])
                print(f"✓ Deleted site: {site['client_name']}")
        else:
            print("No test sites to delete")
    else:
        print("Test data kept in database")

def main():
    """Run all database tests"""
    print("\n" + "=" * 60)
    print("DATABASE SYSTEM TEST SUITE")
    print("=" * 60)
    
    # Test 1: Connection
    if not test_database_connection():
        print("\n✗ Database connection failed. Cannot continue.")
        return False
    
    # Test 2: Add site
    site_id = test_add_site()
    if not site_id:
        print("\n✗ Failed to add site. Cannot continue.")
        return False
    
    # Run remaining tests
    tests = [
        ("Get Site", lambda: test_get_site(site_id)),
        ("Update Site", lambda: test_update_site(site_id)),
        ("Search Sites", test_search_sites),
        ("Scan History", lambda: test_scan_history(site_id)),
        ("DataFrame Export", test_dataframe_export),
        ("Backup Creation", test_backup_creation),
        ("Statistics", test_statistics),
    ]
    
    results = [("Database Connection", True), ("Add Site", True)]  # Already passed
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} FAILED: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All database tests passed!")
        print(f"\n→ Your database is located at: data/mom_data.db")
        print(f"→ Backups are stored in: backups/")
        
        # Optional cleanup
        cleanup_test_data()
        
        return True
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    main()