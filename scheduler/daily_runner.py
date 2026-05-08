"""
scheduler/daily_runner.py
──────────────────────────────────────────────────────────────────────────────
Hệ thống lên lịch chạy farm tự động mỗi ngày.

Luồng hoạt động:
  1. APScheduler khởi động, đăng ký job `daily_farm_job` theo cron hằng ngày.
  2. Mỗi ngày vào giờ đã cấu hình, job:
       a. Đọc tất cả accounts active từ DB
       b. Lọc theo khung giờ hợp lệ của ngày nuôi đó (schedule_plan.window)
       c. Với mỗi account, chạy đủ số phiên (plan.sessions) với delay ngẫu nhiên
          giữa các phiên để không chạy liên tiếp như bot
       d. Tự động increment day trong DB sau mỗi phiên thành công
  3. Nếu nick checkpoint → đánh dấu, skip, không increment

Cách dùng:
  python scheduler/daily_runner.py          # Chạy daemon giữ tiến trình
  python scheduler/daily_runner.py --once   # Chạy ngay 1 lần rồi thoát (test)
──────────────────────────────────────────────────────────────────────────────
"""
import sys
import os
import json
import time
import random
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

from config import settings as cfg
from db.connector import DBConnector
from utils.logger import log
from adspower_farmer import AdsPowerManager
from scheduler.schedule_plan import get_plan, get_window_hours


# ──────────────────────────────────────────────────────────────────────────────
# HELPER: đọc accounts.json → sync vào DB
# ──────────────────────────────────────────────────────────────────────────────
def _sync_accounts_to_db(db: DBConnector) -> list[dict]:
    """Đọc accounts.json, sync vào DB, trả về danh sách active."""
    try:
        with open(cfg.ACCOUNTS_FILE, encoding="utf-8") as f:
            accounts = json.load(f)
    except Exception as e:
        log(f"[Runner] Không đọc được accounts.json: {e}", "error")
        return []

    for acc in accounts:
        uid   = acc.get("user_id", "")
        name  = acc.get("name", uid)
        day   = acc.get("day", 1)
        status = acc.get("status", "inactive")
        if uid:
            db.upsert_account(uid, name=name, day_number=day, status=status)

    return [a for a in accounts if a.get("status") == "active"]


# ──────────────────────────────────────────────────────────────────────────────
# CORE: chạy một phiên cho một account
# ──────────────────────────────────────────────────────────────────────────────
def _run_session_for_account(
    acc_state: dict,
    manager: AdsPowerManager,
    db: DBConnector,
) -> str:
    """
    Mở browser, chạy 1 phiên FacebookFarmer, đóng lại.
    Trả về: 'ok' | 'checkpoint' | 'error' | 'skip'
    """
    from farmer import FacebookFarmer   # import ở đây để tránh circular

    user_id = acc_state["user_id"]
    name    = acc_state.get("name", user_id)
    day     = acc_state.get("day_number", 1)
    plan    = get_plan(day)

    # Kiểm tra khung giờ hợp lệ
    from datetime import datetime
    now_hour = datetime.now().hour
    h_start, h_end = get_window_hours(plan)
    if not (h_start <= now_hour < h_end):
        log(f"[Runner] {name} — ngoài khung giờ {plan['window']}, bỏ qua phiên này.")
        return "skip"

    log(f"[Runner] ▶ Bắt đầu phiên | {name} | Ngày {day} | {plan['notes']}")

    ws_endpoint = manager.start_profile(user_id)
    if not ws_endpoint:
        log(f"[Runner] {name} — không mở được browser.", "error")
        db.log_action(user_id, "start_profile", "failed", day)
        return "error"

    # Delay tự nhiên sau khi browser mở (browser cần thời gian load)
    time.sleep(random.uniform(6, 12))

    farmer = FacebookFarmer(ws_endpoint, account_day=day, user_id=user_id)
    result = farmer.run()
    manager.stop_profile(user_id)

    db.log_action(user_id, "session", result, day)

    if result == "checkpoint":
        db.mark_checkpoint(user_id)
        log(f"[Runner] 🚨 {name} — Checkpoint! Dừng account, cần xử lý thủ công.", "error")
    elif result == "ok":
        # Chỉ increment sau phiên cuối của ngày (daily_runner tự quản)
        log(f"[Runner] ✅ {name} — Phiên OK.")
    else:
        log(f"[Runner] ⚠️ {name} — Phiên lỗi.", "warning")

    return result


