import os
import time
import requests
import docker

client = docker.from_env()

def run_cmd(cmd):
    import subprocess
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def setup_docker_env():
    # Start the dockerized environment
    run_cmd("docker compose -f e2e/docker-compose.yml up -d --build")
    time.sleep(5) # wait for server to boot

def teardown_docker_env():
    # Teardown
    run_cmd("docker compose -f e2e/docker-compose.yml down -v")

def test_sync_server_is_up():
    resp = requests.get("http://localhost:8000/")
    assert resp.status_code == 200
    assert "Timekpr Sync Server is running" in resp.json()["status"]

def exec_in_container(container_name, cmd):
    container = client.containers.get(container_name)
    res = container.exec_run(cmd)
    return res.output.decode('utf-8')

def init_client_files(container_name, username, current_spent=0):
    exec_in_container(container_name, f"mkdir -p /var/lib/timekpr/work/{username}")
    exec_in_container(container_name, f"mkdir -p /var/lib/timekpr/config/{username}")
    exec_in_container(container_name, f"mkdir -p /etc/timekpr")
    
    # Write a mock config
    exec_in_container(container_name, "sh -c 'echo \"[DOCUMENTATION]\" > /etc/timekpr/timekpr.conf'")
    
    # Write a mock user control file
    control_content = f"[{username}]\nTIME_SPENT_DAY = {current_spent}\nTIME_SPENT_BALANCE = {current_spent}\nLAST_CHECKED = 2026-03-13T10:00:00\n"
    exec_in_container(container_name, f"sh -c 'echo \"{control_content}\" > /var/lib/timekpr/work/{username}.time'")
    
    # Write a mock user config file
    config_content = f"[{username}]\nLIMIT_PER_DAY = 3600\nALLOWED_WEEKDAYS = 1;2;3;4;5;6;7\n"
    exec_in_container(container_name, f"sh -c 'echo \"{config_content}\" > /var/lib/timekpr/config/{username}'")

def run_sync(container_name, username):
    script = f"""
import sys
import traceback
import os
import types

sys.path.insert(0, '/app')

# Alpine's python locale module often lacks gettext bindings like bindtextdomain
import locale
if not hasattr(locale, 'bindtextdomain'):
    locale.bindtextdomain = lambda domain, dir: None
if not hasattr(locale, 'textdomain'):
    locale.textdomain = lambda domain: None

try:
    # Build a mock `timekpr` top level module mapping
    import importlib.util
    import timekpr
except ImportError:
    # If not installed, we create a fake module pointing to /app
    timekpr_mod = types.ModuleType('timekpr')
    timekpr_mod.__path__ = ['/app']
    sys.modules['timekpr'] = timekpr_mod

try:
    from client.sync_client import sync_user
    sync_user('/var/lib/timekpr/config', '/var/lib/timekpr/work', '{username}')
except Exception as e:
    traceback.print_exc()
"""
    output = exec_in_container(container_name, ["python3", "-c", script])
    print(f"[{container_name} SYNC OUTPUT]: {output}")
    return output

def read_spent_time(container_name, username):
    output = exec_in_container(container_name, f"cat /var/lib/timekpr/work/{username}.time")
    for line in output.splitlines():
        if "TIME_SPENT_DAY" in line:
            return int(line.split("=")[1].strip())
    return None

def test_delta_sync_scenario():
    user = "kid1"
    
    # 1. Initialize both clients with 0 time spent
    init_client_files("e2e-client1-1", user, 0)
    init_client_files("e2e-client2-1", user, 0)
    
    # 2. Sync client 1 (baseline)
    run_sync("e2e-client1-1", user)
    
    # 3. Simulate usage on Client 1
    # We fake usage by rewriting the TIME_SPENT_DAY directly
    init_client_files("e2e-client1-1", user, 60)
    
    # 4. Sync client 1 again. It should push a delta of +60s.
    run_sync("e2e-client1-1", user)
    
    # Verify server got it (we expect Client 2 to pull this down later)
    # 5. Sync client 2 (it currently has 0, but the server has +60 from client1. 
    # Because client 2 delta is 0, the server should force sync the 60 down).
    init_client_files("e2e-client2-1", user, 0)
    run_sync("e2e-client2-1", user)
    
    # 6. Verify client 2's local time file was updated by the global adjustment!
    c2_time = read_spent_time("e2e-client2-1", user)
    assert c2_time == 60, f"Expected 60, but got {c2_time}"

def test_trigger_hook_scenario():
    print("Testing DBus hook trigger...")
    user = "kid1"
    
    # 1. Init client 1 files
    init_client_files("e2e-client1-1", user, 0)
    
    # 2. Re-trigger full sync by making a config change directly using timekprUserConfig python API
    script = f"""
import sys
import os
import traceback
import types
sys.path.insert(0, '/app')

# Alpine's python locale module often lacks gettext bindings like bindtextdomain
import locale
if not hasattr(locale, 'bindtextdomain'):
    locale.bindtextdomain = lambda domain, dir: None
if not hasattr(locale, 'textdomain'):
    locale.textdomain = lambda domain: None

try:
    # Build a mock `timekpr` top level module mapping
    import importlib.util
    import timekpr
except ImportError:
    # If not installed, we create a fake module pointing to /app
    timekpr_mod = types.ModuleType('timekpr')
    timekpr_mod.__path__ = ['/app']
    sys.modules['timekpr'] = timekpr_mod

try:
    from timekpr.common.utils.config import timekprUserConfig

    cfg_dir = '/var/lib/timekpr/config'
    username = '{user}'
    
    cfg = timekprUserConfig(cfg_dir, username)
    cfg.loadUserConfiguration()
    cfg._timekprUserConfig["LIMIT_PER_DAY"] = "7200"
    cfg.saveUserConfiguration()
    print("SAVED CONFIG SUCCESSFULLY")
except Exception as e:
    traceback.print_exc()
"""
    output = exec_in_container("e2e-client1-1", ["python3", "-c", script])
    print(f"[Trigger script output]: {output}")
    assert "SAVED CONFIG SUCCESSFULLY" in output

    time.sleep(2) # Give the subprocess sync client time to execute

    # We can verify it worked if the sync_client has created the `_last_synced_time.json` 
    # since it wasn't invoked explicitly by us this time, it was invoked by the subprocess
    output = exec_in_container("e2e-client1-1", ["cat", "/tmp/timekpr_sync_last.json"])
    assert f'"{user}"' in output, f"JSON sync file not updated or missing: {output}"


if __name__ == "__main__":
    setup_docker_env()
    try:
        print("Running test_sync_server_is_up...")
        test_sync_server_is_up()
        print("Running test_delta_sync_scenario...")
        test_delta_sync_scenario()
        print("Running test_trigger_hook_scenario...")
        test_trigger_hook_scenario()
        print("ALL TESTS PASSED!")
    finally:
        teardown_docker_env()
