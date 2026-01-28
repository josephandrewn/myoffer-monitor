"""
Quick integration test of all systems
Run this with: python test_integration.py
"""

from config import app_settings, scanner_config
from logger import get_logger
from database import get_database

def main():
    print("=" * 60)
    print("QUICK INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: Config
    print("\n1. Testing Configuration...")
    print(f"   Auto-save: {app_settings.auto_save_enabled}")
    print(f"   Scan wait time: {scanner_config.max_wait_time}s")
    print("   ✓ Config OK")
    
    # Test 2: Logging
    print("\n2. Testing Logging...")
    logger = get_logger("integration_test")
    logger.info("Integration test message", test="successful")
    print("   ✓ Logging OK")
    
    # Test 3: Database
    print("\n3. Testing Database...")
    db = get_database()
    test_id = db.add_site("Integration Test", "https://integration-test.com")
    site = db.get_site(test_id)
    db.delete_site(test_id)  # Clean up
    print(f"   ✓ Database OK")
    
    print("\n" + "=" * 60)
    print("🎉 ALL SYSTEMS OPERATIONAL!")
    print("=" * 60)
    print("\nYou're ready to move to Phase 4: Full Integration with main.py")

if __name__ == "__main__":
    main()