# ──────────────────────────────────────────────────────────────────────────────
# JOB CHÍNH: chạy tất cả accounts theo đúng số phiên trong ngày
# ──────────────────────────────────────────────────────────────────────────────
def daily_farm_job():
    log("\n" + "═" * 55)
    log("DAILY FARM JOB — BẮT ĐẦU")
    log("═" * 55)

    db = DBConnector(cfg.DB_PATH)
    _sync_accounts_to_db(db)

    active_states = db.get_all_active_accounts()
    if not active_states:
        log("[Runner] Không có account active nào.")
        return

    manager = AdsPowerManager(
        api_url=cfg.ADSPOWER_API_URL,
        api_key=cfg.ADSPOWER_API_KEY,
    )

    for acc_state in active_states:
        user_id = acc_state["user_id"]
        name    = acc_state.get("name", user_id)
        day     = acc_state.get("day_number", 1)
        plan    = get_plan(day)
        sessions_today = plan["sessions"]

        log(f"\n[Runner] {'─'*45}")
        log(f"[Runner] Account: {name} | Ngày {day} | {sessions_today} phiên hôm nay")

        sessions_done = 0
        for session_idx in range(sessions_today):
            log(f"[Runner] {name} — Phiên {session_idx + 1}/{sessions_today}")

            result = _run_session_for_account(acc_state, manager, db)

            if result == "checkpoint":
                log(f"[Runner] {name} — Dừng hẳn hôm nay do checkpoint.")
                break

            sessions_done += 1

            # Delay ngẫu nhiên giữa các phiên trong ngày (45 phút – 3 giờ)
            # Mô phỏng người dùng thật: dùng điện thoại nhiều lần trong ngày
            if session_idx < sessions_today - 1:
                inter_session_delay = random.uniform(
                    cfg.INTER_SESSION_MIN_SEC,
                    cfg.INTER_SESSION_MAX_SEC,
                )
                log(f"[Runner] {name} — Nghỉ {inter_session_delay/60:.0f} phút trước phiên tiếp theo...")
                time.sleep(inter_session_delay)

        # Increment day sau khi hoàn thành ≥ 1 phiên thành công
        if sessions_done >= 1:
            db.increment_day(user_id)
            log(f"[Runner] {name} — Hoàn thành ngày {day} → ngày {day + 1}.")

        # Delay giữa các accounts (tránh cùng lúc)
        time.sleep(random.uniform(10, 30))

    log("\n" + "═" * 55)
    log("DAILY FARM JOB — KẾT THÚC")
    log("═" * 55)


# ──────────────────────────────────────────────────────────────────────────────
# SCHEDULER SETUP
# ──────────────────────────────────────────────────────────────────────────────
def _job_listener(event):
    if event.exception:
        log(f"[Scheduler] ❌ Job lỗi: {event.exception}", "error")
    else:
        log(f"[Scheduler] ✅ Job hoàn thành lúc {event.scheduled_run_time}.")


def run_scheduler():
    """Khởi động APScheduler daemon — chạy job hàng ngày theo cấu hình."""
    log("[Scheduler] Khởi động Daily Farm Scheduler...")
    log(f"[Scheduler] Giờ chạy hàng ngày: {cfg.SCHEDULER_HOUR:02d}:{cfg.SCHEDULER_MINUTE:02d}")
    log("[Scheduler] Nhấn Ctrl+C để dừng.\n")

    scheduler = BlockingScheduler(timezone=cfg.SCHEDULER_TIMEZONE)
    scheduler.add_listener(_job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    scheduler.add_job(
        daily_farm_job,
        trigger=CronTrigger(
            hour=cfg.SCHEDULER_HOUR,
            minute=cfg.SCHEDULER_MINUTE,
            timezone=cfg.SCHEDULER_TIMEZONE,
        ),
        id="daily_farm",
        name="Daily Farm Job",
        max_instances=1,          # Không chạy 2 lần đồng thời
        misfire_grace_time=3600,  # Bỏ qua nếu trễ hơn 1 tiếng
    )

    # In job tiếp theo
    job = scheduler.get_job("daily_farm")
    log(f"[Scheduler] Job tiếp theo: {job.next_run_time}")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log("[Scheduler] Đã dừng scheduler.")


# ──────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────
def main():
    # Validate config
    try:
        cfg.validate()
    except EnvironmentError as e:
        log(str(e), "error")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Facebook Farmer Daily Runner")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Chạy ngay 1 lần rồi thoát (không cần đợi đến giờ cron)",
    )
    args = parser.parse_args()

    if args.once:
        log("[Runner] Chế độ --once: chạy ngay lập tức...")
        daily_farm_job()
    else:
        run_scheduler()


if __name__ == "__main__":
    main()
