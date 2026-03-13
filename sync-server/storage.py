import json
import os
import threading

STATE_FILE = "state.json"
_state_lock = threading.Lock()

def load_state():
    with _state_lock:
        if not os.path.exists(STATE_FILE):
            return {"users": {}}
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"users": {}}

def save_state(state):
    with _state_lock:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=4)

def update_user_state(username, device_id, data):
    state = load_state()
    if username not in state["users"]:
        state["users"][username] = {"devices": {}, "config": {}, "global_time": 0}
    
    if "config" in data:
        state["users"][username]["config"] = data["config"]
    
    if "time" in data:
        # Time contains the latest TIME_SPENT_DAY, TIME_SPENT_WEEK, etc. from that device.
        state["users"][username]["devices"][device_id] = data["time"]
        
    save_state(state)
    return state

def adjust_global_time(username, delta_seconds):
    state = load_state()
    if username in state["users"]:
        state["users"][username]["global_time"] += delta_seconds
        save_state(state)
    return state
