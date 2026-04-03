"""
Module: db/connector.py
Chức năng: Kết nối và truy vấn database (SQLite hoặc PostgreSQL)
"""
import sqlite3
from typing import List, Dict, Any

class DBConnector:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def fetch_pending_posts(self) -> List[Dict[str, Any]]:
        """Lấy các bài post cần seeding (ví dụ: seeding_status = 'pending')"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, url, post_type, content FROM posts WHERE seeding_status = 'pending'")
        rows = cursor.fetchall()
        conn.close()
        return [
            {"id": row[0], "url": row[1], "post_type": row[2], "content": row[3]} for row in rows
        ]

    def update_seeding_status(self, post_id: int, status: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE posts SET seeding_status = ? WHERE id = ?", (status, post_id))
        conn.commit()
        conn.close()
