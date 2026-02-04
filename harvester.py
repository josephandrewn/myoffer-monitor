# harvester.py
# Site Map Harvester - Extracts and categorizes navigation URLs from client websites
# Part of MyOffer Monitor

import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urljoin
from typing import Dict, List, Optional, Tuple

# Data directory for site maps
DATA_DIR = Path("data")
SITE_MAPS_FILE = DATA_DIR / "site_maps.json"

# Category display order (priority-based)
CATEGORY_ORDER = [
    "New Inventory",
    "Used Inventory",
    "Certified Inventory",
    "New VDP",
    "Used VDP",
    "Certified VDP",
    "Service",
    "Finance",
    "Specials",
    "Trade-In",
    "Parts",
    "Hours & Directions",
    "About",
    "Contact",
]

# --- Provider-Specific URL Patterns ---
# Each provider has unique URL structures for different page types

PROVIDER_PATTERNS = {
    "DealerOn": {
        "New Inventory": [r"searchnew\.aspx", r"new-inventory", r"/new/"],
        "Used Inventory": [r"searchused\.aspx", r"used-inventory", r"pre-owned", r"/used/"],
        "Certified Inventory": [r"searchcertified\.aspx", r"certified-inventory", r"cpo-inventory"],
        "New VDP": [r"vehicle-details/new", r"/new-\d{4}-\w+"],
        "Used VDP": [r"vehicle-details/used", r"/used-\d{4}-\w+", r"/pre-owned-\d{4}"],
        "Certified VDP": [r"vehicle-details/certified", r"/certified-\d{4}-\w+", r"/cpo-\d{4}"],
        "Service": [r"service\.aspx", r"schedule-service", r"service-department", r"/service"],
        "Finance": [r"financing\.aspx", r"finance-center", r"credit-application", r"/finance"],
        "Specials": [r"specials", r"offers", r"incentives", r"deals"],
        "Trade-In": [r"trade-in", r"value-your-trade", r"kbb", r"tradein"],
        "Parts": [r"parts\.aspx", r"/parts", r"accessories", r"order-parts"],
        "Hours & Directions": [r"hours", r"directions", r"location", r"map", r"contact-us.*hours"],
        "About": [r"about-us", r"about\.aspx", r"our-story", r"dealership-info", r"/about"],
        "Contact": [r"contact-us", r"contact\.aspx", r"contact$"],
    },
    "Dealer.com": {
        "New Inventory": [r"/new-inventory", r"/new-vehicles", r"new\.htm"],
        "Used Inventory": [r"/used-inventory", r"/used-vehicles", r"/pre-owned", r"used\.htm"],
        "Certified Inventory": [r"/certified-inventory", r"/cpo-inventory", r"certified\.htm"],
        "New VDP": [r"/new-\d{4}-[a-z]+-[a-z]+", r"vehicle/new"],
        "Used VDP": [r"/used-\d{4}-[a-z]+-[a-z]+", r"/certified-used-\d{4}", r"vehicle/used"],
        "Certified VDP": [r"/certified-\d{4}-[a-z]+-[a-z]+", r"vehicle/certified"],
        "Service": [r"/service", r"/schedule-service", r"service-center", r"service-department"],
        "Finance": [r"/finance", r"/financing", r"finance-center", r"credit-application"],
        "Specials": [r"specials", r"/offers", r"incentives", r"-deals"],
        "Trade-In": [r"trade-in", r"value-your-trade", r"tradepending", r"kbb"],
        "Parts": [r"/parts", r"accessories", r"parts-center"],
        "Hours & Directions": [r"hours", r"directions", r"location", r"dealership-hours"],
        "About": [r"about-us", r"our-story", r"about-dealership", r"/about"],
        "Contact": [r"contact-us", r"contact$", r"contact-dealer"],
    },
    "Dealer Inspire": {
        # Certified MUST come before Used
        "Certified Inventory": [r"/certified", r"/cpo", r"inventory/certified", r"certified.*vehicles"],
        "New Inventory": [r"/new-vehicles", r"/new/", r"inventory/new"],
        "Used Inventory": [r"/used-vehicles", r"/used/", r"inventory/used", r"(?<!certified[-/])pre-owned"],
        "Certified VDP": [r"/certified-\d{4}-", r"inventory/certified/.*\d{5,}"],
        "New VDP": [r"/new-\d{4}-", r"inventory/new/.*\d{5,}"],
        "Used VDP": [r"/used-\d{4}-", r"inventory/used/.*\d{5,}"],
        "Service": [r"/service", r"schedule-service", r"service-center", r"service-department"],
        "Finance": [r"/financ", r"/finance", r"finance-application", r"credit-application", r"apply.*financ"],
        "Specials": [r"specials", r"offers", r"incentives", r"deals"],
        "Trade-In": [r"trade", r"value-your-trade", r"sell-your-car", r"kbb"],
        "Parts": [r"/parts", r"accessories"],
        "Hours & Directions": [r"hours", r"directions", r"location", r"contact.*hours"],
        "About": [r"about", r"our-story", r"meet-the-team", r"why-buy"],
        "Contact": [r"contact", r"get-in-touch"],
    },
    "DealerSocket": {
        "New Inventory": [r"/new", r"inventory/new", r"new-cars"],
        "Used Inventory": [r"/used", r"inventory/used", r"used-cars", r"pre-owned"],
        "Certified Inventory": [r"/certified", r"inventory/certified"],
        "New VDP": [r"/vehicle/\w+/new", r"/new/.*vin"],
        "Used VDP": [r"/vehicle/\w+/used", r"/used/.*vin"],
        "Certified VDP": [r"/vehicle/\w+/certified"],
        "Service": [r"/service", r"schedule-service"],
        "Finance": [r"/finance", r"financing"],
        "Specials": [r"specials", r"offers"],
        "Trade-In": [r"trade", r"appraisal"],
        "Parts": [r"/parts"],
        "Hours & Directions": [r"hours", r"directions", r"location"],
        "About": [r"about", r"dealership"],
        "Contact": [r"contact"],
    },
    "Sokal": {
        "New Inventory": [r"/new", r"new-inventory", r"new-vehicles"],
        "Used Inventory": [r"/used", r"used-inventory", r"pre-owned"],
        "Certified Inventory": [r"/certified", r"cpo"],
        "New VDP": [r"/vehicle/new", r"/new/.*\d+"],
        "Used VDP": [r"/vehicle/used", r"/used/.*\d+"],
        "Certified VDP": [r"/vehicle/certified"],
        "Service": [r"service", r"schedule"],
        "Finance": [r"finance", r"credit"],
        "Specials": [r"specials", r"offers"],
        "Trade-In": [r"trade", r"value"],
        "Parts": [r"parts"],
        "Hours & Directions": [r"hours", r"directions", r"location"],
        "About": [r"about"],
        "Contact": [r"contact"],
    },
}

