"""Activity logger - tracks what Hermes is doing in real-time."""
import json, os, datetime, threading

ACTIVITY_PATH = "/home/ali/business/state/activity.json"
_lock = threading.Lock()

def _load():
    try:
        with open(ACTIVITY_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"status": "active", "started_at": datetime.datetime.utcnow().isoformat(),
                "current_focus": "Starting up", "last_activity": None, "activities": [],
                "today_goal": "", "stats": {"api_requests_served": 0, "customers_acquired": 0,
                "revenue_usd": 0, "improvements_made": 0}}

def _save(data):
    with open(ACTIVITY_PATH, "w") as f:
        json.dump(data, f, indent=2)

def log(action, detail=""):
    with _lock:
        data = _load()
        entry = {
            "time": datetime.datetime.utcnow().isoformat(),
            "action": action,
            "detail": detail
        }
        data["activities"].insert(0, entry)
        data["last_activity"] = entry
        # Keep last 50 activities
        data["activities"] = data["activities"][:50]
        _save(data)

def set_focus(focus):
    with _lock:
        data = _load()
        data["current_focus"] = focus
        _save(data)

def set_goal(goal):
    with _lock:
        data = _load()
        data["today_goal"] = goal
        _save(data)

def increment_stat(stat, amount=1):
    with _lock:
        data = _load()
        data["stats"][stat] = data["stats"].get(stat, 0) + amount
        _save(data)

def get_status():
    with _lock:
        return _load()
