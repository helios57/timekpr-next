import os
import requests
import json
import logging
from timekpr.common.utils.config import timekprUserControl, timekprUserConfig

# Default sync URL, easily overridable via environment variable
SYNC_SERVER_URL = os.environ.get("SYNC_SERVER_URL", "http://localhost:8000/api/sync")
DEVICE_ID = os.environ.get("DEVICE_ID", os.uname().nodename)

# We store the last synced absolute time.
# In a robust production environment, this might be saved to a hidden dotfile 
# so restarts mid-session retain the delta offset accurately.
# For E2E testing, we save this to a temp file since each execution is a fresh python process.
CACHE_FILE = "/tmp/timekpr_sync_last.json"

def get_last_synced(username):
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f).get(username)
    return None

def set_last_synced(username, value):
    data = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            data = json.load(f)
    data[username] = value
    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f)

def get_user_config(config_dir, username):
    config = timekprUserConfig(config_dir, username)
    config.loadUserConfiguration()
    return {
        "timestamp": str(config.getUserConfigLastModified()),
        "LIMIT_PER_DAY": getattr(config, "_timekprUserConfig", {}).get("LIMIT_PER_DAY", ""),
        "ALLOWED_WEEKDAYS": getattr(config, "_timekprUserConfig", {}).get("ALLOWED_WEEKDAYS", ""),
    }

def get_user_time(work_dir, username):
    control = timekprUserControl(work_dir, username)
    control.loadUserControl()
    return control.getUserTimeSpentDay()

def update_user_time(work_dir, username, global_adjustment):
    control = timekprUserControl(work_dir, username)
    control.loadUserControl()

    # Apply global adjustment from other devices
    if global_adjustment > 0:
        current_day = int(control.getUserTimeSpentDay())
        
        # When global adjustment increases, it means ANOTHER device consumed time.
        # So we add it to our local consumed time to reduce the amount left.
        new_day = current_day + global_adjustment
        control.setUserTimeSpentDay(new_day)
        
        current_balance = int(control.getUserTimeSpentBalance())
        new_balance = current_balance + global_adjustment
        control.setUserTimeSpentBalance(new_balance)
        
        control.saveControl()
        return True
    return False

def sync_user(config_dir, work_dir, username):
    try:
        current_spent = get_user_time(work_dir, username)
        
        # Calculate Delta
        last_spent = get_last_synced(username)
        if last_spent is None:
            last_spent = current_spent
            
        delta = current_spent - last_spent
        
        # Only true if clock was rolled back or day reset
        if delta < 0:
            delta = 0
            
        config_data = get_user_config(config_dir, username)

        payload = {
            "device_id": DEVICE_ID,
            "time_delta": {
                "consumed_seconds": delta
            },
            "config": config_data,
        }

        response = requests.post(f"{SYNC_SERVER_URL}/{username}", json=payload, timeout=5)
        if response.status_code == 200:
            # We successfully sent the delta, update our last_synced marker
            set_last_synced(username, current_spent)
            
            server_data = response.json()
            global_adjustment = server_data.get("global_time", {}).get("global_adjustment", 0)
            
            if global_adjustment > 0:
                # We need to apply this adjustment locally to our .time file
                if update_user_time(work_dir, username, global_adjustment):
                    # We modified the underlying time spent file, so we must reflect this 
                    # in our delta tracker so we don't accidentally push the adjustment back as "new local time"
                    new_synced = current_spent + global_adjustment
                    set_last_synced(username, new_synced)
                
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Silently fail if server is down, fallback to local limits automatically
        pass

if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Timekpr-next Sync Client")
    parser.add_argument("--config-dir", required=True, help="Timekpr config directory")
    parser.add_argument("--work-dir", required=True, help="Timekpr work directory")
    parser.add_argument("--username", required=True, help="Username to sync")
    
    args = parser.parse_args()
    sync_user(args.config_dir, args.work_dir, args.username)
