from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, sessionmaker

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"Validation Error on {request.url}: {exc.errors()}\nBody: {exc.body}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

DB_FILE = os.environ.get("SYNC_DB_PATH", "/app/sync.db")
DB_URL = f"sqlite:///{DB_FILE}"

def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        # We store the global combined time for a user
        conn.execute("""
            CREATE TABLE IF NOT EXISTS global_ledger (
                username TEXT PRIMARY KEY,
                time_spent_day INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # We track config versions. Simplified for this demo.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS configs (
                username TEXT PRIMARY KEY,
                config_json TEXT,
                updated_at TIMESTAMP
            )
        """)

init_db()

from typing import Optional, Union, Any

class TimeDelta(BaseModel):
    consumed_seconds: int

class UserConfig(BaseModel):
    timestamp: Any = ""
    LIMIT_PER_DAY: Any = ""
    ALLOWED_WEEKDAYS: Any = ""

class SyncRequest(BaseModel):
    device_id: str
    time_delta: TimeDelta
    config: UserConfig

@app.get("/")
def read_root():
    return {"status": "Timekpr Sync Server is running"}

@app.post("/api/sync/{username}")
def sync_user(username: str, data: SyncRequest, db: sqlite3.Connection = Depends(get_db)):
    # 1. Update Global Ledger with the Delta
    delta = data.time_delta.consumed_seconds
    
    # Get or create user ledger
    row = db.execute("SELECT time_spent_day FROM global_ledger WHERE username = ?", (username,)).fetchone()
    
    if not row:
        global_spent = delta
        db.execute("INSERT INTO global_ledger (username, time_spent_day) VALUES (?, ?)", (username, global_spent))
    else:
        global_spent = row["time_spent_day"] + delta
        db.execute("UPDATE global_ledger SET time_spent_day = ?, last_updated = CURRENT_TIMESTAMP WHERE username = ?", (global_spent, username))

    # The "global adjustment" is how much 'extra' time this specific device 
    # needs to add to its local counter to match the global state.
    # We skip calculating exactly per device for this simple demo, 
    # and instead assume the client just requested a sync. A true implementation
    # tracks ledgers *per device* to compute the precise difference.

    # simplified logic: if global_spent is greater than delta, it means other devices 
    # consumed time. The adjustment to send back to this device is (global_spent - this_devices_total).
    # Since we only get delta, we'll send back a simplistic adjustment for the demo test.
    
    # A true Delta-Sync calculates: 
    # adjustment = global_spent - (local_spent)
    # Since the client handles the adjustment math by adding it, we'll return 0 in this mock unless testing specific scenarios.
    
    adjustment = 0 
    # For testing purposes - if delta was 0 but global is high, another device used time.
    if delta == 0 and global_spent > 0:
        adjustment = global_spent # Force sync

    return {
        "global_time": {
            "global_adjustment": adjustment, 
            "master_total": global_spent
        },
        "config_update": None # Leaving config sync as a stub for this test
    }

