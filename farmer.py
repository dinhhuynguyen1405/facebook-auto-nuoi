import json
import time
import random
from playwright.sync_api import sync_playwright
from adspower_farmer import AdsPowerManager

# ==========================================
# CẤU HÌNH DỮ LIỆU HUMAN
# ==========================================
SAFE_COMMENTS = [
    "Tuyệt vời quá!", "Đỉnh", "Hay quá", "Quá đẹp",
    "Tuyệt vời", "Đỉnh cao", "Nhìn đã thật", 
    "❤️❤️❤️", "Wow!", "Trông xịn quá"
]

STORY_TEXTS = [
    "Một ngày tuyệt vời ✨", "Cố lên nào 💪", "Chút bình yên...", 
    "Trời hôm nay đẹp quá!", "Tự nhiên thấy nhớ...", "Fighting !!!", 
    "Enjoy the moment 🌿"
]

STATUS_TEXTS = [
    "Có những ngày chỉ muốn ngủ một giấc thật dài.", 
    "Hôm nay ra đường quên xem hoàng lịch \u003D))", 
    "Cafe không mọi người ơi?", 
    "Lâu lâu trồi lên cho mọi người nhớ mặt.",
    "Bình yên là khi tâm không gợn sóng...",
    "Ăn gì cho đỡ buồn nhỉ?"
]

# ==========================================
# CÁC HÀM GIẢ LẬP CON NGƯỜI (HUMAN EMULATION)
# ==========================================
def human_delay(min_sec=1, max_sec=4):
    time.sleep(random.uniform(min_sec, max_sec))

def human_typing(page, text):
    for char in text:
        page.keyboard.type(char, delay=random.randint(50, 200))
        if random.random() < 0.05:
            human_delay(0.2, 0.5)
            page.keyboard.type(random.choice("asdfghjkl"), delay=random.randint(50, 100))
            human_delay(0.1, 0.3)
            page.keyboard.press("Backspace")
            human_delay(0.1, 0.4)

def erratic_mouse_move(page, reading_mode=False):
    try:
        viewport = page.viewport_size
        if not viewport: return
        min_x, max_x = int(viewport['width'] * 0.35), int(viewport['width'] * 0.65)
        min_y, max_y = int(viewport['height'] * 0.20), int(viewport['height'] * 0.85)

        for _ in range(random.randint(2, 5)):
            if reading_mode:
                x = random.randint(min_x, max_x)
                y = random.randint(int(viewport['height'] / 2) - 50, int(viewport['height'] / 2) + 50)
            else:
                x, y = random.randint(min_x, max_x), random.randint(min_y, max_y)
            page.mouse.move(x, y, steps=random.randint(15, 30))
            human_delay(0.1, 0.3)
    except Exception: pass

def human_scroll(page):
    try:
        viewport = page.viewport_size
        if viewport:
            center_x = viewport['width'] / 2 + random.randint(-50, 50)
            center_y = viewport['height'] / 2 + random.randint(-50, 50)
            page.mouse.move(center_x, center_y, steps=10)

        scroll_steps = random.randint(4, 8)
        for _ in range(scroll_steps):
            direction = 1 if random.random() < 0.85 else -0.4
            amount = int(random.uniform(300, 700) * direction)
            page.mouse.wheel(0, amount)
            human_delay(0.5, 2.5)
    except Exception: pass

