"""
Module: actions/action_comment.py
Chức năng: Điều khiển AdsPower/Playwright để comment vào bài post Facebook
"""
from typing import Optional

def comment_to_post(post_url: str, comment_text: str, profile_id: Optional[str] = None) -> bool:
    """
    Mở profile AdsPower, vào post_url và comment comment_text
    profile_id: ID profile AdsPower (nếu dùng nhiều tài khoản)
    Trả về True nếu thành công, False nếu lỗi
    """
    # TODO: Tích hợp Playwright/AdsPower API thực tế
    print(f"[MOCK] Commenting to {post_url} with text: {comment_text}")
    return True
