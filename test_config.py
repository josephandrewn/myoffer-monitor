"""
Test script for configuration system
Run this with: python test_config.py
"""

from config import app_settings, scanner_config, save_settings, save_scanner_config

def test_app_settings():
    """Test application settings"""
    print("=" * 60)
    print("TESTING APPLICATION SETTINGS")
    print("=" * 60)
    
    print(f"\n✓ Auto-save enabled: {app_settings.auto_save_enabled}")
    print(f"✓ Auto-save interval: {app_settings.auto_save_interval} seconds")
    print(f"✓ Auto-backup enabled: {app_settings.auto_backup_enabled}")
    print(f"✓ Backup interval: {app_settings.backup_interval_hours} hours")
    print(f"✓ Max backups to keep: {app_settings.max_backups_to_keep}")
    print(f"✓ Window size: {app_settings.window_width}x{app_settings.window_height}")
    print(f"✓ Log level: {app_settings.log_level}")
    print(f"✓ Debug mode: {app_settings.enable_debug_mode}")
    
    print("\n✓ All application settings loaded successfully!")
    return True

def test_scanner_settings():
    """Test scanner settings"""
    print("\n" + "=" * 60)
    print("TESTING SCANNER SETTINGS")
    print("=" * 60)
    
    print(f"\n✓ Max wait time: {scanner_config.max_wait_time} seconds")
    print(f"✓ Settle time: {scanner_config.settle_time} seconds")
    print(f"✓ Max attempts: {scanner_config.max_attempts}")
    print(f"✓ Scan delay range: {scanner_config.min_delay_between_scans}-{scanner_config.max_delay_between_scans} seconds")
    print(f"✓ Headless mode: {scanner_config.headless_mode}")
    print(f"✓ Take screenshots: {scanner_config.take_screenshots}")
    print(f"✓ Browser size: {scanner_config.browser_window_size}")
    
    print("\n✓ All scanner settings loaded successfully!")
    return True

def test_settings_modification():
    """Test modifying and saving settings"""
    print("\n" + "=" * 60)
    print("TESTING SETTINGS MODIFICATION")
    print("=" * 60)
    
    # Save original values
    original_log_level = app_settings.log_level
    original_wait_time = scanner_config.max_wait_time
    
    print("\n→ Changing log level to DEBUG...")
    app_settings.log_level = "DEBUG"
    save_settings(app_settings)
    print("✓ Saved!")
    
    print("\n→ Changing max wait time to 20...")
    scanner_config.max_wait_time = 20
    save_scanner_config(scanner_config)
    print("✓ Saved!")
    
    # Restore original values
    print("\n→ Restoring original values...")
    app_settings.log_level = original_log_level
    scanner_config.max_wait_time = original_wait_time
    save_settings(app_settings)
    save_scanner_config(scanner_config)
    print("✓ Restored!")
    
    print("\n✓ Settings can be modified and saved successfully!")
    return True

def test_paths():
    """Test that all required directories exist"""
    print("\n" + "=" * 60)
    print("TESTING DIRECTORY STRUCTURE")
    print("=" * 60)
    
    from config import DATA_DIR, LOGS_DIR, SCANS_DIR, BACKUPS_DIR
    
    directories = {
        "Data": DATA_DIR,
        "Logs": LOGS_DIR,
        "Scans": SCANS_DIR,
        "Backups": BACKUPS_DIR
    }
    
    for name, path in directories.items():
        if path.exists():
            print(f"✓ {name} directory exists: {path}")
        else:
            print(f"✗ {name} directory missing: {path}")
            return False
    
    print("\n✓ All required directories exist!")
    return True

def main():
    """Run all configuration tests"""
    print("\n" + "=" * 60)
    print("CONFIGURATION SYSTEM TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Application Settings", test_app_settings),
        ("Scanner Settings", test_scanner_settings),
        ("Settings Modification", test_settings_modification),
        ("Directory Structure", test_paths),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} FAILED: {e}")
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
        print("\n🎉 All configuration tests passed!")
        print("\n→ Next: Check that data/settings.json and data/scanner_settings.json exist")
        return True
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    main()