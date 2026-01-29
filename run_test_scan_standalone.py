"""
Production Test Scan - Standalone Version (No Qt App Required)
Works outside of Qt application context

Usage:
    python run_test_scan_standalone.py
"""

import sys
import os
import pandas as pd
from datetime import datetime
import time

# Make sure we can import from tabs
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tabs.scanner_tab import BatchWorker, needs_session_warming

# ============================================================================
# CONFIGURATION
# ============================================================================

CSV_FILE = "Test_Data_Sites_-_scan_report_2026-01-28_18-1.csv"
OUTPUT_FILE = f"test_scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
MAX_SITES_TO_SCAN = 5  # Change to None to scan all

print("""
======================================================================
MYOFFER MONITOR - PRODUCTION TEST SCAN (STANDALONE)
======================================================================
All Improvements Active:
  ✓ Advanced Browser Fingerprinting
  ✓ Smart Delay Patterns
  ✓ Session Warming (Conditional)
======================================================================
""")

# ============================================================================
# LOAD DATA
# ============================================================================

print(f"Loading test data from: {CSV_FILE}")

try:
    df = pd.read_csv(CSV_FILE)
    print(f"✓ Loaded {len(df)} sites")
    
    # Add required columns if missing
    if 'Provider' not in df.columns:
        df['Provider'] = ''
    if 'Config' not in df.columns:
        df['Config'] = ''
    if 'Status' not in df.columns:
        df['Status'] = 'PENDING'
    if 'Details' not in df.columns:
        df['Details'] = ''
    if 'Active' not in df.columns:
        df['Active'] = 'Yes'
    
except FileNotFoundError:
    print(f"✗ Error: Could not find file: {CSV_FILE}")
    print(f"   Make sure the CSV is in the same directory as this script")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error loading CSV: {e}")
    sys.exit(1)

# Limit sites if needed
if MAX_SITES_TO_SCAN:
    df = df.head(MAX_SITES_TO_SCAN)
    print(f"→ Limiting to first {MAX_SITES_TO_SCAN} sites for testing")

# ============================================================================
# PREPARE BATCH
# ============================================================================

batch_data = []
for idx, row in df.iterrows():
    client_name = row['Client Name']
    url = row['URL']
    
    # Add https:// if not present
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url
    
    batch_data.append((idx, client_name, url, idx))

# ============================================================================
# PRE-SCAN ANALYSIS
# ============================================================================

print("\n" + "=" * 70)
print("PRE-SCAN ANALYSIS")
print("=" * 70)

print(f"\nTotal sites to scan: {len(batch_data)}")

# Check warming needs
warming_count = 0
warming_sites = []
for _, client, url, _ in batch_data:
    if needs_session_warming(url):
        warming_count += 1
        warming_sites.append(client)

print(f"\nSession warming analysis:")
print(f"  Sites requiring warming: {warming_count} ({warming_count/len(batch_data)*100:.1f}%)")
print(f"  Direct access sites: {len(batch_data) - warming_count} ({(len(batch_data)-warming_count)/len(batch_data)*100:.1f}%)")

if warming_sites:
    print(f"\n  Sites that will be warmed:")
    for site in warming_sites[:5]:
        print(f"    • {site}")
    if len(warming_sites) > 5:
        print(f"    ... and {len(warming_sites) - 5} more")

# Estimate time
avg_time_per_site = 25
warming_overhead = warming_count * 4
estimated_time = (len(batch_data) * avg_time_per_site + warming_overhead) / 60

print(f"\nEstimated scan time: {estimated_time:.1f} minutes")

# ============================================================================
# CONFIRM
# ============================================================================

print("\n" + "=" * 70)
response = input("Ready to start scan? (y/n): ")
if response.lower() != 'y':
    print("Scan cancelled.")
    sys.exit(0)

# ============================================================================
# RUN SCAN
# ============================================================================

print("\n" + "=" * 70)
print("STARTING SCAN")
print("=" * 70)
print("\nWatch for:")
print("  • Browser fingerprint messages (random UA and window size)")
print("  • [DIRECT] vs [WARM] indicators")
print("  • Variable delays between scans")
print("\n" + "-" * 70 + "\n")

# Track results
scan_results = {}
scan_start_time = time.time()
scan_completed = [False]  # Use list so we can modify in closure

# Create worker
worker = BatchWorker(batch_data)

# Connect signals
def on_result(row_idx, result):
    """Called when each scan completes"""
    scan_results[row_idx] = result
    
    # Update dataframe directly by row index
    df.at[row_idx, 'Status'] = result['status']
    df.at[row_idx, 'Provider'] = result.get('vendor', '')
    df.at[row_idx, 'Config'] = result.get('config', '')
    df.at[row_idx, 'Details'] = result.get('msg', '')
    
    # Print progress
    completed = len(scan_results)
    total = len(batch_data)
    client = df.at[row_idx, 'Client Name']
    print(f"[{completed}/{total}] {client}: {result['status']}")

