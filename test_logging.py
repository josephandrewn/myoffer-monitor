"""
Test script for logging system
Run this with: python test_logging.py
"""

from logger import get_logger, LogExecutionTime, get_recent_logs, get_error_logs
import time
from pathlib import Path

def test_basic_logging():
    """Test basic log levels"""
    print("=" * 60)
    print("TESTING BASIC LOGGING")
    print("=" * 60)
    
    logger = get_logger("test_basic")
    
    print("\n→ Writing log messages at different levels...")
    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    
    print("✓ All log levels written!")
    return True

def test_structured_logging():
    """Test logging with context"""
    print("\n" + "=" * 60)
    print("TESTING STRUCTURED LOGGING")
    print("=" * 60)
    
    logger = get_logger("test_structured")
    
    print("\n→ Writing structured log with context...")
    logger.info(
        "Testing structured logging",
        client="Test Client",
        url="https://test.com",
        status="TEST"
    )
    
    print("✓ Structured logging works!")
    return True

def test_scan_logging():
    """Test specialized scan logging"""
    print("\n" + "=" * 60)
    print("TESTING SCAN LOGGING")
    print("=" * 60)
    
    logger = get_logger("test_scan")
    
    print("\n→ Logging scan start...")
    logger.scan_start("Test Client", "https://test.com")
    
    print("→ Logging scan result...")
    logger.scan_result(
        client="Test Client",
        url="https://test.com",
        status="PASS",
        vendor="Test Vendor",
        config="STD",
        details="Test passed"
    )
    
    print("✓ Scan logging works!")
    return True

def test_performance_logging():
    """Test performance timing"""
    print("\n" + "=" * 60)
    print("TESTING PERFORMANCE LOGGING")
    print("=" * 60)
    
    logger = get_logger("test_performance")
    
    print("\n→ Timing a simulated operation...")
    with LogExecutionTime(logger, "test_operation", context="test"):
        time.sleep(0.5)  # Simulate work
    
    print("✓ Performance logging works!")
    return True

def test_error_logging():
    """Test error logging with exceptions"""
    print("\n" + "=" * 60)
    print("TESTING ERROR LOGGING")
    print("=" * 60)
    
    logger = get_logger("test_error")
    
    print("\n→ Logging an error with exception...")
    try:
        # Intentionally cause an error
        result = 1 / 0
    except Exception as e:
        logger.error("Intentional test error", exception=e)
    
    print("✓ Error logging works!")
    return True

def test_log_files():
    """Test that log files exist and contain data"""
    print("\n" + "=" * 60)
    print("TESTING LOG FILES")
    print("=" * 60)
    
    from config import LOGS_DIR
    
    log_file = LOGS_DIR / "mom.log"
    error_log_file = LOGS_DIR / "mom_errors.log"
    
    print(f"\n→ Checking for log file: {log_file}")
    if log_file.exists():
        size = log_file.stat().st_size
        print(f"✓ Log file exists ({size} bytes)")
    else:
        print("✗ Log file not found!")
        return False
    
    print(f"\n→ Checking for error log file: {error_log_file}")
    if error_log_file.exists():
        size = error_log_file.stat().st_size
        print(f"✓ Error log file exists ({size} bytes)")
    else:
        print("✗ Error log file not found!")
        return False
    
    return True

def test_log_reading():
    """Test reading logs back"""
    print("\n" + "=" * 60)
    print("TESTING LOG READING")
    print("=" * 60)
    
    print("\n→ Reading recent log entries...")
    recent_logs = get_recent_logs(max_lines=5)
    
    if recent_logs:
        print(f"✓ Retrieved {len(recent_logs)} recent log entries")
        print("\nLast 3 log entries:")
        for line in recent_logs[-3:]:
            print(f"  {line.strip()}")
    else:
        print("⚠️  No log entries found (this is OK if it's your first run)")
    
    print("\n→ Reading error logs...")
    error_logs = get_error_logs(max_lines=5)
    
    if error_logs:
        print(f"✓ Retrieved {len(error_logs)} error log entries")
    else:
        print("✓ No error logs (this is good!)")
    
    return True

def main():
    """Run all logging tests"""
    print("\n" + "=" * 60)
    print("LOGGING SYSTEM TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Basic Logging", test_basic_logging),
        ("Structured Logging", test_structured_logging),
        ("Scan Logging", test_scan_logging),
        ("Performance Logging", test_performance_logging),
        ("Error Logging", test_error_logging),
        ("Log Files", test_log_files),
        ("Log Reading", test_log_reading),
    ]
    
    results = []
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
        print("\n🎉 All logging tests passed!")
        print("\n→ Next: View your logs with:")
        print("     tail -f logs/mom.log        (Linux/Mac)")
        print("     Get-Content logs/mom.log -Tail 20 -Wait    (Windows PowerShell)")
        return True
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    main()