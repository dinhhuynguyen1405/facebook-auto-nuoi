"""
Module: config/settings.py
Chứa tất cả biến cấu hình của hệ thống.
Tất cả path đều là absolute để tránh lỗi chạy từ thư mục khác.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────
# ROOT DIRECTORY (luôn là thư mục chứa file này)
# ──────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ──────────────────────────────────────────
# DATABASE
# ──────────────────────────────────────────
# DB nội bộ của farmer (lưu trạng thái seeding, log phiên)
DB_PATH = os.path.join(BASE_DIR, "farmer.db")

# DB của facebook-tools (nếu dùng chung) - fallback về DB nội bộ nếu không tồn tại
_TOOLS_DB = os.path.join(BASE_DIR, "..", "facebook-tools", "data.db")
TOOLS_DB_PATH = _TOOLS_DB if os.path.exists(_TOOLS_DB) else DB_PATH

# ──────────────────────────────────────────
# ADSPOWER
# ──────────────────────────────────────────
ADSPOWER_API_KEY  = os.getenv("ADSPOWER_API_KEY", "")
ADSPOWER_API_URL  = os.getenv("ADSPOWER_API_URL", "http://local.adspower.net:50325")

# ──────────────────────────────────────────
# AI (GEMINI)
# ──────────────────────────────────────────
GEMINI_API_KEY    = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL      = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ──────────────────────────────────────────
# BADMINTON GO LINK
# ──────────────────────────────────────────
WEB_LINK_TEMPLATE = os.getenv("WEB_LINK_TEMPLATE", "https://badminton-go.vn/post/{post_id}")

# ──────────────────────────────────────────
# FARMER BEHAVIOUR TUNABLES
# ──────────────────────────────────────────
# Số action lớn tối đa / phiên (override bằng .env nếu muốn)
SESSION_ACTIONS_MIN  = int(os.getenv("SESSION_ACTIONS_MIN", "3"))
SESSION_ACTIONS_MAX  = int(os.getenv("SESSION_ACTIONS_MAX", "5"))

# Giới hạn tương tác nặng/phiên trước khi bắt đầu throttle
MAX_ENGAGEMENTS_PER_SESSION = int(os.getenv("MAX_ENGAGEMENTS_PER_SESSION", "8"))

# Xác suất human-breathe pause sau mỗi action (0.0 – 1.0)
BREATHE_PAUSE_PROBABILITY = float(os.getenv("BREATHE_PAUSE_PROBABILITY", "0.10"))
BREATHE_PAUSE_MIN_SEC     = int(os.getenv("BREATHE_PAUSE_MIN_SEC", "30"))
BREATHE_PAUSE_MAX_SEC     = int(os.getenv("BREATHE_PAUSE_MAX_SEC", "90"))

# ──────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────
LOG_DIR  = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "farmer.log")

# ──────────────────────────────────────────
# ACCOUNTS FILE
# ──────────────────────────────────────────
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")

# ──────────────────────────────────────────
# SCHEDULER (APScheduler)
# ──────────────────────────────────────────
# Giờ chạy job hàng ngày (mặc định 09:30 sáng)
SCHEDULER_HOUR     = int(os.getenv("SCHEDULER_HOUR", "9"))
SCHEDULER_MINUTE   = int(os.getenv("SCHEDULER_MINUTE", "30"))
SCHEDULER_TIMEZONE = os.getenv("SCHEDULER_TIMEZONE", "Asia/Ho_Chi_Minh")

# Delay ngẫu nhiên GIỮA các phiên trong ngày (giây)
# Mặc định: 45 phút – 2 giờ 30 phút
INTER_SESSION_MIN_SEC = int(os.getenv("INTER_SESSION_MIN_SEC", str(45 * 60)))
INTER_SESSION_MAX_SEC = int(os.getenv("INTER_SESSION_MAX_SEC", str(150 * 60)))


def validate():
    """Kiểm tra các config bắt buộc trước khi chạy. Raise nếu thiếu."""
    errors = []
    if not ADSPOWER_API_KEY:
        errors.append("ADSPOWER_API_KEY chưa được set trong .env")
    if not os.path.exists(ACCOUNTS_FILE):
        errors.append(f"Không tìm thấy file accounts: {ACCOUNTS_FILE}")
    if errors:
        raise EnvironmentError(
            "\n[CONFIG ERROR] Thiếu cấu hình bắt buộc:\n  - " + "\n  - ".join(errors)
        )