def on_finished():
    """Called when all scans complete"""
    scan_duration = time.time() - scan_start_time
    print("\n" + "-" * 70)
    print(f"✓ Scan completed in {scan_duration / 60:.1f} minutes")
    scan_completed[0] = True

# Connect signals
worker.result_signal.connect(on_result)
worker.finished_signal.connect(on_finished)

# Start scan
worker.start()

# Wait for completion using simple polling (no Qt event loop needed)
print("Scanning in progress... (This may take several minutes)")
while not scan_completed[0]:
    time.sleep(0.5)  # Check every half second
    # Optional: You could add a timeout here if needed

# Make sure worker is fully done
worker.wait()

scan_duration = time.time() - scan_start_time

# ============================================================================
# GENERATE REPORT
# ============================================================================

print("\n" + "=" * 70)
print("SCAN RESULTS SUMMARY")
print("=" * 70)

# Count by status
status_counts = df['Status'].value_counts()
total = len(df)

print(f"\nTotal sites scanned: {total}")
print(f"Scan duration: {scan_duration / 60:.1f} minutes")
print(f"Average time per site: {scan_duration / total:.1f} seconds")

print("\nResults by status:")
for status in ['PASS', 'WARN', 'FAIL', 'BLOCKED', 'ERROR', 'PENDING']:
    count = status_counts.get(status, 0)
    percentage = (count / total * 100) if total > 0 else 0
    print(f"  {status:8s}: {count:3d} ({percentage:5.1f}%)")

# Success rate
success_count = status_counts.get('PASS', 0) + status_counts.get('WARN', 0)
success_rate = (success_count / total * 100) if total > 0 else 0

print(f"\n{'='*70}")
print(f"SUCCESS RATE: {success_rate:.1f}% ({success_count}/{total})")
print(f"{'='*70}")

# Vendor breakdown
print("\nVendor detection:")
vendor_counts = df[df['Provider'] != '']['Provider'].value_counts()
if not vendor_counts.empty:
    for vendor, count in vendor_counts.head(5).items():
        print(f"  {vendor}: {count}")
else:
    print("  No vendors detected")

# Config types
print("\nConfiguration types detected:")
config_counts = df[df['Config'] != '']['Config'].value_counts()
if not config_counts.empty:
    for config, count in config_counts.items():
        print(f"  {config}: {count}")
else:
    print("  No configurations detected")

# Problem sites
blocked = df[df['Status'] == 'BLOCKED']
if not blocked.empty:
    print(f"\n⚠️  BLOCKED sites ({len(blocked)}):")
    for _, row in blocked.iterrows():
        print(f"  • {row['Client Name']} - {row['URL']}")
    print("\n  💡 Consider adding these domains to PROBLEMATIC_SITES list:")
    # Extract unique domains
    blocked_domains = set()
    for url in blocked['URL']:
        # Extract domain
        domain = url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
        blocked_domains.add(domain)
    for domain in sorted(blocked_domains):
        print(f"     '{domain}',")

failed = df[df['Status'] == 'FAIL']
if not failed.empty:
    print(f"\n⚠️  FAILED sites ({len(failed)}):")
    for _, row in failed.head(3).iterrows():
        print(f"  • {row['Client Name']}: {row['Details']}")

pending = df[df['Status'] == 'PENDING']
if not pending.empty:
    print(f"\n⚠️  PENDING sites ({len(pending)}) - These were not scanned:")
    for _, row in pending.iterrows():
        print(f"  • {row['Client Name']}")

# ============================================================================
# SAVE RESULTS
# ============================================================================

try:
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✓ Results saved to: {OUTPUT_FILE}")
except Exception as e:
    print(f"\n✗ Error saving results: {e}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("\n" + "=" * 70)
print("✓ TEST SCAN COMPLETE")
print("=" * 70)
print("\nNext steps:")
print("  1. Review the results in:", OUTPUT_FILE)
if not blocked.empty:
    print("  2. Add blocked domains to PROBLEMATIC_SITES in scanner_tab.py")
    print("  3. Re-run scan to verify improvements")
print("\nExpected success rate with improvements: 80-85%")
print("Current success rate:", f"{success_rate:.1f}%")

if success_rate >= 80:
    print("\n🎉 Excellent! Your improvements are working great!")
elif success_rate >= 60:
    print("\n✓ Good! Add blocked domains to warming list for better results.")
else:
    print("\n⚠️  Lower than expected. Check blocked sites and add to warming list.")

print("=" * 70)
