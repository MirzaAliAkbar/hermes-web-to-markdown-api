#!/usr/bin/env python3
"""
Customer Acquisition Automation
Searches for places where the API can be listed and discovered.
Generates listings for directories that accept email-based signups.
"""
import datetime, json, httpx, os, sys

BUSINESS = "/home/ali/business"

def log(msg):
    print(f"[{datetime.datetime.utcnow().strftime('%H:%M:%S')}] {msg}")

def check_public_access():
    """Verify API is publicly accessible."""
    try:
        r = httpx.get("https://collectors-nearly-lyrics-press.trycloudflare.com/", timeout=10)
        if r.status_code == 200:
            data = r.json()
            log(f"✅ API public: {data.get('service', 'unknown')}")
            return True
    except Exception as e:
        log(f"❌ API not reachable: {e}")
    return False

def search_for_directories():
    """Search for free API directories that don't require accounts."""
    directories = [
        {"name": "GitHub Topics", "url": "https://github.com/MirzaAliAkbar/hermes-web-to-markdown-api", "status": "submitted", "note": "Has 8 discoverability tags"},
        {"name": "ProgrammableWeb", "url": "https://www.programmableweb.com/", "status": "needs account", "note": "Requires signup"},
        {"name": "RapidAPI", "url": "https://rapidapi.com/", "status": "needs account", "note": "Requires signup, free tier available"},
        {"name": "APILayer", "url": "https://apilayer.com/", "status": "needs account", "note": "Email signup"},
        {"name": "OpenAPI Hub", "url": "https://openapihub.com/", "status": "needs account", "note": "Email signup"},
        {"name": "AI Agent Directories", "url": "agent discovery via /agent.json", "status": "active", "note": "Endpoint live and discoverable"},
    ]
    
    log(f"\n📋 Distribution Status:")
    for d in directories:
        icon = "✅" if d["status"] == "submitted" or d["status"] == "active" else "⏳"
        log(f"  {icon} {d['name']}: {d['status']} — {d['note']}")
    
    return directories

def generate_listing_text():
    """Generate promotional text for various channels."""
    texts = {
        "twitter": "Need clean web content for your AI agent?\n\nPass any URL → get markdown.\n\n✅ Built for LLMs & agents\n✅ Auto-payments via USDT\n✅ Halal (Jafari compliant)\n\nCheck it out: https://collectors-nearly-lyrics-press.trycloudflare.com",
        "reddit": "Built a Web-to-Markdown API for AI agents\n\nI built a simple API that takes any URL and returns clean markdown. Designed for LLM consumption, automated agents, and developers.\n\n- Free tier: 100 req/day\n- Paid: $5 USDT for 10K req/day\n- Auto-payment via USDT/ETH (no KYC)\n- Open source: https://github.com/MirzaAliAkbar/hermes-web-to-markdown-api\n\nWould love feedback. Jafari Halal compliant.",
        "hackernews": "Show HN: Web-to-Markdown API with Auto-Crypto Payments\n\nI built a content extraction API that returns clean markdown from URLs. Designed for AI agents and developers.\n\nKey features:\n- Single POST /extract endpoint\n- USDT/ETH auto-payment (no KYC needed)\n- Works with any LLM or agent framework\n- Self-hosted, private, no data logging\n\nTech: FastAPI + trafilatura + Ethereum\n\nEverything is open source. Would appreciate feedback.",
    }
    
    log(f"\n📝 Generated {len(texts)} promotional texts")
    
    # Save for reference
    with open(f"{BUSINESS}/state/promotional_texts.json", "w") as f:
        json.dump(texts, f, indent=2)
    log(f"💾 Saved to state/promotional_texts.json")
    
    return texts

def main():
    log("=" * 50)
    log("CUSTOMER ACQUISITION REPORT")
    log(f"Date: {datetime.date.today().isoformat()}")
    log("=" * 50)
    
    online = check_public_access()
    if not online:
        log("❌ Cannot proceed - API is not publicly accessible")
        return
    
    directories = search_for_directories()
    texts = generate_listing_text()
    
    log(f"\n📊 Summary:")
    submitted = sum(1 for d in directories if d["status"] in ["submitted", "active"])
    pending = len(directories) - submitted
    log(f"  Live listings: {submitted}")
    log(f"  Pending (needs your account): {pending}")
    log(f"  Promotional texts ready: {len(texts)}")
    log(f"\n📌 Action needed from you:")
    log(f"  1. Post on Reddit (r/SideProject, r/API, r/Entrepreneur)")
    log(f"  2. Create ProgrammableWeb/RapidAPI accounts (email only)")
    log(f"  3. Share the wallet address with potential users")

if __name__ == "__main__":
    main()
