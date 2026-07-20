#!/usr/bin/env python3
"""
Self-Audit & Improvement Loop for Hermes Autonomous Services.
Runs daily. Analyzes performance, identifies improvements, updates strategy.
"""
import json, os, sqlite3, datetime, hashlib, time, subprocess
from pathlib import Path

BUSINESS = Path("/home/ali/business")
STATE = BUSINESS / "state.json"
API_DB = BUSINESS / "state" / "api_keys.db"
PAY_DB = BUSINESS / "state" / "payments.db"
SCRIPTS = BUSINESS / "scripts"

def load_state():
    with open(STATE) as f:
        return json.load(f)

def save_state(s):
    with open(STATE, "w") as f:
        json.dump(s, f, indent=2)

def get_stats():
    stats = {"keys": 0, "requests": 0, "today_reqs": 0, "payments": 0, "revenue": 0.0}
    if API_DB.exists():
        conn = sqlite3.connect(str(API_DB))
        stats["keys"] = conn.execute("SELECT COUNT(*) FROM api_keys WHERE active=1").fetchone()[0]
        stats["requests"] = conn.execute("SELECT COUNT(*) FROM usage").fetchone()[0]
        stats["today_reqs"] = conn.execute(
            "SELECT COUNT(*) FROM usage WHERE date(timestamp)=date('now')").fetchone()[0]
        conn.close()
    if PAY_DB.exists():
        conn = sqlite3.connect(str(PAY_DB))
        stats["payments"] = conn.execute("SELECT COUNT(*) FROM payments WHERE processed=1").fetchone()[0]
        stats["revenue"] = conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM payments WHERE processed=1").fetchone()[0]
        conn.close()
    return stats

def check_health():
    import httpx
    try:
        r = httpx.get("http://localhost:8777/health", timeout=5)
        return "healthy" if r.status_code == 200 else f"status {r.status_code}"
    except Exception as e:
        return f"down: {e}"

def suggest_improvements(stats, state):
    suggestions = []
    lessons = []

    # Revenue-based suggestions
    if stats["revenue"] == 0:
        suggestions.append("No revenue yet. Priority: get first customer.")
        suggestions.append("Share wallet address and API URL on relevant platforms.")
        suggestions.append("Add more free tier requests to attract users.")
    elif stats["revenue"] < 50:
        suggestions.append(f"Revenue: ${stats['revenue']:.2f}. Focus on upsell.")
        suggestions.append("Add discount for multi-month prepayment.")

    # Usage-based suggestions
    if stats["requests"] == 0:
        suggestions.append("No API usage yet. API needs visibility.")
        suggestions.append("Consider adding a demo page with live examples.")
    elif stats["today_reqs"] > stats["requests"] * 0.1:
        suggestions.append("Usage growing. Monitor for scaling needs.")

    # Feature suggestions
    lessons.append("API key + auto-payment system working")
    lessons.append("Cloudflare Tunnel provides free public access")
    suggestions.append("Next feature: batch URL extraction endpoint")
    suggestions.append("Next feature: webhook callback on extraction complete")

    return suggestions, lessons

def run_self_improvement():
    state = load_state()
    stats = get_stats()
    health = check_health()
    today = datetime.date.today().isoformat()
    suggestions, lessons = suggest_improvements(stats, state)

    # Log the audit
    state["daily_strategy"][today] = {
        "health": health,
        "stats": stats,
        "phase": state.get("phase", "unknown"),
        "suggestions": suggestions,
    }

    # Add new lessons (dedup)
    existing = set(state.get("lessons", []))
    for l in lessons:
        if l not in existing:
            state.setdefault("lessons", []).append(l)
            existing.add(l)

    # Update phase based on progress
    if stats["revenue"] > 0:
        state["phase"] = "3-growth"
    elif stats["requests"] > 10:
        state["phase"] = "2-execution"
    else:
        state["phase"] = "1-discovery"

    save_state(state)

    # Print report
    print(f"=== Self-Audit: {today} ===")
    print(f"Health:     {health}")
    print(f"Phase:      {state['phase']}")
    print(f"Requests:   {stats['requests']} total ({stats['today_reqs']} today)")
    print(f"Keys:       {stats['keys']} active")
    print(f"Revenue:    ${stats['revenue']:.2f} ({stats['payments']} payments)")
    print(f"Suggestions:")
    for s in suggestions:
        print(f"  → {s}")
    print(f"Lessons:    {len(lessons)} new")

if __name__ == "__main__":
    run_self_improvement()