# Generic patterns used when provider is unknown or "Other"
GENERIC_PATTERNS = {
    # IMPORTANT: Certified must be checked BEFORE Used to avoid misclassification
    "Certified Inventory": [
        r"certified",
        r"\bcpo\b", 
        r"certified[-_]*(inventory|vehicles?|pre-?owned)",
    ],
    "New Inventory": [r"new.*(inventory|vehicle|car)", r"/new/", r"searchnew"],
    "Used Inventory": [
        r"(?<!certified[-_])used.*(inventory|vehicle|car)",  # used but not certified-used
        r"(?<!certified[-_])pre-?owned",  # pre-owned but not certified-pre-owned
        r"/used/", 
        r"searchused"
    ],
    "Certified VDP": [r"/certified[-/]\d{4}[-/]", r"vehicle.*certified.*\d{5,}"],
    "New VDP": [r"/new[-/]\d{4}[-/]", r"vehicle.*new.*\d{5,}", r"vin.*new"],
    "Used VDP": [r"/used[-/]\d{4}[-/]", r"vehicle.*used.*\d{5,}", r"vin.*used", r"(?<!certified[-_])pre-?owned[-/]\d{4}"],
    "Service": [r"service", r"schedule.*service", r"repair", r"maintenance"],
    "Finance": [r"financ", r"credit", r"loan", r"payment", r"pre-?approv", r"apply.*(credit|financ)"],
    "Specials": [r"specials?", r"offers?", r"incentives?", r"deals?", r"savings"],
    "Trade-In": [r"trade-?in", r"value.*trade", r"sell.*car", r"appraisal", r"kbb"],
    "Parts": [r"parts", r"accessories", r"oem"],
    "Hours & Directions": [r"hours", r"directions", r"location", r"map", r"find-us"],
    "About": [r"about", r"our-story", r"history", r"meet.*team"],
    "Contact": [r"contact", r"get-in-touch", r"reach-us"],
}

