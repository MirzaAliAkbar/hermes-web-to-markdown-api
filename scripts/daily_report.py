#!/usr/bin/env python3
"""
Daily Founder's Report for Hermes Autonomous Services.
Runs every 24 hours via cronjob, delivers to Ali.
"""

import json, os, datetime, sqlite3
from pathlib import Path

BUSINESS_DIR = Path("/home/ali/business")
STATE_PATH = BUSINESS_DIR / "state.json"
API_KEYS_DB = BUSINESS_DIR / "state" / "api_keys.db"
TUNNEL_LOG = BUSINESS_DIR / "api" / "tunnel.log"

def load_state():
    with open(STATE_PATH) as f:
        return json.load(f)

def save_state(state):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)

def get_api_usage():
    if not API_KEYS_DB.exists():
        return {"total_requests": 0, "successful": 0, "errors": 0, "active_keys": 0}
    conn = sqlite3.connect(str(API_KEYS_DB))
    cur = conn.cursor()
    try:
        total = cur.execute("SELECT COUNT(*) FROM usage").fetchone()[0]
        success = cur.execute("SELECT COUNT(*) FROM usage WHERE status='success'").fetchone()[0]
        errors = cur.execute("SELECT COUNT(*) FROM usage WHERE status='error'").fetchone()[0]
        keys = cur.execute("SELECT COUNT(*) FROM api_keys WHERE active=1").fetchone()[0]
        today_total = cur.execute("SELECT COUNT(*) FROM usage WHERE date(timestamp) = date('now')").fetchone()[0]
    except:
        total = success = errors = keys = today_total = 0
    conn.close()
    return {"total_requests": total, "successful": success, "errors": errors, "active_keys": keys, "today": today_total}

def get_tunnel_url():
    if not TUNNEL_LOG.exists():
        return "Not set up"
    with open(TUNNEL_LOG) as f:
        content = f.read()
    for line in content.split("\n"):
        if "trycloudflare.com" in line:
            for word in line.split():
                if "trycloudflare.com" in word:
                    return word.strip()
    return "Check tunnel log"

def main():
    state = load_state()
    usage = get_api_usage()
    tunnel_url = get_tunnel_url()
    today = datetime.date.today().isoformat()

    report = f"""╔══════════════════════════════════════╗
║  HERMES FOUNDER'S REPORT           ║
║  {today}              ║
╚══════════════════════════════════════╝

📊 PRODUCT: Web-to-Markdown API
🌐 PUBLIC URL: {tunnel_url}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 USAGE STATS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Total requests:      {usage['total_requests']}
  Today:               {usage['today']}
  Successful:          {usage['successful']}
  Errors:              {usage['errors']}
  Active API keys:     {usage['active_keys']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 REVENUE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Revenue:            ${state.get('revenue', 0):.2f}
  Expenses:           ${state.get('expenses', 0):.2f}
  Profit:             ${state.get('profit', 0):.2f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️  STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Product:            {state.get('current_product', 'None')}
  Phase:              {state.get('phase', 'N/A')}
  Blockers:           {', '.join(state.get('blockers', ['None']))}
  Lessons learned:    {len(state.get('lessons', []))}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 NEXT 24H STRATEGY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. Monitor API traffic and logs
  2. Publish API docs to GitHub / developer directories
  3. Add user feedback channel
  4. Explore Halal payment rails (crypto/manual)
  5. Iterate based on usage patterns

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Halal compliance (Jafari): Active
   Service provides real utility (content extraction)
   No riba, no qimar, no gharar
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    # Update state with today's strategy
    state["daily_strategy"][today] = {
        "status": "running",
        "usage": usage,
        "revenue": state.get("revenue", 0),
    }
    save_state(state)

    print(report)

if __name__ == "__main__":
    main()
