import sys, os, traceback, types
import locale
import json

locale.bindtextdomain = lambda domain, dir: None
locale.textdomain = lambda domain: None

sys.path.insert(0, '/app')
timekpr_mod = types.ModuleType('timekpr')
timekpr_mod.__path__ = ['/app']
sys.modules['timekpr'] = timekpr_mod

try:
    from client.sync_client import sync_user, get_user_time, get_user_config
    print(f'Before sync: {get_user_time("/var/lib/timekpr/work", "kid1")}')
    config = get_user_config('/var/lib/timekpr/config', 'kid1')
    print(f'Config Payload: {config}')
    sync_user('/var/lib/timekpr/config', '/var/lib/timekpr/work', 'kid1')
    print(f'After sync: {get_user_time("/var/lib/timekpr/work", "kid1")}')
except Exception as e:
    traceback.print_exc()
