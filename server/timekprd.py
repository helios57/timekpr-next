"""
Created on Aug 28, 2018

@author: mjasnik
"""

# imports
import os
import sys
import dbus
# distro detection
try:
    # try to load distro module
    import distro
    # if successful, mark it so
    _DISTRO_AVAILABLE = True
except (ImportError, ValueError):
    # if successful, mark it so
    _DISTRO_AVAILABLE = False

# set up our python path
if "/usr/lib/python3/dist-packages" not in sys.path:
    sys.path.append("/usr/lib/python3/dist-packages")

# imports
import signal

# timekpr imports
from timekpr.common.constants import constants as cons
from timekpr.common.log import log
from timekpr.server.interface.dbus.daemon import timekprDaemon
from timekpr.common.utils import misc
from timekpr.server.config.userhelper import timekprUserStore
from timekpr.common.utils.config import timekprConfig
import time
import threading


# main start
if __name__ == "__main__":
    # simple self-running check
    if misc.checkAndSetRunning(os.path.splitext(os.path.basename(__file__))[0]):
        # get out
        sys.exit(0)

    log.log(cons.TK_LOG_LEVEL_INFO, "--- initiating timekpr v. %s ---" % (cons.TK_VERSION))
    # get uname
    uname = os.uname()
    log.log(cons.TK_LOG_LEVEL_INFO, "running on: %s, %s, %s, %s" % (uname[0], uname[2], uname[3], uname[4]))
    # distro
    if _DISTRO_AVAILABLE:
        log.log(cons.TK_LOG_LEVEL_INFO, "distribution: %s, %s, %s" % (distro.id(), distro.name(), distro.version()))
    log.log(cons.TK_LOG_LEVEL_INFO, "using python: %s" % (sys.version))
    log.log(cons.TK_LOG_LEVEL_INFO, "dbus python: %s" % (dbus.__version__))
    log.log(cons.TK_LOG_LEVEL_INFO, "---")

    # get daemon class
    _timekprDaemon = timekprDaemon()

    # this is needed for appindicator to react to ctrl+c
    signal.signal(signal.SIGINT, _timekprDaemon.finishTimekpr)
    signal.signal(signal.SIGTERM, _timekprDaemon.finishTimekpr)

    # prepare all users in the system
    timekprUserStore().checkAndInitUsers()

    # init daemon
    _timekprDaemon.initTimekpr()

    # start daemon threads
    _timekprDaemon.startTimekprDaemon()

    # Sync client hook
    def run_sync_client():
        try:
            # Check locally available users to sync
            users = timekprUserStore().getSavedUserList()
            cfgManager = timekprConfig()
            cfgManager.loadMainConfiguration()
            
            import sys
            import os
            
            try:
                # Add timekpr root if not installed system-wide
                sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
                from client import sync_client
                for u in users:
                    sync_client.sync_user(cfgManager.getTimekprConfigDir(), cfgManager.getTimekprWorkDir(), u[0])
            except Exception as e:
                log.log(cons.TK_LOG_LEVEL_INFO, f"Sync client run failed to execute: {str(e)}")
        except Exception as e:
            log.log(cons.TK_LOG_LEVEL_INFO, f"Sync background thread failed: {str(e)}")

    def sync_loop():
        # Delay on startup, so the system network wait target has time to come up
        time.sleep(15)
        while True:
            run_sync_client()
            time.sleep(60)

    sync_thread = threading.Thread(target=sync_loop, daemon=True)
    sync_thread.start()