# Link text patterns (matches against anchor text, not URL)
TEXT_PATTERNS = {
    "Certified Inventory": [r"certified", r"^cpo$", r"certified.*pre-?owned"],
    "New Inventory": [r"^new\s*(vehicles?|inventory|cars?)?$", r"shop\s*new", r"new\s*cars"],
    "Used Inventory": [r"^(used|pre-?owned)\s*(vehicles?|inventory|cars?)?$", r"shop\s*(used|pre-?owned)"],
    "Service": [r"^service", r"schedule\s*service", r"service\s*(dept|department|center)", r"book\s*service"],
    "Finance": [r"financ", r"apply.*credit", r"get\s*approved", r"credit\s*app", r"pre-?qual", r"payment\s*calc"],
    "Specials": [r"specials?$", r"offers?$", r"incentives?", r"deals?$", r"savings?"],
    "Trade-In": [r"trade", r"value\s*your", r"sell\s*(my|your)\s*car", r"we.*buy.*cars?"],
    "Parts": [r"^parts", r"accessories", r"order\s*parts"],
    "Hours & Directions": [r"hours", r"directions", r"location", r"find\s*us", r"get\s*directions"],
    "About": [r"^about", r"our\s*story", r"meet.*team", r"why\s*(buy|choose)"],
    "Contact": [r"^contact", r"get\s*in\s*touch", r"reach\s*us"],
}


