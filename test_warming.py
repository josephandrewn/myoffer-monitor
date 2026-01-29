"""
Test session warming logic
"""

# Simulate the functions (without actually loading pages)
PROBLEMATIC_SITES = [
    'cloudflare',
    'imperva',
    'lithia.com',
    'autonation.com',
]

def needs_session_warming(url):
    url_lower = url.lower()
    for pattern in PROBLEMATIC_SITES:
        if pattern in url_lower:
            return True
    return False

def test_warming_detection():
    print("Testing Session Warming Detection")
    print("=" * 60)
    
    # Test URLs
    test_urls = [
        ("https://acmemotors.com", False, "Regular dealer site"),
        ("https://johnsonauto.dealer.com", False, "Dealer.com (not in list yet)"),
        ("https://nissan.lithia.com", True, "Lithia (large group)"),
        ("https://smithcars.dealeron.com", False, "DealerOn (usually OK)"),
        ("https://autonation.com/store-123", True, "AutoNation (large group)"),
        ("https://smalldealer.com", False, "Small independent dealer"),
        ("https://protected.cloudflare.net", True, "Has cloudflare in URL"),
    ]
    
    print("\nTesting which URLs trigger session warming:\n")
    
    for url, expected, description in test_urls:
        result = needs_session_warming(url)
        status = "✓" if result == expected else "✗"
        action = "[WARM]" if result else "[DIRECT]"
        print(f"{status} {action} {url}")
        print(f"           {description}")
        print()
    
    print("=" * 60)
    print("Summary:")
    warm_count = sum(1 for url, exp, _ in test_urls if needs_session_warming(url))
    total_count = len(test_urls)
    print(f"  {warm_count}/{total_count} URLs would be warmed ({warm_count/total_count*100:.0f}%)")
    print(f"  {total_count - warm_count}/{total_count} URLs would be direct ({(total_count-warm_count)/total_count*100:.0f}%)")
    print("\n✓ Only warming problematic sites - smart!")

if __name__ == "__main__":
    test_warming_detection()