# ==========================================
# LỚP TỰ ĐỘNG HÓA NÂNG CAO
# ==========================================
class FacebookFarmer:
    def __init__(self, ws_endpoint):
        self.ws_endpoint = ws_endpoint

    def get_elements_in_center(self, page, locators):
        valid_elements = []
        viewport = page.viewport_size
        if not viewport: return []
        min_x, max_x = int(viewport['width'] * 0.25), int(viewport['width'] * 0.75)

        for el in locators:
            try:
                if not el.is_visible(timeout=500): continue
                box = el.bounding_box()
                if box and (min_x <= (box['x'] + box['width'] / 2) <= max_x):
                    valid_elements.append(el)
            except Exception: continue
        return valid_elements

    def get_safe_center_coords(self, element):
        box = element.bounding_box()
        if not box: return None
        return box['x'] + box['width'] / 2, box['y'] + box['height'] / 2

    def run(self):
        print("[Farmer] Kết nối vào trình duyệt qua Playwright (CDP)...")
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(self.ws_endpoint)
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else context.new_page()

            try:
                context.grant_permissions(["notifications"])
                print("[Farmer] Truy cập www.facebook.com...")
                page.goto("https://www.facebook.com", timeout=60000, wait_until="domcontentloaded")
                human_delay(4, 8)

                if "login" in page.url or "checkpoint" in page.url:
                    print("[Farmer] ⚠️ Nick bị văng hoặc checkpoint! Dừng lại.")
                    return

                # Đã thêm Đăng status và Đăng story vào lộ trình (Tỷ lệ xuất hiện thấp nhưng chân thật)
                actions = [
                    (self.surf_newsfeed, 45),
                    (self.watch_reels, 15),
                    (self.watch_videos, 15),
                    (self.watch_stories, 10),
                    (self.view_own_profile, 5),
                    (self.create_text_story, 5),
                    (self.post_status, 5)
                ]
                
                session_actions = random.randint(3, 6)
                print(f"[Farmer] Thực thi lượng công việc sâu ({session_actions} thao tác lớn)...")
                
                for step in range(session_actions):
                    print(f"\n[Farmer] --- Bước {step + 1}/{session_actions} ---")
                    action_func = random.choices([a[0] for a in actions], weights=[a[1] for a in actions])[0]
                    action_func(page)
                    print("[Farmer] Dừng lại nghỉ ngơi (chuột idle)...")
                    erratic_mouse_move(page)
                    human_delay(8, 15)

            except Exception as e:
                print(f"[Farmer] ❌ Gặp lỗi trong phiên: {e}")
            finally:
                print("[Farmer] Đóng kết nối.")
                browser.disconnect()

    def surf_newsfeed(self, page):
        print("[Hành động] Đọc và lướt Newsfeed sâu...")
        page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
        human_delay(4, 8)
        
        for _ in range(random.randint(5, 12)):
            human_scroll(page)
            if random.random() < 0.4:
                erratic_mouse_move(page, reading_mode=True)
                human_delay(3, 8)
                self.action_click_see_more(page)
            
            # Tăng tần suất tương tác khi xem bài
            if random.random() < 0.20:
                self.complex_post_engagement(page)

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
                    human_delay(4, 10)
        except Exception: pass

    def complex_post_engagement(self, page):
        """BỘ NÃO TƯƠNG TÁC (Tích hợp Share/Chia sẻ mồi)"""
        # Chia đều tỷ lệ cho các hành động tương tác
        choice = random.choices(
            ["view_photo", "react_emotion", "comment", "share"], 
            weights=[30, 40, 20, 10]
        )[0]

        if choice == "view_photo":
            self.action_view_image(page)
        elif choice == "react_emotion":
            self.action_smart_reaction(page)
        elif choice == "comment":
            self.action_human_comment(page)
        elif choice == "share":
            self.action_share_post(page)

    def action_share_post(self, page):
        try:
            share_bts = page.locator('div[aria-label="Gửi thư này cho bạn bè hoặc đăng trên trang cá nhân của bạn."], div[aria-label="Chia sẻ"], div[aria-label="Share"]').all()
            safe_shares = self.get_elements_in_center(page, share_bts)
            if safe_shares:
                btn = random.choice(safe_shares)
                btn.scroll_into_view_if_needed()
                coords = self.get_safe_center_coords(btn)
                if coords:
                    page.mouse.move(coords[0], coords[1], steps=15)
                    human_delay(1, 2)
                    page.mouse.click(coords[0], coords[1])
                    print("  -> (Hành vi) Bấm nút Chia sẻ (Share) bài viết đang xem.")
                    human_delay(2, 4)
                    
                    # Chờ menu bung lên và bấm "Chia sẻ ngay" hoặc Share Now
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
                photo.scroll_into_view_if_needed()
                coords = self.get_safe_center_coords(photo)
                if coords:
                    page.mouse.move(coords[0], coords[1], steps=20)
                    human_delay(0.5, 1.5)
                    page.mouse.click(coords[0], coords[1])
                    print("  -> (Hành vi) Click phóng to ảnh để ngắm.")
                    human_delay(3, 8)
                    page.keyboard.press("Escape")
        except Exception: pass

    def action_smart_reaction(self, page):
        try:
            like_bts = page.locator('div[aria-label="Thích"], div[aria-label="Like"]').all()
            safe_likes = self.get_elements_in_center(page, like_bts)
            if safe_likes:
                btn = random.choice(safe_likes)
                btn.scroll_into_view_if_needed()
                coords = self.get_safe_center_coords(btn)
                if coords:
                    page.mouse.move(coords[0], coords[1], steps=15)
                    human_delay(1, 2)
                    
                    if random.random() < 0.4:
                        page.mouse.click(coords[0], coords[1])
                        print("  -> (Hành vi) Bấm nút Like (Thích) cục súc.")
                    else:
                        print("  -> (Hành vi) Hover để chọn biểu tượng cảm xúc (Tim/Haha).")
                        page.mouse.move(coords[0], coords[1], steps=2)
                        btn.hover()
                        human_delay(1.5, 2.5) 
                        page.mouse.move(coords[0] + random.randint(20, 80), coords[1] - random.randint(40, 60), steps=10)
                        human_delay(0.5, 1)
                        page.mouse.down()
                        human_delay(0.1, 0.2)
                        page.mouse.up()
        except Exception: pass

    def action_human_comment(self, page):
        try:
            cmt_boxes = page.locator('div[aria-label="Viết bình luận"], div[aria-label="Write a comment"], div[aria-label*="Bình luận dưới tên"]').all()
            safe_boxes = self.get_elements_in_center(page, cmt_boxes)
            if safe_boxes:
                box = safe_boxes[0]
                box.scroll_into_view_if_needed()
                coords = self.get_safe_center_coords(box)
                if coords:
                    page.mouse.move(coords[0], coords[1], steps=random.randint(15, 25))
                    human_delay(0.5, 1)
                    page.mouse.click(coords[0], coords[1])
                    human_delay(1, 2.5) 
                    
                    content = random.choice(SAFE_COMMENTS)
                    human_typing(page, content)
                    human_delay(0.5, 1.5)
                    page.keyboard.press("Enter")
                    print(f"  -> (Hành vi) Đã thả comment như người thật: '{content}'")
                    human_delay(2, 4)
        except Exception: pass


    # ==========================
    # CÁC NGHIỆP VỤ SẢN XUẤT NỘI DUNG (POST STR/STATUS)
    # ==========================
    def create_text_story(self, page):
        """Hành vi: Đăng một story chữ nhanh gọn để chứng tỏ Acc đang 'sống'"""
        print("[Hành động] Tạo nhanh một Story chữ (Đăng Tin)...")
        page.goto("https://www.facebook.com/stories/create", wait_until="domcontentloaded")
        human_delay(4, 7)
        try:
            text_story_btn = page.locator('div[aria-label="Tạo tin dạng văn bản"], div[aria-label="Create a Text Story"]').first
            if text_story_btn.is_visible(timeout=5000):
                text_story_btn.click()
                human_delay(2, 4)
                
                content = random.choice(STORY_TEXTS)
                print(f"  -> Bắt đầu gõ content story: '{content}'")
                human_typing(page, content)
                human_delay(2, 4)
                
                # Bấm chia sẻ lên tin
                share_btn = page.locator('div[aria-label="Chia sẻ lên tin"], div[aria-label="Share to Story"]').first
                if share_btn.is_visible(timeout=3000):
                    share_btn.click()
                    print(f"  -> (Thành công) Đã đăng Story lên vòng tròn bạn bè!")
                    human_delay(6, 10)
        except Exception as e:
            print("  -> (Bỏ qua) Không thể tạo tin lúc này.")
            pass


    def post_status(self, page):
        """Hành vi: Trở về Tường để đăng 1 bọt Status xàm"""
        print("[Hành động] Đăng Trạng Thái / Tâm trạng lên tường cá nhân...")
        # Lối vào an toàn nhất để tránh nhầm Newsfeed là thông qua tab "Trang cá nhân / Profile"
        page.goto("https://www.facebook.com/me/", wait_until="domcontentloaded")
        human_delay(4, 8)
        try:
            # Nhấn vào composer đang nghĩ gì
            composer = page.locator('div[role="button"]:has-text("đang nghĩ gì"), div[role="button"]:has-text("on your mind")').first
            if composer.is_visible(timeout=5000):
                composer.click()
                human_delay(2, 5) # Chờ popup viết bài bật lên
                
                content = random.choice(STATUS_TEXTS)
                human_typing(page, content)
                human_delay(2, 4)
                
                post_btn = page.locator('div[aria-label="Đăng"], div[aria-label="Post"]').first
                if post_btn.is_visible(timeout=3000):
                    post_btn.click()
                    print(f"  -> (Thành công) Đã cắm 1 status mới lên trang cá nhân: '{content}'")
                    human_delay(8, 12)
        except Exception:
            pass


    # ==========================
    # CÁC NGHIỆP VỤ TIÊU THỤ (REELS / VIDEOS)
    # ==========================
    def watch_reels(self, page):
        print("[Hành động] Lướt Facebook Reels (Video Ngắn)...")
        page.goto("https://www.facebook.com/reels/", wait_until="domcontentloaded")
        human_delay(4, 9)
        for i in range(random.randint(4, 10)):
            print(f"  -> Đang dán mắt vào Reel thứ {i+1}...")
            human_delay(8, 30)
            erratic_mouse_move(page)
            if random.random() < 0.1:
                try: self.action_smart_reaction(page)
                except Exception: pass
            page.mouse.wheel(0, random.randint(1500, 2500))
            human_delay(1, 3)

    def view_own_profile(self, page):
        print("[Hành động] Về ngắm Tường cá nhân...")
        page.goto("https://www.facebook.com/me/", wait_until="domcontentloaded")
        human_delay(4, 8)
        for _ in range(random.randint(2, 4)):
            human_scroll(page)
            erratic_mouse_move(page, reading_mode=True)
            human_delay(2, 6)

    def watch_videos(self, page):
        print("[Hành động] Đổi qua xem Video dài (Facebook Watch)...")
        page.goto("https://www.facebook.com/watch", wait_until="domcontentloaded")
        human_delay(3, 6)
        for i in range(random.randint(2, 4)):
            print(f"  -> Xem vội video thứ {i+1}...")
            human_delay(15, 40) 
            erratic_mouse_move(page)
            if random.random() < 0.2:
                self.action_smart_reaction(page)
            page.mouse.wheel(0, random.randint(700, 1000))
            human_delay(1, 3)

    def watch_stories(self, page):
        print("[Hành động] Soi Stories vòng tròn bạn bè...")
        page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
        human_delay(3, 6)
        try:
            story_cards = page.locator('div[aria-label*="Tin"], div[aria-label*="Story"], div[data-pagelet*="Stories"]').all()
            safe_stories = self.get_elements_in_center(page, story_cards)
            if safe_stories:
                btn = safe_stories[0]
                coords = self.get_safe_center_coords(btn)
                if coords:
                    page.mouse.move(coords[0], coords[1], steps=20)
                    human_delay(0.5, 1)
                    page.mouse.click(coords[0], coords[1])
                    print("  -> (Hành vi) Hóng hớt story của Freinds.")
                    viewport = page.viewport_size
                    for _ in range(random.randint(3, 6)):
                        human_delay(4, 10) 
                        next_x_pos = int(viewport['width'] * 0.75) if viewport else 900
                        next_y_pos = int(viewport['height'] * 0.5) if viewport else 500
                        page.mouse.move(next_x_pos, next_y_pos, steps=10)
                        page.mouse.click(next_x_pos, next_y_pos)
                    page.keyboard.press("Escape")
        except Exception: pass

def main():
    manager = AdsPowerManager()
    try:
        with open("accounts.json", "r") as f:
            accounts = json.load(f)
    except FileNotFoundError:
        print("[Lỗi] Không tìm thấy file accounts.json!")
        return

    for acc in accounts:
        if acc.get("status") != "active": continue
        user_id = acc["user_id"]
        print(f"\n======================================")
        print(f"BẮT ĐẦU HOẠT ĐỘNG: {acc['name']} (ID: {user_id})")
        print(f"======================================")

        ws_endpoint = manager.start_profile(user_id)
        if ws_endpoint:
            human_delay(5, 10)
            farmer = FacebookFarmer(ws_endpoint)
            farmer.run()
            manager.stop_profile(user_id)
            
        print(f"[Hoàn thành] ⏳ Nghỉ ngơi chuyển Profile.")
        human_delay(15, 30)

if __name__ == "__main__":
    main()