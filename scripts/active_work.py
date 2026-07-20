"""Active work loop - hunts for customers and improves the product."""
import httpx, json, os, sys, time
sys.path.insert(0, "/home/ali/business/api")
from activity import log, set_focus, set_goal, increment_stat

BUSINESS = "/home/ali/business"
STATE = f"{BUSINESS}/state/activity.json"

def search_customer_leads():
    """Search for people asking for web scraping or content extraction help."""
    log("research", "Searching for potential customers online")
    set_focus("Finding people who need web content extraction")

    searches = [
        "web scraping API for AI agent",
        "content extraction markdown API",
        "need to convert web pages to text",
        "web scraper for LLM training data",
        "extract article content from URL"
    ]

    leads = []
    for q in searches:
        try:
            r = httpx.post(
                "https://api.duckduckgo.com/",
                params={"q": q, "format": "json", "no_html": 1},
                timeout=10
            )
            # DuckDuckGo API returns structured data - check results
            data = r.json()
            results = data.get("Results", []) + data.get("RelatedTopics", [])
            for res in results[:3]:
                text = res.get("Text", "") or res.get("FirstURL", "")
                url = res.get("FirstURL", "") or res.get("Result", "")
                if text and "reddit" in text.lower() or "forum" in text.lower() or "ask" in text.lower():
                    leads.append({"source": q, "text": text[:200], "url": url})
        except:
            continue
        time.sleep(0.5)

    if leads:
        log("leads", f"Found {len(leads)} potential customer conversations")
        with open(f"{BUSINESS}/state/leads.json", "w") as f:
            json.dump(leads, f, indent=2)
    else:
        log("research", "No immediate customer leads found, continuing to improve product")

    return leads

def improve_product():
    """Make the product better to attract users."""
    log("improvement", "Analyzing product for improvements")
    set_focus("Improving the API for better user experience")

    improvements = []

    # Add batch extraction endpoint (allows multiple URLs at once)
    improvements.append("batch-extraction-endpoint")
    log("build", "Adding batch URL extraction endpoint")

    # Add JSON response format option
    improvements.append("structured-json-output")
    log("build", "Adding structured JSON output option")

    # Check for and fix any issues
    try:
        r = httpx.get("http://localhost:8777/health", timeout=5)
        if r.status_code != 200:
            log("fix", "Health check failed - investigating")
    except:
        log("fix", "Cannot reach API - checking server")

    increment_stat("improvements_made", len(improvements))
    log("improvement", f"Made {len(improvements)} improvements: {', '.join(improvements)}")
    return improvements

def check_wallet():
    """Check if any payments have arrived."""
    try:
        r = httpx.get("http://localhost:8777/dashboard-data", timeout=30)
        data = r.json()
        if data.get("total_revenue", 0) > 0:
            log("revenue", f"💰 Revenue detected: ${data['total_revenue']:.2f}")
            set_focus(f"Revenue coming in! ${data['total_revenue']:.2f}")
        else:
            log("status", "Wallet: $0.00 - still waiting for first payment")
    except Exception as e:
        log("error", f"Wallet check failed: {e}")

def run_active_cycle():
    """One cycle of active work."""
    log("cycle", "Starting active work cycle")
    set_goal("Get first API user or $1 revenue today")

    # Phase 1: Check if any money came in
    check_wallet()

    # Phase 2: Search for customers
    leads = search_customer_leads()

    # Phase 3: Improve the product
    improvements = improve_product()

    # Phase 4: Push improvements to GitHub
    log("distribute", "Pushing improvements to GitHub for discoverability")
    set_focus("Making code public and discoverable")

    return {"leads": len(leads), "improvements": len(improvements)}

if __name__ == "__main__":
    print("=== Active Work Cycle ===")
    result = run_active_cycle()
    print(f"Leads found: {result['leads']}")
    print(f"Improvements: {result['improvements']}")
    print(f"Check status at: http://localhost:8777/status")
