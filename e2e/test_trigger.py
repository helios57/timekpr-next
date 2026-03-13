import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from timekpr.common.utils.config import timekprUserConfig

def main():
    config_dir = "/var/lib/timekpr/config"
    username = "testuser"
    cfg = timekprUserConfig(config_dir, username)
    cfg.initUserConfiguration(True)
    cfg._timekprUserConfig["LIMIT_PER_DAY"] = "120"
    cfg.saveUserConfiguration()
    print("Saved user configuration!")

if __name__ == "__main__":
    main()
