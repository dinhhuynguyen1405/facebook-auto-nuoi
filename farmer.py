import json
import sys
import os
import time
import random
import math

# Đảm bảo luôn import được từ thư mục gốc dù gọi từ đâu
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playwright.sync_api import sync_playwright
from adspower_farmer import AdsPowerManager
from ai.smart_content import get_ai_comment_or_spin, get_ai_status_or_spin
from config import settings as cfg
from utils.logger import log
from scheduler.schedule_plan import get_plan, get_window_hours
from db.connector import DBConnector

# Ký tự lân cận trên bàn phím QWERTY để gõ sai tự nhiên hơn
ADJACENT_KEYS = {
    'a': 'qwsz', 'b': 'vghn', 'c': 'xdfv', 'd': 'serfc', 'e': 'wsdr',
    'f': 'rdgvc', 'g': 'tfhbv', 'h': 'ygjnb', 'i': 'ujko', 'j': 'uhkmn',
    'k': 'ijlm', 'l': 'okp', 'm': 'njk', 'n': 'bhjm', 'o': 'ikp',
    'p': 'ol', 'q': 'aw', 'r': 'edf', 's': 'awedxz', 't': 'rfgy',
    'u': 'yhij', 'v': 'cfgb', 'w': 'qeas', 'x': 'zsdc', 'y': 'tghu',
    'z': 'asx'
}

# ==========================================
# CẤU HÌNH DỮ LIỆU HUMAN
# ==========================================
SAFE_COMMENTS = [
    "Tuyệt vời quá!", "Đỉnh", "Hay quá", "Quá đẹp",
    "Tuyệt vời", "Đỉnh cao", "Nhìn đã thật", 
    "❤️❤️❤️", "Wow!", "Trông xịn quá",
    "Xin thông tin với ạ", "Ib mình với", "Đẹp", "Duyệt",
    "Đồng ý luôn", "Chuẩn quá", "Đúng rồi đó", "Cũng đang quan tâm",
    "Cho mình xin giá với", "Rep inbox mình nhé",
    "Haha buồn cười thật", "Thú vị ghê", "10 điểm không có nhưng",
    "Thích thế!", "Nhìn thèm quá", "Lưu lại ngay mới được"
]

SAFE_REPLIES = [
    "Chuẩn rồi bạn", "Đúng luôn", "Cảm ơn bạn nhé",
    "Haha", "Công nhận", "+1", "Chứ sao nữa", 
    "Mình cũng thấy vậy", "Xin info với ạ", "Ib ạ"
]

STORY_TEXTS = [
    "Một ngày tuyệt vời ✨", "Cố lên nào 💪", "Chút bình yên...", 
    "Trời hôm nay đẹp quá!", "Tự nhiên thấy nhớ...", "Fighting !!!", 
    "Enjoy the moment 🌿", "Nhiều lúc mệt mỏi nhưng vẫn phải cố",
    "Khởi đầu tuần mới đầy năng lượng!!!"
]

STATUS_TEXTS = [
    "Có những ngày chỉ muốn ngủ một giấc thật dài.", 
    "Hôm nay ra đường quên xem hoàng lịch \u003D))", 
    "Cafe không mọi người ơi?", 
    "Lâu lâu trồi lên cho mọi người nhớ mặt.",
    "Bình yên là khi tâm không gợn sóng...",
    "Ăn gì cho đỡ buồn nhỉ?",
    "Dạo này thời tiết thất thường quá, mọi người giữ gìn sức khoẻ nhé!",
    "Có ai đang thức không nhỉ?"
]

SEARCH_KEYWORDS = [
    "Mèo dễ thương", "Quần áo thời trang", "Du lịch Đà Lạt",
    "Địa điểm ăn uống", "Phim hay 2023", "Nhạc chill", "Góc học tập",
    "Cầu lông", "Giày thể thao nam"
]

# ==========================================
# CÁC HÀM GIẢ LẬP CON NGƯỜI (HUMAN EMULATION NÂNG CAO)
# ==========================================
def human_delay(min_sec=1, max_sec=3):
    """Nghỉ ngơi ngẫu nhiên, mô phỏng quá trình load UI hoặc đọc text ngắn."""
    time.sleep(random.uniform(min_sec, max_sec))
    # Giảm 0.5% cơ hội nghỉ dài từ 5s đến 12s
    if random.random() < 0.005:
        print("  [Human] Người dùng đang ngắt quãng nhẹ...")
        time.sleep(random.uniform(5, 12))

def human_typing(page, text):
    """Gõ phím có tốc độ không đều và dễ gõ sai theo phím lân cận sau đó xóa đi gõ lại"""
    for char in text:
        page.keyboard.type(char, delay=random.randint(40, 200))
        # 2% gõ sai tự nhiên
        if char.lower() in ADJACENT_KEYS and random.random() < 0.02:
            human_delay(0.1, 0.3)
            wrong_char = random.choice(ADJACENT_KEYS[char.lower()])
            page.keyboard.type(wrong_char, delay=random.randint(50, 150))
            human_delay(0.2, 0.4)
            page.keyboard.press("Backspace")
            time.sleep(random.uniform(0.1, 0.3))
        human_delay(0.01, 0.05)

def erratic_mouse_move(page, reading_mode=False):
    """Di chuyển chuột bằng đường cong Bezier mô phỏng tay thật"""
    try:
        viewport = page.viewport_size
        if not viewport: return
        
        start_x = random.randint(0, viewport['width'])
        start_y = random.randint(0, viewport['height'])
        
        for _ in range(random.randint(1, 3)):
            if reading_mode:
                end_x = random.randint(int(viewport['width'] * 0.3), int(viewport['width'] * 0.7))
                end_y = random.randint(int(viewport['height'] * 0.4), int(viewport['height'] * 0.6))
            else:
                end_x = random.randint(int(viewport['width'] * 0.2), int(viewport['width'] * 0.8))
                end_y = random.randint(int(viewport['height'] * 0.2), int(viewport['height'] * 0.8))
            
            control_x = (start_x + end_x) / 2 + random.randint(-150, 150)
            control_y = (start_y + end_y) / 2 + random.randint(-150, 150)
            
            steps = random.randint(15, 30)
            for i in range(steps):
                t = i / steps
                x = (1-t)**2 * start_x + 2*(1-t)*t * control_x + t**2 * end_x
                y = (1-t)**2 * start_y + 2*(1-t)*t * control_y + t**2 * end_y
                page.mouse.move(x, y)
                time.sleep(random.uniform(0.01, 0.03))
            
            start_x, start_y = end_x, end_y
            human_delay(0.1, 0.3)
    except Exception: pass

