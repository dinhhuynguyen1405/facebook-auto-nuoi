"""
Module: actions/action_comment.py
Chức năng: Điều khiển AdsPower/Playwright để comment vào bài post Facebook thực tế.
"""
import time
import random
import sys
import os
from typing import Optional

# Đảm bảo import được từ root dù gọi từ đâu
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adspower_farmer import AdsPowerManager
from utils.logger import log


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────
ADJACENT_KEYS = {
    'a': 'qwsz', 'b': 'vghn', 'c': 'xdfv', 'd': 'serfc', 'e': 'wsdr',
    'f': 'rdgvc', 'g': 'tfhbv', 'h': 'ygjnb', 'i': 'ujko', 'j': 'uhkmn',
    'k': 'ijlm', 'l': 'okp', 'm': 'njk', 'n': 'bhjm', 'o': 'ikp',
    'p': 'ol', 'q': 'aw', 'r': 'edf', 's': 'awedxz', 't': 'rfgy',
    'u': 'yhij', 'v': 'cfgb', 'w': 'qeas', 'x': 'zsdc', 'y': 'tghu',
    'z': 'asx'
}


def _human_delay(min_sec=0.5, max_sec=2.0):
    time.sleep(random.uniform(min_sec, max_sec))


def _human_typing(page, text: str):
    """Gõ text với tốc độ không đều, đôi khi gõ sai và xoá lại."""
    for char in text:
        page.keyboard.type(char, delay=random.randint(50, 180))
        if char.lower() in ADJACENT_KEYS and random.random() < 0.02:
            wrong = random.choice(ADJACENT_KEYS[char.lower()])
            page.keyboard.type(wrong, delay=random.randint(60, 150))
            _human_delay(0.15, 0.35)
            page.keyboard.press("Backspace")
            time.sleep(random.uniform(0.1, 0.25))
        _human_delay(0.01, 0.04)


def _move_to_element(page, element):
    """Di chuột Bezier đến phần tử, không thẳng tắp."""
    try:
        box = element.bounding_box()
        if not box:
            return
        offset_x = random.uniform(-box['width'] * 0.2, box['width'] * 0.2)
        offset_y = random.uniform(-box['height'] * 0.2, box['height'] * 0.2)
        tx = box['x'] + box['width'] / 2 + offset_x
        ty = box['y'] + box['height'] / 2 + offset_y

        viewport = page.viewport_size or {'width': 1280, 'height': 800}
        sx = random.randint(0, viewport['width'])
        sy = random.randint(0, viewport['height'])
        cx = (sx + tx) / 2 + random.randint(-100, 100)
        cy = (sy + ty) / 2 + random.randint(-100, 100)

        steps = random.randint(15, 28)
        for i in range(steps):
            t = i / steps
            x = (1 - t) ** 2 * sx + 2 * (1 - t) * t * cx + t ** 2 * tx
            y = (1 - t) ** 2 * sy + 2 * (1 - t) * t * cy + t ** 2 * ty
            page.mouse.move(x, y)
            time.sleep(random.uniform(0.01, 0.025))
    except Exception:
        pass


# ──────────────────────────────────────────────
# MAIN PUBLIC FUNCTION
# ──────────────────────────────────────────────
def comment_to_post(
    post_url: str,
    comment_text: str,
    profile_id: Optional[str] = None,
    ws_endpoint: Optional[str] = None,
) -> bool:
    """
    Mở profile AdsPower (hoặc dùng ws_endpoint sẵn có), điều hướng tới post_url
    và comment comment_text bằng Playwright.

    Args:
        post_url:     URL bài viết Facebook cần comment.
        comment_text: Nội dung comment.
        profile_id:   AdsPower profile user_id (bỏ qua nếu cung cấp ws_endpoint).
        ws_endpoint:  CDP WebSocket URL (nếu browser đã mở sẵn).

    Returns:
        True nếu comment thành công, False nếu gặp lỗi.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log("[action_comment] Playwright chưa được cài. Chạy: pip install playwright")
        return False

    manager = None
    _ws = ws_endpoint

    # Khởi động AdsPower nếu chưa có ws_endpoint
    if not _ws:
        if not profile_id:
            log("[action_comment] Cần profile_id hoặc ws_endpoint.")
            return False
        manager = AdsPowerManager()
        _ws = manager.start_profile(profile_id)
        if not _ws:
            log(f"[action_comment] Không lấy được ws_endpoint cho profile {profile_id}.")
            return False

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(_ws)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()

            # ── Kiểm tra đã đăng nhập chưa ──────────────────
            page.goto("https://www.facebook.com", timeout=30000, wait_until="domcontentloaded")
            _human_delay(3, 6)
            if "login" in page.url or "checkpoint" in page.url:
                log("[action_comment] ⚠️ Nick bị văng / checkpoint. Bỏ qua.")
                browser.disconnect()
                return False

            # ── Điều hướng tới bài viết ──────────────────────
            log(f"[action_comment] Đang mở bài: {post_url}")
            page.goto(post_url, timeout=30000, wait_until="domcontentloaded")
            _human_delay(3, 6)

            # ── Scroll xuống để load comment box ────────────
            for _ in range(random.randint(2, 4)):
                page.mouse.wheel(0, random.uniform(300, 600))
                _human_delay(0.8, 1.5)

            # ── Tìm và click vào ô comment ──────────────────
            comment_selectors = [
                'div[aria-label="Viết bình luận…"]',
                'div[aria-label="Write a comment…"]',
                'div[aria-label="Viết bình luận"]',
                'div[aria-label="Write a comment"]',
                'div[aria-label*="Bình luận dưới tên"]',
                'div[contenteditable="true"][role="textbox"]',
            ]
            comment_box = None
            for sel in comment_selectors:
                el = page.locator(sel).first
                try:
                    if el.is_visible(timeout=3000):
                        comment_box = el
                        break
                except Exception:
                    continue

            if not comment_box:
                log("[action_comment] Không tìm thấy ô nhập bình luận.")
                browser.disconnect()
                return False

            # Di chuột đến ô comment → click → gõ
            _move_to_element(page, comment_box)
            _human_delay(0.5, 1.2)
            comment_box.click()
            _human_delay(1.5, 3.0)

            # Đọc lướt bài 1 chút trước khi gõ (tự nhiên hơn)
            if random.random() < 0.4:
                for _ in range(random.randint(1, 3)):
                    page.mouse.wheel(0, random.uniform(150, 300))
                    _human_delay(1, 2)
                comment_box.click()
                _human_delay(1, 2)

            _human_typing(page, comment_text)
            _human_delay(0.8, 1.5)

            # Xem lại comment trước khi gửi (30%)
            if random.random() < 0.3:
                log("[action_comment] Xem lại nội dung trước khi gửi...")
                _human_delay(1, 2.5)

            page.keyboard.press("Enter")
            log(f"[action_comment] ✅ Đã comment: '{comment_text[:60]}...' vào {post_url}")
            _human_delay(3, 6)

            browser.disconnect()
            return True

    except Exception as e:
        log(f"[action_comment] ❌ Lỗi khi comment: {e}")
        return False
    finally:
        # Tắt profile AdsPower nếu ta đã mở nó
        if manager and profile_id and not ws_endpoint:
            try:
                manager.stop_profile(profile_id)
            except Exception:
                pass
