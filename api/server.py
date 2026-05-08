"""
api/server.py — FastAPI backend cho Nick Farmer UI
Chạy: uvicorn api.server:app --reload --port 8000
"""
import sys
import os
import json
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from config import settings as cfg
from db.connector import DBConnector
from scheduler.schedule_plan import get_plan, SCHEDULE
from utils.logger import log

app = FastAPI(title="Nick Farmer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:4173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db() -> DBConnector:
    return DBConnector(cfg.DB_PATH)

# ─── Scheduler state (in-memory, singleton) ──────────────────────────────────
_scheduler_thread: Optional[threading.Thread] = None
_scheduler_stop   = threading.Event()
_scheduler_instance = None   # APScheduler instance

def _is_scheduler_running() -> bool:
    return (
        _scheduler_instance is not None
        and hasattr(_scheduler_instance, "running")
        and _scheduler_instance.running
    )

# ─── Models ───────────────────────────────────────────────────────────────────
class SetStatusBody(BaseModel):
    status: str

class SetDayBody(BaseModel):
    day: int

# ─── Stats ────────────────────────────────────────────────────────────────────
@app.get("/api/stats")
def get_stats():
    db = get_db()
    accounts = db.get_all_active_accounts()

    # Also include inactive/checkpoint from DB
    all_accs: list[dict] = []
    try:
        with db._connect() as conn:
            rows = conn.execute("SELECT * FROM account_state").fetchall()
        all_accs = [dict(r) for r in rows]
    except Exception:
        all_accs = accounts

    total      = len(all_accs)
    active     = sum(1 for a in all_accs if a.get("status") == "active")
    checkpt    = sum(1 for a in all_accs if a.get("status") == "checkpoint")
    seeding    = sum(1 for a in all_accs if get_plan(a.get("day_number", 1))["allow_seeding"])
    avg_day    = (sum(a.get("day_number", 1) for a in all_accs) / total) if total else 0

    return {
        "total_accounts":     total,
        "active_accounts":    active,
        "checkpoint_accounts": checkpt,
        "sessions_today":     sum(get_plan(a.get("day_number", 1))["sessions"] for a in all_accs if a.get("status") == "active"),
        "seeding_enabled":    seeding,
        "avg_day":            round(avg_day, 1),
    }

# ─── Accounts ─────────────────────────────────────────────────────────────────
@app.get("/api/accounts")
def list_accounts():
    db = get_db()

    # Sync từ accounts.json vào DB trước
    try:
        with open(cfg.ACCOUNTS_FILE, encoding="utf-8") as f:
            json_accs = json.load(f)
        for a in json_accs:
            db.upsert_account(a["user_id"], a.get("name", ""), a.get("day", 1), a.get("status", "inactive"))
    except Exception:
        pass

    try:
        with db._connect() as conn:
            rows = conn.execute("SELECT * FROM account_state ORDER BY day_number DESC").fetchall()
        accounts = [dict(r) for r in rows]
    except Exception:
        accounts = []

    result = []
    for a in accounts:
        day  = a.get("day_number", 1)
        plan = get_plan(day)
        result.append({
            **a,
            "sessions_today": plan["sessions"],
            "allow_seeding":  plan["allow_seeding"],
            "plan_notes":     plan["notes"],
        })
    return result

@app.post("/api/accounts/{user_id}/run")
def run_account(user_id: str):
    """Trigger chạy ngay 1 phiên cho 1 account cụ thể (chạy trong background thread)."""
    db = get_db()
    acc = db.get_account(user_id)
    if not acc:
        raise HTTPException(404, f"Account {user_id} không tìm thấy")
    if acc.get("status") == "banned":
        raise HTTPException(400, "Account bị banned")

    def _run():
        try:
            from adspower_farmer import AdsPowerManager
            from farmer import FacebookFarmer
            import time, random

            manager = AdsPowerManager(api_url=cfg.ADSPOWER_API_URL, api_key=cfg.ADSPOWER_API_KEY)
            day     = acc.get("day_number", 1)
            ws      = manager.start_profile(user_id)
            if not ws:
                db.log_action(user_id, "manual_run", "failed", day)
                return
            time.sleep(random.uniform(5, 10))
            farmer = FacebookFarmer(ws, account_day=day, user_id=user_id)
            result = farmer.run()
            manager.stop_profile(user_id)
            db.log_action(user_id, "manual_run", result, day)
            if result == "ok":
                db.increment_day(user_id)
            elif result == "checkpoint":
                db.mark_checkpoint(user_id)
        except Exception as e:
            log(f"[API] run_account error: {e}", "error")

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return {"success": True, "message": f"Đã bắt đầu chạy phiên cho {user_id} (background)"}

@app.patch("/api/accounts/{user_id}/status")
def set_status(user_id: str, body: SetStatusBody):
    db = get_db()
    acc = db.get_account(user_id)
    if not acc:
        raise HTTPException(404, f"Account {user_id} không tìm thấy")
    db.set_account_status(user_id, body.status)
    return {"success": True, "message": f"Đã cập nhật status → {body.status}"}

@app.patch("/api/accounts/{user_id}/day")
def set_day(user_id: str, body: SetDayBody):
    db = get_db()
    acc = db.get_account(user_id)
    if not acc:
        raise HTTPException(404, f"Account {user_id} không tìm thấy")
    with db._connect() as conn:
        conn.execute("UPDATE account_state SET day_number = ? WHERE user_id = ?", (body.day, user_id))
    return {"success": True, "message": f"Đã reset ngày → {body.day}"}

# ─── Schedule ─────────────────────────────────────────────────────────────────
@app.get("/api/schedule")
def list_schedule():
    return [
        {
            "day": day,
            "sessions": plan["sessions"],
            "window":   plan["window"],
            "allow_seeding": plan["allow_seeding"],
            "notes":    plan["notes"],
            "actions":  plan["actions"],
        }
        for day, plan in sorted(SCHEDULE.items())
    ]

@app.get("/api/schedule/{day}")
def get_day_plan(day: int):
    plan = get_plan(day)
    return {"day": day, **{k: v for k, v in plan.items()}}

# ─── Logs ─────────────────────────────────────────────────────────────────────
@app.get("/api/logs")
def get_logs(limit: int = 100):
    db = get_db()
    try:
        with db._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM session_logs ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []

@app.get("/api/logs/{user_id}")
def get_account_logs(user_id: str):
    db = get_db()
    return db.get_session_logs(user_id, limit=100)

# ─── Scheduler control ────────────────────────────────────────────────────────
@app.get("/api/scheduler/status")
def scheduler_status():
    running = _is_scheduler_running()
    next_run = None
    if running and _scheduler_instance:
        job = _scheduler_instance.get_job("daily_farm")
        if job and job.next_run_time:
            next_run = job.next_run_time.isoformat()
    return {
        "running":  running,
        "next_run": next_run,
        "timezone": cfg.SCHEDULER_TIMEZONE,
        "hour":     cfg.SCHEDULER_HOUR,
        "minute":   cfg.SCHEDULER_MINUTE,
    }

@app.post("/api/scheduler/start")
def start_scheduler():
    global _scheduler_instance
    if _is_scheduler_running():
        return {"success": False, "message": "Scheduler đang chạy rồi"}

    def _launch():
        global _scheduler_instance
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        from scheduler.daily_runner import daily_farm_job

        sched = BackgroundScheduler(timezone=cfg.SCHEDULER_TIMEZONE)
        sched.add_job(
            daily_farm_job,
            trigger=CronTrigger(hour=cfg.SCHEDULER_HOUR, minute=cfg.SCHEDULER_MINUTE),
            id="daily_farm",
            name="Daily Farm",
            max_instances=1,
        )
        sched.start()
        _scheduler_instance = sched
        log("[API] Scheduler started.")

    t = threading.Thread(target=_launch, daemon=True)
    t.start()
    import time; time.sleep(0.5)
    return {"success": True, "message": "Scheduler đã khởi động"}

@app.post("/api/scheduler/stop")
def stop_scheduler():
    global _scheduler_instance
    if not _is_scheduler_running():
        return {"success": False, "message": "Scheduler chưa chạy"}
    try:
        _scheduler_instance.shutdown(wait=False)
        _scheduler_instance = None
        return {"success": True, "message": "Scheduler đã dừng"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/scheduler/trigger")
def trigger_now():
    """Chạy job ngay lập tức (1 lần) trong background thread."""
    def _run():
        from scheduler.daily_runner import daily_farm_job
        daily_farm_job()

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return {"success": True, "message": "Đã trigger job ngay lập tức (chạy background)"}