def human_swipe(page):
    """Mô phỏng thao tác vuốt ngón tay (touch swipe) trên màn hình mobile/touch"""
    try:
        viewport = page.viewport_size
        if not viewport:
            return
        cx = viewport['width'] / 2 + random.randint(-60, 60)
        start_y = int(viewport['height'] * random.uniform(0.6, 0.8))
        end_y = int(viewport['height'] * random.uniform(0.2, 0.4))

        # Lên = scroll xuống (swipe up), ngược lại 15%
        if random.random() < 0.85:
            sy, ey = start_y, end_y      # Vuốt lên (xem nội dung mới)
        else:
            sy, ey = end_y, start_y      # Vuốt xuống (back lại)
            print("  [Human] Vuốt ngược để nhìn lại bài vừa qua...")

        steps = random.randint(18, 35)
        page.mouse.move(cx, sy)
        page.mouse.down()
        for i in range(1, steps + 1):
            t = i / steps
            # Easing out cubic: giảm tốc cuối swipe
            ease = 1 - (1 - t) ** 3
            y = sy + (ey - sy) * ease
            x = cx + random.uniform(-3, 3)
            page.mouse.move(x, y)
            time.sleep(random.uniform(0.008, 0.018))
        page.mouse.up()
        human_delay(0.5, 1.5)
    except Exception:
        pass


def human_scroll(page):
    """Cuộn chuột mượt mà hơn, có thói quen dùng phím để đọc dài, ngắt quãng"""
    try:
        viewport = page.viewport_size

        # 15% dùng touch swipe thay wheel (thiết bị cảm ứng)
        if random.random() < 0.15:
            human_swipe(page)
            return

        # Thói quen dùng phím để cuộn
        if viewport and random.random() < 0.2:
            keys = ["PageDown", "ArrowDown", "Space"]
            key = random.choice(keys)
            presses = random.randint(2, 5) if key == "ArrowDown" else 1
            for _ in range(presses):
                page.keyboard.press(key)
                time.sleep(random.uniform(0.1, 0.3))
            human_delay(1, 3)
            return

        if viewport:
            # Rê chuột ra giữa màn hình tí xíu hoặc hờ hờ ở góc
            center_x = viewport['width'] / 2 + random.randint(-150, 150)
            center_y = viewport['height'] / 2 + random.randint(-100, 100)
            page.mouse.move(center_x, center_y, steps=random.randint(10, 20))

        scroll_steps = random.randint(3, 9)
        for _ in range(scroll_steps):
            # 85% cuộn xuống, 15% cuộn ngược để đọc lại
            is_down = random.random() < 0.85
            amount = random.uniform(200, 600) if is_down else -random.uniform(100, 300)
            
            # Cuộn thành nhiều nhịp nhỏ (micro-scrolls) cho giống con lăn chuột vật lý
            mini_ticks = random.randint(3, 8)
            step_amt = amount / mini_ticks
            for _ in range(mini_ticks):
                page.mouse.wheel(0, step_amt)
                time.sleep(random.uniform(0.02, 0.1))
            
            if not is_down:
                print("  [Human] Vừa cuộn ngược lại để nhìn kỹ hơn...")
                human_delay(2, 4)
            else:
                human_delay(1, 3)
    except Exception: pass

def action_random_text_highlight(page):
    """Thói quen bôi đen text ngẫu nhiên (highlight để đọc)"""
    try:
        viewport = page.viewport_size
        if not viewport or random.random() > 0.3: return # 30% tỷ lệ thực hiện
        
        start_x = viewport['width'] / 2 + random.randint(-100, 100)
        start_y = viewport['height'] / 2 + random.randint(-100, 100)
        end_x = start_x + random.randint(50, 300)
        end_y = start_y + random.randint(-20, 50) # Quét ngang dòng hoặc xuống dòng 1 tí
        
        page.mouse.move(start_x, start_y, steps=15)
        page.mouse.down()
        human_delay(0.2, 0.5)
        page.mouse.move(end_x, end_y, steps=25)
        human_delay(0.2, 0.8)
        page.mouse.up()
        print("  [Human] Bôi đen vùng văn bản (thói quen tay).")
        human_delay(2, 5) # Đứng lại đọc
        
        # Click bỏ bôi đen
        page.mouse.click(start_x - 100, start_y - 50)
    except Exception: pass

