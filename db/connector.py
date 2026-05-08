"""
Module: db/connector.py
Chức năng: Kết nối SQLite, tự tạo schema nếu chưa tồn tại.
"""
import sqlite3
import os
from typing import List, Dict, Any


class DBConnector:
    def __init__(self, db_path: str):
        self.db_path = db_path
        # Tạo thư mục chứa DB nếu chưa có
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._init_schema()

    # ──────────────────────────────────────────
    # SCHEMA AUTO-INIT
    # ──────────────────────────────────────────
    def _init_schema(self):
        """Tạo bảng nếu chưa tồn tại — an toàn để gọi nhiều lần."""
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS posts (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    url             TEXT NOT NULL,
                    post_type       TEXT DEFAULT 'general',
                    content         TEXT DEFAULT '',
                    seeding_status  TEXT DEFAULT 'pending',
                    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
                    seeded_at       DATETIME
                );

                CREATE TABLE IF NOT EXISTS session_logs (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id      TEXT NOT NULL,
                    action          TEXT NOT NULL,
                    result          TEXT DEFAULT 'ok',
                    day_number      INTEGER DEFAULT 1,
                    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                -- Bảng track trạng thái nuôi từng nick
                CREATE TABLE IF NOT EXISTS account_state (
                    user_id         TEXT PRIMARY KEY,
                    name            TEXT DEFAULT '',
                    day_number      INTEGER DEFAULT 1,
                    status          TEXT DEFAULT 'active',
                    last_run        DATETIME,
                    last_checkpoint DATETIME,
                    checkpoint_count INTEGER DEFAULT 0,
                    notes           TEXT DEFAULT '',
                    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)

    # ──────────────────────────────────────────
    # CONNECTION HELPER
    # ──────────────────────────────────────────
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ──────────────────────────────────────────
    # POSTS
    # ──────────────────────────────────────────
    def fetch_pending_posts(self) -> List[Dict[str, Any]]:
        """Lấy các bài post cần seeding (seeding_status = 'pending')."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, url, post_type, content FROM posts WHERE seeding_status = 'pending' ORDER BY id"
            ).fetchall()
        return [dict(r) for r in rows]

    def update_seeding_status(self, post_id: int, status: str):
        with self._connect() as conn:
            conn.execute(
                "UPDATE posts SET seeding_status = ?, seeded_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, post_id)
            )

    def insert_post(self, url: str, post_type: str = "general", content: str = "") -> int:
        """Thêm bài post mới vào hàng đợi seeding. Trả về id mới."""
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO posts (url, post_type, content) VALUES (?, ?, ?)",
                (url, post_type, content)
            )
            return cur.lastrowid

    # ──────────────────────────────────────────
    # SESSION LOGS
    # ──────────────────────────────────────────
    def log_action(self, account_id: str, action: str, result: str = "ok", day_number: int = 1):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO session_logs (account_id, action, result, day_number) VALUES (?, ?, ?, ?)",
                (account_id, action, result, day_number)
            )

    def get_session_logs(self, account_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM session_logs WHERE account_id = ? ORDER BY created_at DESC LIMIT ?",
                (account_id, limit)
            ).fetchall()
        return [dict(r) for r in rows]

    # ──────────────────────────────────────────
    # ACCOUNT STATE (tracking ngày nuôi)
    # ──────────────────────────────────────────
    def upsert_account(self, user_id: str, name: str = "", day_number: int = 1, status: str = "active"):
        """Tạo mới hoặc cập nhật record account. Không reset day nếu đã tồn tại."""
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT user_id FROM account_state WHERE user_id = ?", (user_id,)
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE account_state SET name = ?, status = ? WHERE user_id = ?",
                    (name, status, user_id)
                )
            else:
                conn.execute(
                    "INSERT INTO account_state (user_id, name, day_number, status) VALUES (?, ?, ?, ?)",
                    (user_id, name, day_number, status)
                )

    def get_account(self, user_id: str) -> Dict[str, Any]:
        """Lấy trạng thái nuôi của một account. Trả về {} nếu không có."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM account_state WHERE user_id = ?", (user_id,)
            ).fetchone()
        return dict(row) if row else {}

    def get_all_active_accounts(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM account_state WHERE status = 'active' ORDER BY user_id"
            ).fetchall()
        return [dict(r) for r in rows]

    def increment_day(self, user_id: str):
        """Tăng số ngày nuôi lên 1 sau khi hoàn thành phiên hôm nay."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE account_state SET day_number = day_number + 1, last_run = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )

    def mark_checkpoint(self, user_id: str):
        """Ghi nhận nick vừa gặp checkpoint — để theo dõi."""
        with self._connect() as conn:
            conn.execute(
                """UPDATE account_state
                   SET last_checkpoint = CURRENT_TIMESTAMP,
                       checkpoint_count = checkpoint_count + 1,
                       status = 'checkpoint'
                   WHERE user_id = ?""",
                (user_id,)
            )

    def set_account_status(self, user_id: str, status: str):
        """status: active | inactive | checkpoint | banned"""
        with self._connect() as conn:
            conn.execute(
                "UPDATE account_state SET status = ? WHERE user_id = ?",
                (status, user_id)
            )