def load_site_maps() -> Dict:
    """Load site maps from JSON file."""
    try:
        if SITE_MAPS_FILE.exists():
            with open(SITE_MAPS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading site maps: {e}")
    return {}


def save_site_maps(data: Dict) -> bool:
    """Save site maps to JSON file."""
    try:
        DATA_DIR.mkdir(exist_ok=True)
        with open(SITE_MAPS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving site maps: {e}")
        return False


def get_site_map(url: str) -> Optional[Dict]:
    """Get stored site map for a URL's domain."""
    site_maps = load_site_maps()
    domain = get_domain(url)
    return site_maps.get(domain)


def has_site_map(url: str) -> bool:
    """Check if a site map exists for this URL's domain."""
    return get_site_map(url) is not None


def get_domain(url: str) -> str:
    """Extract domain from URL for use as key."""
    parsed = urlparse(url)
    # Include scheme and netloc for full domain
    return f"{parsed.scheme}://{parsed.netloc}"


def normalize_domain(domain: str) -> str:
    """Normalize domain for comparison (handle www/non-www)."""
    return domain.replace("://www.", "://").lower()


def domains_match(url: str, base_domain: str) -> bool:
    """Check if a URL belongs to the same domain (handles www/non-www)."""
    url_domain = get_domain(url)
    return normalize_domain(url_domain) == normalize_domain(base_domain)


def get_provider_patterns(provider: str) -> Dict[str, List[str]]:
    """Get URL patterns for a specific provider."""
    if provider and provider in PROVIDER_PATTERNS:
        return PROVIDER_PATTERNS[provider]
    return GENERIC_PATTERNS


def categorize_link(url: str, text: str, provider: str) -> Tuple[Optional[str], bool]:
    """
    Categorize a link based on URL and anchor text.
    
    Returns:
        Tuple of (category_name, is_vdp)
        category_name is None if uncategorized
    """
    url_lower = url.lower()
    text_lower = text.lower().strip() if text else ""
    
    patterns = get_provider_patterns(provider)
    
    # Check for VDP patterns first - Certified before Used to avoid misclassification
    for vdp_category in ["Certified VDP", "New VDP", "Used VDP"]:
        if vdp_category in patterns:
            for pattern in patterns[vdp_category]:
                if re.search(pattern, url_lower, re.IGNORECASE):
                    return (vdp_category, True)
    
    # IMPORTANT: Check categories in specific order - Certified BEFORE Used
    # This prevents "certified-pre-owned" from matching "pre-owned" first
    priority_order = [
        "Certified Inventory",  # Must be before Used
        "New Inventory",
        "Used Inventory",
        "Service",
        "Finance",
        "Specials",
        "Trade-In",
        "Parts",
        "Hours & Directions",
        "About",
        "Contact",
    ]
    
    # Check URL against patterns in priority order
    for category in priority_order:
        if category in patterns:
            for pattern in patterns[category]:
                if re.search(pattern, url_lower, re.IGNORECASE):
                    return (category, False)
    
    # Check any remaining categories not in priority list
    for category, category_patterns in patterns.items():
        if "VDP" in category or category in priority_order:
            continue  # Already checked
        for pattern in category_patterns:
            if re.search(pattern, url_lower, re.IGNORECASE):
                return (category, False)
    
    # Check anchor text against text patterns (also in priority order)
    for category in priority_order:
        if category in TEXT_PATTERNS:
            for pattern in TEXT_PATTERNS[category]:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return (category, False)
    
    # Check remaining text patterns
    for category, text_pattern_list in TEXT_PATTERNS.items():
        if category in priority_order:
            continue  # Already checked
        for pattern in text_pattern_list:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return (category, "VDP" in category)
    
    return (None, False)


def is_vdp_url(url: str, provider: str) -> Optional[str]:
    """
    Check if URL is a Vehicle Detail Page.
    
    Returns:
        VDP type ("New VDP", "Used VDP", "Certified VDP") or None
    """
    url_lower = url.lower()
    patterns = get_provider_patterns(provider)
    
    for vdp_type in ["New VDP", "Used VDP", "Certified VDP"]:
        if vdp_type in patterns:
            for pattern in patterns[vdp_type]:
                if re.search(pattern, url_lower, re.IGNORECASE):
                    return vdp_type
    
    # Generic VDP detection - look for VIN patterns, year-make-model
    vin_pattern = r"[A-HJ-NPR-Z0-9]{17}"
    year_make_model = r"/\d{4}[-/][a-z]+[-/][a-z]+"
    
    if re.search(vin_pattern, url, re.IGNORECASE):
        # Try to determine type from URL context
        if "new" in url_lower:
            return "New VDP"
        elif "certified" in url_lower or "cpo" in url_lower:
            return "Certified VDP"
        else:
            return "Used VDP"
    
    if re.search(year_make_model, url_lower):
        if "/new" in url_lower or "new-" in url_lower:
            return "New VDP"
        elif "/certified" in url_lower or "certified-" in url_lower:
            return "Certified VDP"
        elif "/used" in url_lower or "used-" in url_lower or "pre-owned" in url_lower:
            return "Used VDP"
    
    return None


def extract_links_from_html(html: str, base_url: str) -> List[Dict]:
    """
    Extract links from HTML, focusing on navigation areas.
    
    Returns list of dicts with 'url', 'text', 'in_nav' keys.
    """
    links = []
    seen_urls = set()
    
    # Parse base URL for resolving relative links
    base_domain = get_domain(base_url)
    
    # Pattern to find anchor tags
    # This is a simplified regex approach - in actual implementation,
    # we'll use the browser's DOM access which is more reliable
    link_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]*)</a>'
    
    for match in re.finditer(link_pattern, html, re.IGNORECASE | re.DOTALL):
        href = match.group(1).strip()
        text = match.group(2).strip()
        
        # Clean up text (remove extra whitespace)
        text = ' '.join(text.split())
        
        # Skip empty, anchor-only, javascript, mailto, tel links
        if not href or href.startswith('#') or href.startswith('javascript:') \
           or href.startswith('mailto:') or href.startswith('tel:'):
            continue
        
        # Resolve relative URLs
        if href.startswith('/'):
            full_url = base_domain + href
        elif not href.startswith('http'):
            full_url = urljoin(base_url, href)
        else:
            full_url = href
        
        # Skip external links
        if not full_url.startswith(base_domain):
            continue
        
        # Skip duplicates
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)
        
        # Skip common non-content links
        skip_patterns = [
            r'/cdn-cgi/', r'/wp-content/', r'/wp-includes/',
            r'\.(jpg|jpeg|png|gif|svg|css|js|pdf|zip)$',
            r'#', r'javascript:', r'void\(0\)'
        ]
        if any(re.search(p, full_url, re.IGNORECASE) for p in skip_patterns):
            continue
        
        links.append({
            'url': full_url,
            'text': text,
        })
    
    return links