# ==========================================
# LỚP TỰ ĐỘNG HÓA NÂNG CAO
# ==========================================
class FacebookFarmer:
    def __init__(self, ws_endpoint, account_day: int = 1, user_id: str = ""):
        self.ws_endpoint = ws_endpoint
        self.account_day = account_day
        self.user_id = user_id
        self._used_actions: set = set()
        self._engagement_count: int = 0
        self._plan = get_plan(account_day)   # DayPlan cho ngày hôm nay

    def get_elements_in_center(self, page, locators):
        """Lấy danh sách các phần tử đang nằm trong vùng viewport hiển thị rõ ràng"""
        valid_elements = []
        viewport = page.viewport_size
        if not viewport: return []
        
        # Chỉ giới hạn vùng an toàn (xung quanh tỷ lệ giữa màn hình)
        min_x, max_x = int(viewport['width'] * 0.15), int(viewport['width'] * 0.85)
        min_y, max_y = int(viewport['height'] * 0.15), int(viewport['height'] * 0.95)
        
        for el in locators:
            try:
                if not el.is_visible(timeout=500): continue
                box = el.bounding_box()
                if box:
                    center_x = box['x'] + box['width'] / 2
                    center_y = box['y'] + box['height'] / 2
                    if (min_x <= center_x <= max_x) and (min_y <= center_y <= max_y):
                        valid_elements.append(el)
            except Exception: continue
        return valid_elements

    def get_safe_center_coords(self, element):
        try:
            box = element.bounding_box()
            if not box: return None
            # Chệch quỹ đạo xíu, không bao giờ nhắm thẳng tâm 100%
            offset_x = random.uniform(-box['width']*0.2, box['width']*0.2)
            offset_y = random.uniform(-box['height']*0.2, box['height']*0.2)
            return box['x'] + box['width'] / 2 + offset_x, box['y'] + box['height'] / 2 + offset_y
        except Exception:
            return None

    def _resolve_actions(self, plan) -> list:
        """Chuyển danh sách (method_name, weight) từ plan sang (callable, weight).
        Bỏ qua method không tồn tại để không crash."""
        resolved = []
        for name, weight in plan["actions"]:
            fn = getattr(self, name, None)
            if fn is None:
                log(f"[Farmer] ⚠️ Không tìm thấy action '{name}', bỏ qua.", "warning")
                continue
            resolved.append((fn, weight))
        return resolved

    def run(self) -> str:
        """
        Chạy một phiên farming theo schedule_plan của ngày hôm nay.
        Trả về: 'ok' | 'checkpoint' | 'error'
        """
        plan = self._plan
        log(f"[Farmer] Ngày {self.account_day} — {plan['notes']}")
        log(f"[Farmer] Seeding: {'✅ BẬT' if plan['allow_seeding'] else '🚫 TẮT'} | Phiên: {plan['sessions']}")

        with sync_playwright() as p:
            try:
                browser = p.chromium.connect_over_cdp(self.ws_endpoint)
            except Exception as e:
                log(f"[Farmer] ❌ Không kết nối được CDP: {e}", "error")
                return "error"

            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()
            result = "ok"

            try:
                context.grant_permissions(["notifications"])
                page.goto("https://www.facebook.com", timeout=60000, wait_until="domcontentloaded")
                human_delay(5, 10)

                # ── Phát hiện checkpoint / bị văng ──────────────
                if "login" in page.url:
                    log("[Farmer] ⚠️ Nick bị văng đăng nhập!", "warning")
                    return "checkpoint"
                if "checkpoint" in page.url or "disabled" in page.url:
                    log("[Farmer] 🚨 Nick gặp CHECKPOINT / bị disable!", "error")
                    return "checkpoint"

                # ── Build action pool từ schedule_plan ──────────
                actions = self._resolve_actions(plan)
                if not actions:
                    log("[Farmer] Không có action nào hợp lệ cho ngày này.", "error")
                    return "error"

                # ── Chạy các phiên trong ngày ────────────────────
                # daily_runner sẽ gọi run() nhiều lần (1 lần/phiên),
                # nên ở đây ta chỉ chạy 1 phiên với số bước theo plan
                session_steps = random.randint(cfg.SESSION_ACTIONS_MIN, cfg.SESSION_ACTIONS_MAX)
                log(f"[Farmer] Thực thi {session_steps} action trong phiên này...")

                for step in range(session_steps):
                    log(f"\n[Farmer] --- Bước {step + 1}/{session_steps} ---")

                    # Anti-repeat trong phiên
                    remaining = [(fn, w) for fn, w in actions if fn.__name__ not in self._used_actions]
                    if not remaining:
                        self._used_actions.clear()
                        remaining = actions

                    action_func = random.choices(
                        [a[0] for a in remaining],
                        weights=[a[1] for a in remaining]
                    )[0]
                    self._used_actions.add(action_func.__name__)

                    try:
                        action_func(page)
                    except Exception as e:
                        log(f"  [Farmer] Lỗi action '{action_func.__name__}': {e}", "warning")

                    # Re-check checkpoint sau mỗi action nặng
                    if "checkpoint" in page.url or "disabled" in page.url:
                        log("[Farmer] 🚨 Checkpoint phát hiện giữa phiên!", "error")
                        result = "checkpoint"
                        break

                    # Human breathe pause (config-driven)
                    if random.random() < cfg.BREATHE_PAUSE_PROBABILITY:
                        pause = random.uniform(cfg.BREATHE_PAUSE_MIN_SEC, cfg.BREATHE_PAUSE_MAX_SEC)
                        log(f"  [Human] Đặt thiết bị xuống ~{pause:.0f}s...")
                        time.sleep(pause)

                    erratic_mouse_move(page)
                    human_delay(2, 5)

            except Exception as e:
                log(f"[Farmer] ❌ Lỗi phiên: {e}", "error")
                result = "error"
            finally:
                log("[Farmer] Đóng kết nối.")
                browser.disconnect()

        return result

    def surf_newsfeed_no_engagement(self, page):
        """Khởi động lướt trang Newsfeed nhưng không tương tác thích/comment/share"""
        print("[Hành động] Lướt Newsfeed tĩnh lặng (Không comment/Like)...")
        page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
        human_delay(2, 4)
        for _ in range(random.randint(5, 10)):
            human_scroll(page)
            erratic_mouse_move(page, reading_mode=True)
            action_random_text_highlight(page)
            if random.random() < 0.2:
                self.action_click_see_more(page)

    def watch_reels_no_engagement(self, page):
        print("[Hành động] Lướt Reels lặng im...")
        page.goto("https://www.facebook.com/reels/", wait_until="domcontentloaded")
        human_delay(3, 5)
        for i in range(random.randint(4, 7)):
            human_delay(8, 15)
            erratic_mouse_move(page)
            page.mouse.wheel(0, random.randint(1500, 2500))

    def watch_videos_no_engagement(self, page):
        print("[Hành động] Xem Facebook Watch giải trí (Không Like)...")
        page.goto("https://www.facebook.com/watch", wait_until="domcontentloaded")
        human_delay(3, 5)
        for i in range(random.randint(3, 5)):
            human_delay(15, 30)
            erratic_mouse_move(page)
            page.mouse.wheel(0, random.randint(700, 1200))

    def visit_groups_no_engagement(self, page):
        print("[Hành động] Đọc Feed nhóm tự nhiên (Không Like/Comment)...")
        try:
            page.goto("https://www.facebook.com/groups/feed/", wait_until="domcontentloaded")
            human_delay(4, 8)
            for _ in range(random.randint(6, 12)):
                human_scroll(page)
                if random.random() < 0.2:
                    self.action_click_see_more(page)
        except Exception: pass

    def join_target_groups(self, page):
        print("[Hành động] Tìm kiếm và xin tham gia Nhóm...")
        keyword = random.choice(SEARCH_KEYWORDS)
        try:
            url = f"https://www.facebook.com/search/groups/?q={int(keyword.encode('utf-8').hex(), 16)}"
            page.goto(url, wait_until="domcontentloaded") # Dummy URL logic if needed, actually we can just goto search groups directly, let's just go search url and type
            # Or simpler:
            page.goto("https://www.facebook.com/groups/discover/", wait_until="domcontentloaded")
            human_delay(4, 9)
            
            # Cuộn 1 chút
            for _ in range(random.randint(2, 5)):
                human_scroll(page)
            
            # Bấm Tham gia
            join_btns = page.locator('div[role="button"]:has-text("Tham gia"), div[role="button"]:has-text("Join")').all()
            safe_btns = self.get_elements_in_center(page, join_btns)
            if safe_btns:
                # Gửi 1-3 yêu cầu tham gia mỗi lần
                for _ in range(random.randint(1, 3)):
                    if not safe_btns: break
                    btn = random.choice(safe_btns)
                    coords = self.get_safe_center_coords(btn)
                    if coords:
                        page.mouse.move(coords[0], coords[1], steps=15)
                        human_delay(1, 2)
                        page.mouse.click(coords[0], coords[1])
                        print("  -> (Hành vi) Đã bấm nút XIN THAM GIA một nhóm Gợi ý!")
                        human_delay(2, 5)
                        # Có thể có popup trả lời câu hỏi nhóm
                        close_btn = page.locator('div[aria-label="Đóng"], div[aria-label="Close"]').first
                        if close_btn.is_visible(timeout=3000):
                            close_btn.click()
                    safe_btns.remove(btn)
        except Exception: pass

    def add_friends_suggested(self, page):
        print("[Hành động] Lướt danh sách Gợi ý kết bạn mở rộng...")
        try:
            page.goto("https://www.facebook.com/friends/suggestions", wait_until="domcontentloaded")
            human_delay(4, 7)
            for _ in range(random.randint(2, 5)):
                human_scroll(page)
            
            add_btns = page.locator('div[aria-label^="Thêm"], div[aria-label^="Add"]').all()
            safe_btns = self.get_elements_in_center(page, add_btns)
            if safe_btns:
                requests = random.randint(1, 3)
                print(f"  -> (Hành vi) Gửi {requests} yêu cầu kết bạn mở tệp...")
                for _ in range(requests):
                    if not safe_btns: break
                    btn = random.choice(safe_btns)
                    coords = self.get_safe_center_coords(btn)
                    if coords:
                        page.mouse.move(coords[0], coords[1], steps=20)
                        human_delay(0.5, 1)
                        page.mouse.click(coords[0], coords[1])
                        human_delay(2, 6)
                    safe_btns.remove(btn)
        except Exception: pass

    def surf_newsfeed(self, page):
        """Lướt và đọc Newsfeed có bôi đen, nhấp ảnh, like dạo..."""
        print("[Hành động] Đọc và lướt Newsfeed sâu...")
        page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
        human_delay(2, 4)
        
        for _ in range(random.randint(4, 8)):
            human_scroll(page)
            erratic_mouse_move(page, reading_mode=True)
            action_random_text_highlight(page)
            
            if random.random() < 0.3:
                self.action_click_see_more(page)
            
            # Tương tác tự nhiên hơn
            if random.random() < 0.2:
                self.complex_post_engagement(page)
                
            # Đôi khi hover vào tên tác giả bài đăng để xem info card
            if random.random() < 0.1:
                self.action_hover_author_name(page)

    def action_hover_author_name(self, page):
        try:
            authors = page.locator('h3 a, h2 a, h4 a').all()
            safe_authors = self.get_elements_in_center(page, authors)
            if safe_authors:
                author = random.choice(safe_authors[:3])
                coords = self.get_safe_center_coords(author)
                if coords:
                    page.mouse.move(coords[0], coords[1], steps=20)
                    print("  -> (Hành vi) Rê chuột lên tên profile tác giả xem card.")
                    human_delay(3, 5) # Chờ card mọc lên và đọc
        except Exception: pass

    def action_click_see_more(self, page):
        try:
            see_more_btns = page.locator('div[role="button"]:has-text("Xem thêm"), div[role="button"]:has-text("See more")').all()
            safe_btns = self.get_elements_in_center(page, see_more_btns)
            if safe_btns:
                btn = random.choice(safe_btns)
                coords = self.get_safe_center_coords(btn)
                if coords:
                    page.mouse.move(coords[0], coords[1], steps=15)
                    human_delay(0.5, 1)
                    page.mouse.click(coords[0], coords[1])
                    print("  -> (Hành vi) Đã bấm 'Xem thêm' để đọc văn bản dài.")
                    erratic_mouse_move(page, reading_mode=True)
                    action_random_text_highlight(page)
                    human_delay(4, 10)
        except Exception: pass

    def complex_post_engagement(self, page):
        """BỘ NÃO TƯƠNG TÁC (Tích hợp Share/Ads/Save) - có giới hạn tự nhiên"""
        # Giới hạn tối đa 8 lần tương tác nặng/phiên để tránh spam
        self._engagement_count += 1
        if self._engagement_count > 8:
            prob = max(0.1, 1.0 - (self._engagement_count - 8) * 0.15)
            if random.random() > prob:
                print(f"  [Human] Đã tương tác {self._engagement_count} lần, mỏi tay, bỏ qua.")
                return

        choice = random.choices(
            ["view_photo", "react_emotion", "comment_and_read", "share", "click_ad", "save_post"],
            weights=[20, 30, 20, 5, 15, 10]
        )[0]

        if choice == "view_photo":
            self.action_view_image(page)
        elif choice == "react_emotion":
            self.action_smart_reaction(page)
        elif choice == "comment_and_read":
            self.action_read_and_engage_comments(page)
        elif choice == "share":
            self.action_share_post(page)
        elif choice == "click_ad":
            self.action_click_ad_or_link(page)
        elif choice == "save_post":
            self.action_save_post(page)

    def action_save_post(self, page):
        """Mô phỏng thói quen lưu bài viết để xem sau"""
        try:
            more_btns = page.locator('div[aria-haspopup="menu"][role="button"], div[aria-label="Hành động đối với bài viết"], div[aria-label="Actions for this post"]').all()
            safe_btns = self.get_elements_in_center(page, more_btns)
            if safe_btns:
                btn = random.choice(safe_btns)
                coords = self.get_safe_center_coords(btn)
                if coords:
                    page.mouse.move(coords[0], coords[1], steps=15)
                    human_delay(0.5, 1)
                    page.mouse.click(coords[0], coords[1])
                    human_delay(1.5, 3)
                    
                    save_btn = page.locator('div[role="menuitem"]:has-text("Lưu"), div[role="menuitem"]:has-text("Save")').first
                    if save_btn.is_visible(timeout=2000):
                        save_coords = self.get_safe_center_coords(save_btn)
                        if save_coords:
                            page.mouse.move(save_coords[0], save_coords[1], steps=10)
                            human_delay(0.5, 1)
                            page.mouse.click(save_coords[0], save_coords[1])
                            print("  -> (Hành vi) Đã bấm Lưu Post/Video để xem lại sau.")
                            human_delay(3, 5)
                            return
                    page.keyboard.press("Escape")
        except Exception: pass

    def action_share_post(self, page):
        try:
            share_bts = page.locator('div[aria-label="Gửi thư này cho bạn bè hoặc đăng trên trang cá nhân của bạn."], div[aria-label="Chia sẻ"], div[aria-label="Share"]').all()
            safe_shares = self.get_elements_in_center(page, share_bts)
            if safe_shares:
                btn = random.choice(safe_shares)
                coords = self.get_safe_center_coords(btn)
                if coords:
                    page.mouse.move(coords[0], coords[1], steps=15)
                    human_delay(1, 2)
                    page.mouse.click(coords[0], coords[1])
                    print("  -> (Hành vi) Bấm nút Chia sẻ (Share) bài viết đang xem.")
                    human_delay(2, 4)
                    
                    quick_share = page.locator('span:has-text("Chia sẻ ngay"), span:has-text("Share now")').first
                    if quick_share.is_visible(timeout=3000):
                        quick_share.click()
                        print("  -> (Thành công) Đã Share bài lên bảng tin nhà thành công!")
                        human_delay(3, 5)
                    else:
                        page.keyboard.press("Escape")
        except Exception: pass

    def action_view_image(self, page):
        try:
            photo_links = page.locator('a[href*="/photo"], a[href*="?fbid="]').all()
            safe_photos = self.get_elements_in_center(page, photo_links)
            if safe_photos:
                photo = random.choice(safe_photos)
                coords = self.get_safe_center_coords(photo)
                if coords:
                    page.mouse.move(coords[0], coords[1], steps=20)
                    human_delay(0.5, 1.5)
                    page.mouse.click(coords[0], coords[1])
                    print("  -> (Hành vi) Click phóng to ảnh để ngắm.")
                    human_delay(4, 10)
                    # Click Next Image vài lần
                    for _ in range(random.randint(1, 3)):
                        if random.random() < 0.6:
                            page.keyboard.press("ArrowRight")
                            human_delay(2, 5)
                    page.keyboard.press("Escape")
        except Exception: pass

    def action_smart_reaction(self, page):
        """Like hoặc thả reaction (tim/haha/wow/buồn/phẫn nộ) với xác suất tự nhiên"""
        # Cấu trúc: (aria-label VN, aria-label EN, offset_x từ nút Like, weight)
        REACTION_TARGETS = [
            ("Thích",    "Like",    0,    45),   # Like thường - phổ biến nhất
            ("Yêu thích","Love",   48,    25),   # Tim
            ("Haha",     "Haha",   96,    15),   # Haha
            ("Thật bất ngờ", "Wow", 144,  8),    # Wow
            ("Buồn",     "Sad",   192,    5),    # Buồn
            ("Phẫn nộ",  "Angry", 240,    2),    # Angry
        ]
        try:
            like_bts = page.locator('div[aria-label="Thích"], div[aria-label="Like"]').all()
            safe_likes = self.get_elements_in_center(page, like_bts)
            if not safe_likes:
                return
            btn = random.choice(safe_likes)
            coords = self.get_safe_center_coords(btn)
            if not coords:
                return

            page.mouse.move(coords[0], coords[1], steps=15)
            human_delay(0.8, 1.5)

            # 50% bấm Like nhanh, 50% chọn reaction icon cụ thể
            if random.random() < 0.5:
                page.mouse.click(coords[0], coords[1])
                print("  -> (Hành vi) Bấm nút Like nhanh.")
            else:
                # Hover giữ để popup reaction hiện ra
                page.evaluate(
                    "(el) => el.dispatchEvent(new MouseEvent('mouseover', {bubbles: true}))",
                    btn.element_handle()
                )
                page.mouse.move(coords[0], coords[1], steps=5)
                human_delay(1.5, 2.5)  # Chờ popup hiện

                # Chọn reaction theo weight tự nhiên
                weights = [r[3] for r in REACTION_TARGETS]
                chosen = random.choices(REACTION_TARGETS, weights=weights)[0]
                vn_label, en_label, offset_x, _ = chosen

                # Thử click theo aria-label trước (chính xác nhất)
                reaction_el = page.locator(
                    f'div[aria-label="{vn_label}"][role="button"], div[aria-label="{en_label}"][role="button"]'
                ).first
                if reaction_el.is_visible(timeout=1500):
                    rc = self.get_safe_center_coords(reaction_el)
                    if rc:
                        page.mouse.move(rc[0], rc[1], steps=10)
                        human_delay(0.3, 0.7)
                        page.mouse.click(rc[0], rc[1])
                        print(f"  -> (Hành vi) Đã thả reaction: {vn_label}.")
                        return

                # Fallback: di chuột theo offset cố định từ nút Like
                target_x = coords[0] + offset_x + random.randint(-5, 5)
                target_y = coords[1] - random.randint(45, 65)
                page.mouse.move(target_x, target_y, steps=12)
                human_delay(0.4, 0.8)
                page.mouse.click(target_x, target_y)
                print(f"  -> (Hành vi) Đã thả reaction (offset): {vn_label}.")
        except Exception: pass

    def extract_post_text(self, page, coords):
        """Cố gắng lấy text của bài viết gần con trỏ (dùng cho AI)"""
        try:
            # Lấy các thẻ div chứa text ở gần vị trí tương tác
            els = page.locator('div[dir="auto"]').all()
            for el in els:
                if el.is_visible(timeout=500):
                    box = el.bounding_box()
                    if box and abs(box['y'] - coords[1]) < 800:
                        text = el.inner_text().strip()
                        if len(text) > 15:
                            return text
        except Exception: pass
        return ""

    def action_read_and_engage_comments(self, page):
        """Mở bình luận ra đọc, like bình luận của người khác, reply hoặc thả comment mới"""
        try:
            # 1. Tìm nút Bình luận của bài viết để mở popup/phần comment
            open_cmt_btns = page.locator('div[role="button"]:has-text("Bình luận"), div[role="button"]:has-text("Comment"), div[aria-label="Viết bình luận"], div[aria-label="Write a comment"]').all()
            safe_open_btns = self.get_elements_in_center(page, open_cmt_btns)
            post_context_text = ""
            if safe_open_btns:
                # Bấm vào nút đầu tiên hợp lệ tìm thấy
                btn = safe_open_btns[0]
                coords = self.get_safe_center_coords(btn)
                if coords:
                    post_context_text = self.extract_post_text(page, coords)
                    page.mouse.move(coords[0], coords[1], steps=15)
                    human_delay(0.5, 1)
                    page.mouse.click(coords[0], coords[1])
                    print("  -> (Hành vi) Mở luồng Bình luận để đọc.")
                    if post_context_text:
                        print(f"     [+] Lấy ngữ cảnh bài: '{post_context_text[:40]}...'")
                    human_delay(2, 5)

            # 2. Cuộn chuột để đọc comment
            for _ in range(random.randint(1, 4)):
                human_scroll(page)
                human_delay(1, 3)

            # 3. Random Like 1 comment của người khác
            if random.random() < 0.4:
                like_cmts = page.locator('div[role="button"]:has-text("Thích"), div[role="button"]:has-text("Like")').all()
                safe_likes = self.get_elements_in_center(page, like_cmts)
                if safe_likes:
                    # Lấy cẩn thận để tránh nút Like to của bài viết chính, lấy từ vị trí số 1 trở đi nếu có
                    target_like = random.choice(safe_likes[1:] if len(safe_likes) > 1 else safe_likes)
                    coords = self.get_safe_center_coords(target_like)
                    if coords:
                        page.mouse.move(coords[0], coords[1], steps=10)
                        human_delay(0.2, 0.8)
                        page.mouse.click(coords[0], coords[1])
                        print("  -> (Hành vi) Đã thả Thích (Like) một bình luận của user khác.")
                        human_delay(1, 2)

            # 4. Đôi khi Reply (Phản hồi) một comment
            if random.random() < 0.2:
                reply_btns = page.locator('div[role="button"]:has-text("Phản hồi"), div[role="button"]:has-text("Reply")').all()
                safe_replies = self.get_elements_in_center(page, reply_btns)
                if safe_replies:
                    reply_btn = random.choice(safe_replies)
                    coords = self.get_safe_center_coords(reply_btn)
                    if coords:
                        page.mouse.move(coords[0], coords[1], steps=15)
                        page.mouse.click(coords[0], coords[1])
                        print("  -> (Hành vi) Bấm Phản hồi (Reply) một bình luận.")
                        human_delay(1.5, 2.5)
                        
                        reply_content = get_ai_comment_or_spin(post_text="", context_type="reply")
                        human_typing(page, reply_content)
                        human_delay(0.5, 1)
                        page.keyboard.press("Enter")
                        print(f"  -> (Hành vi) Đã thả reply: '{reply_content}'")
                        human_delay(2, 4)

            # 5. Random viết 1 Comment mới hoàn toàn vào bài viết (70% tỉ lệ comment vào bài đang mở focus)
            if random.random() < 0.7:
                cmt_boxes = page.locator('div[aria-label="Viết bình luận"], div[aria-label="Write a comment"], div[aria-label*="Bình luận dưới tên"]').all()
                safe_boxes = self.get_elements_in_center(page, cmt_boxes)
                if safe_boxes:
                    box = safe_boxes[0]
                    coords = self.get_safe_center_coords(box)
                    if coords:
                        page.mouse.move(coords[0], coords[1], steps=random.randint(15, 25))
                        human_delay(0.5, 1)
                        page.mouse.click(coords[0], coords[1])
                        human_delay(1.5, 3) 
                        
                        content = get_ai_comment_or_spin(post_text=post_context_text, context_type="post")
                        human_typing(page, content)
                        human_delay(1, 2)
                        page.keyboard.press("Enter")
                        print(f"  -> (Hành vi) Đã thả comment: '{content}'")
                        human_delay(2, 4)

            # 6. Bấm Escape để tắt overlay comment (nếu UI Facebook mở mode Modal hiển thị comment)
            page.keyboard.press("Escape")
            human_delay(1, 2)

        except Exception: pass

    # ==========================
    # CÁC NGHIỆP VỤ NHIỀU HƠN
    # ==========================
    def search_something(self, page):
        print("[Hành động] Tìm kiếm từ khóa để lấy cookie sở thích...")
        keyword = random.choice(SEARCH_KEYWORDS)
        try:
            page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
            human_delay(3, 6)
            
            search_box = page.locator('input[type="search"]').first
            if search_box.is_visible(timeout=5000):
                search_box.click()
                human_delay(1, 2)
                human_typing(page, keyword)
                human_delay(1, 2)
                page.keyboard.press("Enter")
                print(f"  -> Đã tìm kiếm: '{keyword}'")
                human_delay(5, 10)
                
                # Cuộn xem kết quả
                for _ in range(random.randint(3, 6)):
                    human_scroll(page)
        except Exception: pass

    def visit_groups(self, page):
        print("[Hành động] Dạo qua các Nhóm để giống user thực sự...")
        try:
            page.goto("https://www.facebook.com/groups/feed/", wait_until="domcontentloaded")
            human_delay(4, 8)
            for _ in range(random.randint(4, 8)):
                human_scroll(page)
                if random.random() < 0.2:
                    self.action_click_see_more(page)
                
                if random.random() < 0.15:
                    self.complex_post_engagement(page)
        except Exception: pass

    def check_notifications(self, page):
        print("[Hành động] Xem thông báo để xóa badge số đỏ...")
        try:
            page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
            human_delay(2, 4)
            notif_btn = page.locator('div[aria-label="Thông báo"], div[aria-label="Notifications"]').first
            if notif_btn.is_visible(timeout=5000):
                coords = self.get_safe_center_coords(notif_btn)
                if coords:
                    page.mouse.move(coords[0], coords[1], steps=15)
                    page.mouse.click(coords[0], coords[1])
                    human_delay(3, 5)
                    human_scroll(page)
                    human_delay(2, 4)
                    page.keyboard.press("Escape")
        except Exception: pass

    def check_messages(self, page):
        print("[Hành động] Mở box chat đọc tin nhắn/ soạn nháp...")
        try:
            page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
            human_delay(2, 4)
            msg_btn = page.locator('div[aria-label="Messenger"]').first
            if msg_btn.is_visible(timeout=5000):
                coords = self.get_safe_center_coords(msg_btn)
                if coords:
                    page.mouse.move(coords[0], coords[1], steps=15)
                    page.mouse.click(coords[0], coords[1])
                    human_delay(3, 6)
                    if random.random() < 0.3:
                        human_typing(page, "Haha")
                        human_delay(1, 2)
                        for _ in range(4):
                            page.keyboard.press("Backspace")
                            time.sleep(0.1)
                    page.keyboard.press("Escape")
        except Exception: pass

    def action_click_ad_or_link(self, page):
        try:
            links = page.locator('a[target="_blank"], a[href*="l.facebook.com/l.php"]').all()
            safe_links = self.get_elements_in_center(page, links)
            if safe_links:
                link = random.choice(safe_links)
                coords = self.get_safe_center_coords(link)
                if coords:
                    print("  -> (Hành vi) Bấm vào link/quảng cáo để xem trang ngoài.")
                    page.mouse.move(coords[0], coords[1], steps=15)
                    human_delay(1, 2)
                    with page.context.expect_page() as new_page_info:
                        page.mouse.click(coords[0], coords[1])
                    new_page = new_page_info.value
                    new_page.wait_for_load_state()
                    human_delay(5, 15)
                    for _ in range(random.randint(2, 5)):
                        human_scroll(new_page)
                    new_page.close()
                    print("  -> Đã đóng trang ngoài, quay lại Facebook.")
                    human_delay(2, 4)
        except Exception: pass

    # ==========================
    # CÁC NGHIỆP VỤ ĐỜI SỐNG (MARKETPLACE, BẠN BÈ)
    # ==========================
    def visit_marketplace(self, page):
        """Mô phỏng thói quen hay dạo chợ đồ cũ của dân Việt"""
        print("[Hành động] Window Shopping tại Facebook Marketplace...")
        try:
            page.goto("https://www.facebook.com/marketplace", wait_until="domcontentloaded")
            human_delay(4, 9)
            
            # Cuộn lướt nhẹ các mặt hàng
            for _ in range(random.randint(3, 7)):
                human_scroll(page)
                
            # Random click xem một sản phẩm
            if random.random() < 0.6:
                items = page.locator('a[href*="/marketplace/item/"]').all()
                safe_items = self.get_elements_in_center(page, items)
                if safe_items:
                    item = random.choice(safe_items)
                    coords = self.get_safe_center_coords(item)
                    if coords:
                        page.mouse.move(coords[0], coords[1], steps=15)
                        human_delay(0.5, 1.5)
                        page.mouse.click(coords[0], coords[1])
                        print("  -> (Hành vi) Đã bấm vào 1 bài đăng Marketplace để đọc.")
                        human_delay(5, 10)
                        for _ in range(random.randint(1, 3)):
                            human_scroll(page)
                            human_delay(2, 4)
                        
                        # Không mua gì cả, click thoát hình ảnh/hộp thoại về trang chợ
                        close_btn = page.locator('div[aria-label="Đóng"], div[aria-label="Close"]').first
                        if close_btn.is_visible(timeout=3000):
                            close_btn.click()
                        else:
                            page.keyboard.press("Escape")
                            human_delay(2, 3)
        except Exception: pass

    def manage_friend_requests(self, page):
        """Lướt giao diện Bạn bè để đọc gợi ý hoặc các lời mời kết bạn"""
        print("[Hành động] Kiểm tra danh sách bạn bè / Gợi ý kết bạn...")
        try:
            page.goto("https://www.facebook.com/friends", wait_until="domcontentloaded")
            human_delay(4, 7)
            
            for _ in range(random.randint(2, 5)):
                human_scroll(page)
                
            # Random xem profile của một người được gợi ý
            if random.random() < 0.4:
                suggested = page.locator('a[href*="profile.php"], a[href^="https://www.facebook.com/"][role="link"]').all()
                safe_suggested = self.get_elements_in_center(page, suggested)
                if safe_suggested:
                    # Tránh bấm nhầm home link, chọn link từ vị trí thứ 3 trở đi thường an toàn
                    person = random.choice(safe_suggested[2:] if len(safe_suggested) > 2 else safe_suggested)
                    coords = self.get_safe_center_coords(person)
                    if coords:
                        page.mouse.move(coords[0], coords[1], steps=15)
                        human_delay(0.5, 1.5)
                        page.mouse.click(coords[0], coords[1])
                        print("  -> (Hành vi) Bấm vào tường một người lạ (Gợi ý) để xem.")
                        human_delay(6, 12)
                        
                        for _ in range(random.randint(2, 4)):
                            human_scroll(page)
                            erratic_mouse_move(page, reading_mode=True)
                            human_delay(2, 5)
                            
                        # Đọc xong bấm Back (mũi tên <- trên browser) quay lại tab Friends
                        page.go_back()
                        human_delay(3, 5)
        except Exception: pass

    def create_text_story(self, page):
        print("[Hành động] Tạo nhanh một Story chữ...")
        page.goto("https://www.facebook.com/stories/create", wait_until="domcontentloaded")
        human_delay(4, 7)
        try:
            text_story_btn = page.locator('div[aria-label="Tạo tin dạng văn bản"], div[aria-label="Create a Text Story"]').first
            if text_story_btn.is_visible(timeout=5000):
                text_story_btn.click()
                human_delay(2, 4)
                
                content = get_ai_status_or_spin()
                human_typing(page, content)
                human_delay(2, 4)
                
                share_btn = page.locator('div[aria-label="Chia sẻ lên tin"], div[aria-label="Share to Story"]').first
                if share_btn.is_visible(timeout=3000):
                    share_btn.click()
                    print(f"  -> (Thành công) Đã đăng Story: '{content}'")
                    human_delay(6, 10)
        except Exception: pass

    def post_status(self, page):
        print("[Hành động] Đăng Trạng Thái / Tâm trạng cá nhân...")
        page.goto("https://www.facebook.com/me/", wait_until="domcontentloaded")
        human_delay(4, 8)
        try:
            composer = page.locator('div[role="button"]:has-text("đang nghĩ gì"), div[role="button"]:has-text("on your mind")').first
            if composer.is_visible(timeout=5000):
                composer.click()
                human_delay(2, 5) 
                
                content = get_ai_status_or_spin()
                human_typing(page, content)
                human_delay(2, 4)
                
                post_btn = page.locator('div[aria-label="Đăng"], div[aria-label="Post"]').first
                if post_btn.is_visible(timeout=3000):
                    post_btn.click()
                    print(f"  -> (Thành công) Đã đăng status: '{content}'")
                    human_delay(8, 12)
        except Exception: pass

    # ==========================
    # CÁC NGHIỆP VỤ TIÊU THỤ (REELS / VIDEOS)
    # ==========================
    def watch_reels(self, page):
        print("[Hành động] Lướt Facebook Reels (Video Ngắn)...")
        page.goto("https://www.facebook.com/reels/", wait_until="domcontentloaded")
        human_delay(3, 5)
        for i in range(random.randint(3, 6)):
            print(f"  -> Đang nán lại ở Reel thứ {i+1}...")
            # Xem reel một khoảng thời gian vừa đủ
            human_delay(10, 20)
            erratic_mouse_move(page)
            if random.random() < 0.1:
                try: self.action_smart_reaction(page)
                except Exception: pass
            
            # Sang reel sau
            page.mouse.wheel(0, random.randint(1500, 2500))
            human_delay(1, 3)

    def view_own_profile(self, page):
        print("[Hành động] Tự thẩm tường cá nhân & Ảnh của mình...")
        page.goto("https://www.facebook.com/me/", wait_until="domcontentloaded")
        human_delay(2, 4)
        for _ in range(random.randint(2, 4)):
            human_scroll(page)
            erratic_mouse_move(page, reading_mode=True)
            human_delay(2, 4)

        # Thỉnh thoảng bấm sang tab Bạn bè / Ảnh
        try:
            tabs = page.locator('div[role="tablist"] a').all()
            if tabs and random.random() < 0.3:
                tab = random.choice(tabs[:4]) # About, Friends, Photos, v.v.
                coords = self.get_safe_center_coords(tab)
                if coords:
                    page.mouse.move(coords[0], coords[1], steps=15)
                    page.mouse.click(coords[0], coords[1])
                    print("  -> (Hành vi) Chuyển tab xem Bạn bè/Ảnh cá nhân.")
                    human_delay(3, 6)
                    for _ in range(random.randint(1, 2)):
                        human_scroll(page)
        except Exception: pass

    def watch_videos(self, page):
        print("[Hành động] Đổi qua tệp Video dài (Facebook Watch)...")
        page.goto("https://www.facebook.com/watch", wait_until="domcontentloaded")
        human_delay(3, 5)
        for i in range(random.randint(2, 4)):
            print(f"  -> Đang xem video thứ {i+1}...")
            human_delay(15, 30) # Xem video dài vừa đủ
            erratic_mouse_move(page)
            if random.random() < 0.1:
                self.action_smart_reaction(page)
            page.mouse.wheel(0, random.randint(700, 1200))
            human_delay(1, 3)

    def watch_stories(self, page):
        print("[Hành động] Hóng chuyện bằng Stories của friends...")
        page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
        human_delay(2, 4)
        try:
            story_cards = page.locator('div[aria-label*="Tin"], div[aria-label*="Story"], div[data-pagelet*="Stories"]').all()
            safe_stories = self.get_elements_in_center(page, story_cards)
            if safe_stories:
                btn = safe_stories[0] # Chọn cái story đầu tiên (thường của bạn bè)
                coords = self.get_safe_center_coords(btn)
                if coords:
                    page.mouse.move(coords[0], coords[1], steps=20)
                    human_delay(0.5, 1)
                    page.mouse.click(coords[0], coords[1])
                    print("  -> Bắt đầu xem Chuỗi Story...")
                    viewport = page.viewport_size
                    
                    for _ in range(random.randint(3, 6)):
                        human_delay(3, 7) 
                        next_x_pos = int(viewport['width'] * 0.75) if viewport else 900
                        next_y_pos = int(viewport['height'] * 0.5) if viewport else 500
                        page.mouse.move(next_x_pos, next_y_pos, steps=10)
                        # Cơ hội bấm qua story tiếp
                        if random.random() < 0.7:
                            page.mouse.click(next_x_pos, next_y_pos)
                            print("  -> (Hành vi) Bấm NEXT story tiêp theo.")
                    
                    page.keyboard.press("Escape")
        except Exception: pass

    # ==========================
    # HÀNH VI PHỤ - TĂNG ĐỘ TỰ NHIÊN
    # ==========================
    def browse_events(self, page):
        """Dạo qua trang Events/Sự kiện — hành vi rất tự nhiên của người Việt"""
        print("[Hành động] Lướt trang Sự kiện / Events...")
        try:
            page.goto("https://www.facebook.com/events/", wait_until="domcontentloaded")
            human_delay(3, 6)
            for _ in range(random.randint(3, 6)):
                human_scroll(page)
                erratic_mouse_move(page, reading_mode=True)

            # 30% click xem chi tiết một event
            if random.random() < 0.3:
                event_links = page.locator('a[href*="/events/"]').all()
                safe_links = self.get_elements_in_center(page, event_links)
                # Bỏ qua link /events/ tổng, lấy link sự kiện cụ thể (có số ID)
                specific = [e for e in safe_links if "/events/" in (e.get_attribute("href") or "") and len((e.get_attribute("href") or "").split("/")) > 4]
                if specific:
                    lnk = random.choice(specific[:5])
                    coords = self.get_safe_center_coords(lnk)
                    if coords:
                        page.mouse.move(coords[0], coords[1], steps=15)
                        human_delay(0.5, 1)
                        page.mouse.click(coords[0], coords[1])
                        print("  -> (Hành vi) Xem chi tiết một Sự kiện.")
                        human_delay(5, 10)
                        for _ in range(random.randint(2, 4)):
                            human_scroll(page)
                        page.go_back()
                        human_delay(2, 4)
        except Exception: pass

    def action_copy_post_text(self, page):
        """Copy đoạn text bài viết (Ctrl+C sau khi bôi đen) — thói quen người dùng thực"""
        print("[Hành động] Bôi đen & copy text bài viết...")
        try:
            page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
            human_delay(2, 4)
            for _ in range(random.randint(2, 4)):
                human_scroll(page)

            # Tìm đoạn text bài viết
            text_els = page.locator('div[dir="auto"]').all()
            candidates = [el for el in text_els if el.is_visible(timeout=300)]
            if not candidates:
                return
            target = random.choice(candidates[:6])
            box = target.bounding_box()
            if not box:
                return

            # Bôi đen một đoạn
            sx = box['x'] + random.uniform(5, 30)
            sy = box['y'] + box['height'] / 2
            ex = box['x'] + box['width'] * random.uniform(0.4, 0.9)
            ey = sy + random.uniform(-5, 10)

            page.mouse.move(sx, sy, steps=15)
            page.mouse.down()
            human_delay(0.15, 0.35)
            page.mouse.move(ex, ey, steps=20)
            human_delay(0.2, 0.6)
            page.mouse.up()
            print("  -> (Hành vi) Đã bôi đen text.")
            human_delay(0.5, 1.5)

            # Ctrl+C
            page.keyboard.press("Meta+c" if sys.platform == "darwin" else "Control+c")
            print("  -> (Hành vi) Ctrl+C copy text.")
            human_delay(2, 4)

            # Click bỏ bôi đen
            page.mouse.click(sx - 50, sy - 30)
        except Exception: pass

    def action_open_link_in_new_tab(self, page):
        """Ctrl+click mở link trong tab mới rồi xem 1 lúc, đóng lại — hành vi browser thực"""
        print("[Hành động] Mở link ngoài trong tab mới...")
        try:
            page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
            human_delay(2, 4)
            for _ in range(random.randint(2, 4)):
                human_scroll(page)

            external_links = page.locator('a[href*="l.facebook.com/l.php"], a[target="_blank"]').all()
            safe_links = self.get_elements_in_center(page, external_links)
            if not safe_links:
                return

            lnk = random.choice(safe_links)
            coords = self.get_safe_center_coords(lnk)
            if not coords:
                return

            page.mouse.move(coords[0], coords[1], steps=18)
            human_delay(0.5, 1)

            # Ctrl+click → tab mới
            try:
                with page.context.expect_page(timeout=8000) as new_tab_info:
                    page.mouse.click(
                        coords[0], coords[1],
                        modifiers=["Meta"] if sys.platform == "darwin" else ["Control"]
                    )
                new_tab = new_tab_info.value
                new_tab.wait_for_load_state("domcontentloaded", timeout=15000)
                print("  -> (Hành vi) Mở tab mới, đang đọc nội dung ngoài...")
                human_delay(6, 15)
                for _ in range(random.randint(2, 5)):
                    human_scroll(new_tab)
                new_tab.close()
                print("  -> Đóng tab ngoài, quay lại Facebook.")
                human_delay(2, 4)
            except Exception:
                pass
        except Exception: pass


