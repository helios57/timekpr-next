# Timekpr-Next Delta Sync Server

This is an add-on sync server and client integration for **Timekpr-Next**. By default, Timekpr limits time usage on a *single* local computer.

Standard file synchronization services (Syncthing, Nextcloud, Dropbox) cannot reliably handle Timekpr's rapidly changing tracking files since they do not resolve overlapping changes gracefully. 

This **Delta-Sync architecture** was built to solve this safely:
1. **The Server**: A central, lightweight FastAPI server (usually running on a 24/7 device like a Raspberry Pi or NAS) that maintains a "global time spent" ledger.
2. **The Client**: Your PCs running `timekprd` will periodically (and immediately upon limit administration changes) compute the *delta* difference in local consumed time, pushing it directly to the server, and effortlessly receiving any global adjustments from other computers.

## How it works

When Alice unlocks a laptop and uses 30 minutes, her local Timekpr instance records 1800 seconds. 
The background `sync_client.py` observes this 1800 second delta and pushes `+1800` to the Sync Server. 
If Alice then switches to her desktop, the desktop's Timekpr pulls that `+1800` from the server, instantly adjusting her local limits *down* by 30 minutes as a Global Adjustment.

## Example Setup Scenario

Imagine a family with 3 children (`alice`, `bob`, `charlie`), having a **Desktop PC** and a **Laptop PC**, and a home **Raspberry Pi**.
* **Overlapping Users**: `alice` and `bob` both use the Desktop and the Laptop randomly.
* **Non-Overlapping User**: `charlie` only uses the Desktop.

### 1. Setting up the Server (The Pi)
On your Raspberry Pi or home server (e.g., IP `192.168.1.50`), use Docker to boot the centralized sync container.

Navigate to this directory (`sync-server`) and run:
```bash
docker compose up -d
```
The server will now be listening on `http://192.168.1.50:8000`.

Alternatively, if you prefer to build the raw image directly:
```bash
docker build -t timekpr-sync-server .
docker run -d --name timekpr-sync -p 8000:8000 -v sync_data:/app/data timekpr-sync-server
```

Or, download the pre-built image directly from the GitHub Container Registry:
```bash
docker pull ghcr.io/mjasnik/timekpr-next-sync-server:main
docker run -d --name timekpr-sync -p 8000:8000 -v sync_data:/app/data ghcr.io/mjasnik/timekpr-next-sync-server:main
```
The server will now be listening on `http://192.168.1.50:8000`.

### 2. Setting up the Clients (Desktop & Laptop)
Ensure the `requests` library is installed globally on both Linux computers:
```bash
sudo apt update && sudo apt install -y python3-requests
```
*(Alternatively, you can install via pip: `sudo pip install requests --break-system-packages`)*

Next, expose your Pi's IP to the Timekpr-next sync client so it knows where to send the deltas. 
Open `/home/helios/workspace/timekpr-next/client/sync_client.py` and update the `SYNC_SERVER_URL` at the top of the file:
```python
SYNC_SERVER_URL = os.environ.get("SYNC_SERVER_URL", "http://192.168.1.50:8000/api/sync")
```

Restart the Timekpr daemon on both machines:
```bash
sudo systemctl restart timekprd
```

### 3. Usage & Testing Example

* When `alice` uses the **Desktop** for 1 hour, the Desktop daemon will push `+3600s` to the Pi.
* Since the Sync Server stores `alice: 3600`, the next time `alice` logs into the **Laptop**, the Laptop's Timekpr will receive a `global_adjustment` of `+3600` and immediately subtract 1 hour from her Laptop time!
* When `charlie` uses the **Desktop**, his time syncs to the Pi too. Even though he never uses the **Laptop**, his time is safely backed up on the Pi.

If an Administrator adds 1 hour to `bob`'s allowed time limit from the DBus Administration menu on the Desktop, Timekpr will automatically broadcast this full configurations schema to the Pi in real-time, instantly unlocking that hour for him on the Laptop as well!