def harvest_from_browser(driver, url: str, provider: str) -> Dict:
    """
    Harvest site map using Selenium WebDriver.
    This is the primary harvesting method during scans.
    
    Args:
        driver: Selenium WebDriver instance
        url: The page URL to harvest from
        provider: Expected provider for pattern matching
    
    Returns:
        Dict with categorized links
    """
    result = {category: [] for category in CATEGORY_ORDER}
    other_links = []
    vdp_found = {"New VDP": False, "Used VDP": False, "Certified VDP": False}
    
    base_domain = get_domain(url)
    seen_urls = set()
    
    try:
        # Get all links from navigation areas first
        nav_links = driver.execute_script("""
            const links = [];
            const seenUrls = new Set();
            
            // Priority selectors for navigation
            const navSelectors = [
                'nav a',
                'header a',
                '[role="navigation"] a',
                '.nav a',
                '.navbar a',
                '.navigation a',
                '.main-nav a',
                '.primary-nav a',
                '.menu a',
                '.main-menu a',
                '#menu a',
                '#navigation a'
            ];
            
            // Collect from nav areas
            for (const selector of navSelectors) {
                const elements = document.querySelectorAll(selector);
                elements.forEach(a => {
                    const href = a.href;
                    const text = a.textContent.trim().replace(/\\s+/g, ' ');
                    if (href && !seenUrls.has(href) && text) {
                        seenUrls.add(href);
                        links.push({url: href, text: text, isNav: true});
                    }
                });
            }
            
            // Also get footer links (often have important pages)
            const footerLinks = document.querySelectorAll('footer a');
            footerLinks.forEach(a => {
                const href = a.href;
                const text = a.textContent.trim().replace(/\\s+/g, ' ');
                if (href && !seenUrls.has(href) && text) {
                    seenUrls.add(href);
                    links.push({url: href, text: text, isNav: false});
                }
            });
            
            return links;
        """)
        
        if not nav_links:
            # Fallback: get all links on page
            nav_links = driver.execute_script("""
                const links = [];
                const seenUrls = new Set();
                const allLinks = document.querySelectorAll('a[href]');
                
                allLinks.forEach(a => {
                    const href = a.href;
                    const text = a.textContent.trim().replace(/\\s+/g, ' ');
                    if (href && !seenUrls.has(href) && text && text.length < 100) {
                        seenUrls.add(href);
                        links.push({url: href, text: text, isNav: false});
                    }
                });
                
                return links.slice(0, 200);  // Limit to prevent overcollection
            """)
        
        for link in nav_links:
            link_url = link.get('url', '')
            link_text = link.get('text', '')
            
            # Skip external links (handle www/non-www mismatch)
            if not domains_match(link_url, base_domain):
                continue
            
            # Skip already seen
            if link_url in seen_urls:
                continue
            seen_urls.add(link_url)
            
            # Skip common non-content patterns
            skip_patterns = [
                r'/cdn-cgi/', 
                r'\.(jpg|jpeg|png|gif|svg|css|js|pdf)(\?|$)',
                r'javascript:', 
                r'tel:', 
                r'mailto:',
            ]
            if any(re.search(p, link_url, re.IGNORECASE) for p in skip_patterns):
                continue
            
            # Skip if URL is just the domain with # (like "https://site.com/#")
            if link_url.rstrip('/').endswith('#'):
                continue
            
            # Categorize the link
            category, is_vdp = categorize_link(link_url, link_text, provider)
            
            # Handle VDPs - only keep first of each type
            if is_vdp and category:
                if not vdp_found.get(category, False):
                    vdp_found[category] = True
                    result[category].append(link_url)
                continue
            
            # Check if it's a VDP we didn't catch
            vdp_type = is_vdp_url(link_url, provider)
            if vdp_type:
                if not vdp_found.get(vdp_type, False):
                    vdp_found[vdp_type] = True
                    result[vdp_type].append(link_url)
                continue
            
            # Add to appropriate category
            if category:
                # Avoid duplicates within category
                if link_url not in result[category]:
                    result[category].append(link_url)
            else:
                # Uncategorized - add to other
                if link_text and len(link_text) < 50:
                    other_links.append(link_text)
        
    except Exception as e:
        print(f"Error harvesting links: {e}")
    
    # Remove duplicates from other_links and limit
    other_links = list(dict.fromkeys(other_links))[:20]
    
    return {
        "links": result,
        "other": other_links
    }