def main():
    # ── Validate config bắt buộc trước khi làm gì ──
    try:
        cfg.validate()
    except EnvironmentError as e:
        log(str(e))
        sys.exit(1)

    # ── Đọc danh sách accounts ──────────────────────
    try:
        with open(cfg.ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            accounts = json.load(f)
    except FileNotFoundError:
        log(f"[Lỗi] Không tìm thấy file accounts: {cfg.ACCOUNTS_FILE}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        log(f"[Lỗi] accounts.json không hợp lệ: {e}")
        sys.exit(1)

    active = [a for a in accounts if a.get("status") == "active"]
    if not active:
        log("[Lỗi] Không có account nào status=active trong accounts.json")
        sys.exit(1)

    log(f"Tìm thấy {len(active)} account active. Bắt đầu farming...")

    db = DBConnector(cfg.DB_PATH)
    manager = AdsPowerManager(
        api_url=cfg.ADSPOWER_API_URL,
        api_key=cfg.ADSPOWER_API_KEY,
    )

    for acc in active:
        user_id = acc["user_id"]
        name    = acc.get("name", user_id)

        # ── Đồng bộ state từ DB (ưu tiên DB, fallback về accounts.json) ──
        db.upsert_account(user_id, name=name, day_number=acc.get("day", 1))
        state = db.get_account(user_id)
        day   = state.get("day_number", acc.get("day", 1))

        log(f"\n{'='*50}")
        log(f"BẮT ĐẦU: {name} (ID: {user_id}) | Ngày nuôi: {day}")
        log(f"{'='*50}")

        ws_endpoint = manager.start_profile(user_id)
        if not ws_endpoint:
            log(f"[Bỏ qua] Không mở được browser cho {name}.")
            db.log_action(user_id, "start_profile", "failed", day)
            human_delay(5, 10)
            continue

        human_delay(5, 10)
        farmer = FacebookFarmer(ws_endpoint, account_day=day, user_id=user_id)
        result = farmer.run()
        manager.stop_profile(user_id)

        # ── Xử lý kết quả ───────────────────────────────
        db.log_action(user_id, "session", result, day)
        if result == "checkpoint":
            db.mark_checkpoint(user_id)
            log(f"[{name}] 🚨 Checkpoint! Đã đánh dấu — cần xử lý thủ công.", "error")
        elif result == "ok":
            db.increment_day(user_id)
            new_day = day + 1
            log(f"[{name}] ✅ Hoàn thành ngày {day} → chuyển sang ngày {new_day}.")
        else:
            log(f"[{name}] ⚠️ Phiên kết thúc với lỗi, giữ nguyên ngày {day}.", "warning")

        log(f"Nghỉ ngơi trước khi chuyển Profile tiếp theo...")
        human_delay(15, 30)

    log("Đã hoàn thành tất cả accounts.")


if __name__ == "__main__":
    main()
