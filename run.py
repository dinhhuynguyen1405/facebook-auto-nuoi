#!/usr/bin/env python3
"""
run.py — Entry point duy nhất của Facebook Farmer.

Cách dùng:
  python run.py                  # Menu tương tác
  python run.py ui               # Khởi động Farmer UI (API + mở browser)
  python run.py api              # Chỉ khởi động API server (port 8000)
  python run.py farmer           # Chạy 1 lần ngay
  python run.py scheduler        # Chạy daemon lên lịch hàng ngày
  python run.py scheduler --once # Trigger ngay 1 lần (test)
  python run.py seeding          # Chạy seeding job
  python run.py check            # Kiểm tra config
  python run.py status           # Xem trạng thái nick
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import log


# ──────────────────────────────────────────────────────
# BANNER & DEPS
# ──────────────────────────────────────────────────────
def _print_banner():
    print("""
╔══════════════════════════════════════════════════════════╗
║           FACEBOOK FARMER — Badminton GO                 ║
╠══════════════════════════════════════════════════════════╣
║  [1] Khởi động Farmer UI  (API + React dashboard)        ║
║  [2] Chạy Daily Scheduler (daemon — chạy nền mỗi ngày)   ║
║  [3] Trigger Scheduler ngay 1 lần (test)                  ║
║  [4] Chạy Farmer 1 lần ngay (manual)                     ║
║  [5] Chạy Seeding Job (comment bài đăng chờ)             ║
║  [6] Xem trạng thái nick (status dashboard)              ║
║  [7] Kiểm tra cấu hình (.env + accounts)                 ║
║  [8] Xem logs gần nhất                                   ║
║  [0] Thoát                                               ║
╚══════════════════════════════════════════════════════════╝
""")


def _check_deps():
    missing = []
    for pkg, imp in [
        ("playwright",   "playwright"),
        ("requests",     "requests"),
        ("dotenv",       "dotenv"),
        ("apscheduler",  "apscheduler"),
    ]:
        try:
            __import__(imp)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"\n[LỖI] Chưa cài đầy đủ dependencies: {', '.join(missing)}")
        print("Chạy lệnh:\n  pip install -r requirements.txt")
        print("Rồi cài Playwright:\n  playwright install chromium")
        sys.exit(1)


# ──────────────────────────────────────────────────────
# CÁC CHẾ ĐỘ
# ──────────────────────────────────────────────────────
def run_ui():
    """Khởi động API server + mở browser tới React dashboard."""
    import subprocess, webbrowser, threading, time
    log("=== CHẾ ĐỘ FARMER UI ===")
    print("  Khởi động FastAPI backend tại http://localhost:8000 ...")
    print("  Mở http://localhost:5174 trong browser sau 2 giây")
    print("  Nhấn Ctrl+C để dừng.\n")

    def _open_browser():
        time.sleep(2)
        webbrowser.open("http://localhost:5174")

    threading.Thread(target=_open_browser, daemon=True).start()
    os.execlp("uvicorn", "uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000", "--reload")


def run_api():
    """Chỉ khởi động API server (không mở browser)."""
    log("=== CHẾ ĐỘ API SERVER ===")
    print("  FastAPI tại http://localhost:8000")
    print("  Nhấn Ctrl+C để dừng.\n")
    os.execlp("uvicorn", "uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000", "--reload")


def run_farmer():
    log("=== CHẾ ĐỘ FARMER — 1 LẦN ===")
    from farmer import main
    main()


def run_scheduler(once: bool = False):
    if once:
        log("=== SCHEDULER — TRIGGER NGAY 1 LẦN ===")
        from scheduler.daily_runner import daily_farm_job
        daily_farm_job()
    else:
        log("=== CHẾ ĐỘ SCHEDULER — DAEMON ===")
        from scheduler.daily_runner import run_scheduler as _run
        _run()


def run_seeding():
    log("=== CHẾ ĐỘ SEEDING ===")
    from jobs.seeding_job import run_seeding_job
    run_seeding_job()


def show_status():
    """Dashboard trạng thái tất cả nick — lấy từ DB."""
    print()
    try:
        from config import settings as cfg
        from db.connector import DBConnector
        from scheduler.schedule_plan import get_plan

        db = DBConnector(cfg.DB_PATH)
        accounts = db.get_all_active_accounts()

        if not accounts:
            print("  (Chưa có account nào trong DB. Chạy farmer hoặc check trước.)\n")
            return

        STATUS_ICON = {
            "active":     "🟢",
            "checkpoint": "🚨",
            "inactive":   "⚫",
            "banned":     "💀",
        }
        print(f"  {'Nick':<20} {'ID':<16} {'Ngày':>5} {'Phiên/ngày':>10} {'Seeding':>8} {'Trạng thái':<12} {'Chạy cuối'}")
        print("  " + "─" * 100)
        for acc in accounts:
            uid    = acc["user_id"]
            name   = acc.get("name", uid)[:18]
            day    = acc.get("day_number", 1)
            status = acc.get("status", "active")
            last   = acc.get("last_run") or "chưa chạy"
            plan   = get_plan(day)
            chk    = acc.get("checkpoint_count", 0)

            icon   = STATUS_ICON.get(status, "❓")
            seed   = "✅" if plan["allow_seeding"] else "🚫"
            chk_s  = f" (cp:{chk})" if chk > 0 else ""

            print(f"  {name:<20} {uid:<16} {day:>5} {plan['sessions']:>10} {seed:>8} {icon} {status:<10}{chk_s}  {last}")

        print()
        print(f"  Tổng: {len(accounts)} account active | DB: {cfg.DB_PATH}")
        print()
    except Exception as e:
        print(f"\n  Lỗi đọc status: {e}\n")


def check_config():
    print("\n── Kiểm tra cấu hình ────────────────────────────────")
    try:
        from config import settings as cfg
        cfg.validate()

        print(f"  ✅ ADSPOWER_API_KEY  : {'✓ có' if cfg.ADSPOWER_API_KEY else '✗ thiếu'}")
        print(f"  ✅ GEMINI_API_KEY    : {'✓ có' if cfg.GEMINI_API_KEY else '⚠ trống → spintax fallback'}")
        print(f"  ✅ ACCOUNTS_FILE     : {cfg.ACCOUNTS_FILE}")
        print(f"  ✅ DB_PATH           : {cfg.DB_PATH}")
        print(f"  ✅ LOG_FILE          : {cfg.LOG_FILE}")
        print(f"  ✅ Scheduler         : {cfg.SCHEDULER_HOUR:02d}:{cfg.SCHEDULER_MINUTE:02d} ({cfg.SCHEDULER_TIMEZONE})")
        print(f"  ✅ Inter-session     : {cfg.INTER_SESSION_MIN_SEC//60}–{cfg.INTER_SESSION_MAX_SEC//60} phút")

        import json
        with open(cfg.ACCOUNTS_FILE, encoding="utf-8") as f:
            accounts = json.load(f)
        active = [a for a in accounts if a.get("status") == "active"]
        print(f"\n  ✅ Accounts (JSON)   : {len(active)} active / {len(accounts)} total")

        from scheduler.schedule_plan import get_plan
        for a in active:
            day  = a.get("day", 1)
            plan = get_plan(day)
            print(f"       - {a.get('name','?'):<20} user_id={a.get('user_id'):<15} "
                  f"ngày={day:<3} phiên={plan['sessions']}  seeding={'✅' if plan['allow_seeding'] else '🚫'}")
            print(f"         └─ {plan['notes']}")

        print("\n  ✅ Cấu hình hợp lệ. Sẵn sàng chạy!\n")
    except EnvironmentError as e:
        print(f"\n  ❌ {e}\n")
    except Exception as e:
        print(f"\n  ❌ Lỗi: {e}\n")


def view_logs():
    try:
        from config.settings import LOG_FILE
        if not os.path.exists(LOG_FILE):
            print("\n  (Chưa có file log)\n")
            return
        print(f"\n── {LOG_FILE} (60 dòng cuối) ─────────────────────────")
        with open(LOG_FILE, encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines[-60:]:
            print(line, end="")
        print("\n─────────────────────────────────────────────────────\n")
    except Exception as e:
        print(f"\n  Lỗi đọc log: {e}\n")


# ──────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────
def main():
    _check_deps()

    # CLI mode: python run.py <command> [--once]
    if len(sys.argv) > 1:
        cmd  = sys.argv[1].lower()
        once = "--once" in sys.argv

        dispatch = {
            "ui":        lambda: run_ui(),
            "api":       lambda: run_api(),
            "farmer":    lambda: run_farmer(),
            "1":         lambda: run_farmer(),
            "scheduler": lambda: run_scheduler(once=once),
            "2":         lambda: run_scheduler(once=once),
            "seeding":   lambda: run_seeding(),
            "seed":      lambda: run_seeding(),
            "status":    lambda: show_status(),
            "check":     lambda: check_config(),
            "config":    lambda: check_config(),
            "logs":      lambda: view_logs(),
        }
        fn = dispatch.get(cmd)
        if fn:
            fn()
        else:
            cmds = " | ".join(dispatch.keys())
            print(f"Không nhận ra lệnh '{cmd}'.\nDùng: {cmds}")
            sys.exit(1)
        return

    # Interactive menu
    handlers = {
        "1": run_ui,
        "2": lambda: run_scheduler(once=False),
        "3": lambda: run_scheduler(once=True),
        "4": run_farmer,
        "5": run_seeding,
        "6": show_status,
        "7": check_config,
        "8": view_logs,
    }
    while True:
        _print_banner()
        choice = input("Chọn chế độ: ").strip()
        if choice == "0":
            print("Thoát.")
            sys.exit(0)
        fn = handlers.get(choice)
        if fn:
            fn()
        else:
            print("Lựa chọn không hợp lệ.\n")


if __name__ == "__main__":
    main()
