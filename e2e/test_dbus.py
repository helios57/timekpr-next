import subprocess

# This script manually triggers a DBus command to change user limits on client1
# We'll monitor the docker log output to see if sync_client is called.
def main():
    print("Sending limit config change to DBus...")
    # we can use the timekpr-gui or directly call dbus-send on client1
    cmd = [
        "docker", "compose", "exec", "client1",
        "python3", "-c", 
        "import dbus; bus = dbus.SystemBus(); obj = bus.get_object('com.ubuntu.Timekpr', '/com/ubuntu/Timekpr/a'); iface = dbus.Interface(obj, 'com.ubuntu.Timekpr'); iface.setAllowedDays('testuser', [1, 2, 3, 4, 5, 6, 7])"
    ]
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