def save_harvested_site_map(url: str, provider: str, harvest_result: Dict) -> bool:
    """
    Save harvested site map data.
    
    Args:
        url: The site URL
        provider: Provider used for harvesting
        harvest_result: Result from harvest_from_browser()
    
    Returns:
        True if saved successfully
    """
    site_maps = load_site_maps()
    domain = get_domain(url)
    
    site_maps[domain] = {
        "harvested_at": datetime.now().isoformat(),
        "provider": provider or "Unknown",
        "links": harvest_result.get("links", {}),
        "other": harvest_result.get("other", [])
    }
    
    return save_site_maps(site_maps)


def delete_site_map(url: str) -> bool:
    """Delete site map for a URL's domain."""
    site_maps = load_site_maps()
    domain = get_domain(url)
    
    if domain in site_maps:
        del site_maps[domain]
        return save_site_maps(site_maps)
    return True


def format_site_map_for_display(site_map: Dict) -> str:
    """
    Format site map data for display in a dialog.
    
    Returns formatted text string.
    """
    if not site_map:
        return "No site map data available."
    
    lines = []
    
    # Links by category
    links = site_map.get("links", {})
    
    for category in CATEGORY_ORDER:
        urls = links.get(category, [])
        lines.append(f"\n{category}")
        
        if urls:
            for url in urls:
                lines.append(url)
        else:
            lines.append("Not found")
    
    # Other links
    other = site_map.get("other", [])
    if other:
        lines.append("\n" + "─" * 40)
        lines.append(f"Other: {', '.join(other[:10])}")
        if len(other) > 10:
            lines.append(f"  ...and {len(other) - 10} more")
    
    return "\n".join(lines)


# --- Convenience functions for external use ---

def get_site_map_summary(url: str) -> Optional[Dict]:
    """
    Get a summary of the site map for display.
    
    Returns dict with harvested_at, provider, and formatted links.
    """
    site_map = get_site_map(url)
    if not site_map:
        return None
    
    return {
        "harvested_at": site_map.get("harvested_at", "Unknown"),
        "provider": site_map.get("provider", "Unknown"),
        "links": site_map.get("links", {}),
        "other": site_map.get("other", []),
        "formatted": format_site_map_for_display(site_map)
    }
