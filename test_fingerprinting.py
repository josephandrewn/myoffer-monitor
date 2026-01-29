"""
Test the new fingerprinting functionality
"""
import sys
sys.path.append('.')  # Add current directory to path

from tabs.scanner_tab import BatchWorker

def test_fingerprinting():
    print("Testing browser fingerprinting...")
    print("=" * 60)
    
    # Create a worker instance (we just need the start_driver method)
    worker = BatchWorker([])
    
    # Start 3 browsers and show their fingerprints
    for i in range(3):
        print(f"\nBrowser {i+1}:")
        try:
            driver = worker.start_driver()
            
            # Check what the browser thinks it is
            ua = driver.execute_script("return navigator.userAgent")
            webdriver = driver.execute_script("return navigator.webdriver")
            plugins = driver.execute_script("return navigator.plugins.length")
            
            print(f"  User Agent: {ua[:80]}...")
            print(f"  Webdriver property: {webdriver}")  # Should be undefined
            print(f"  Plugins detected: {plugins}")  # Should be > 0
            
            driver.quit()
            print("  ✓ Browser closed successfully")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✓ Fingerprinting test complete!")
    print("\nWhat to look for:")
    print("  • Each browser should have DIFFERENT user agent")
    print("  • Webdriver should be 'None' or 'undefined'")
    print("  • Plugins should be > 0 (we mock 5)")

if __name__ == "__main__":
    test_fingerprinting()