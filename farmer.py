import json
import time
import random
from playwright.sync_api import sync_playwright
from adspower_farmer import AdsPowerManager

# ==========================================
# CÁC HÀM GIẢ LẬP CON NGƯỜI (HUMAN EMULATION)
# ==========================================
def human_delay(min_sec=1, max_sec=4):
    """Nghỉ ngơi ngẫu nhiên như người thật đang đọc"""
    time.sleep(random.uniform(min_sec, max_sec))

def human_typing(page, selector, text):
    """Gõ phím với tốc độ thay đổi và thi thoảng gõ sai rồi xóa"""
    page.locator(selector).click(delay=random.randint(50, 150))
    for char in text:
        page.keyboard.type(char, delay=random.randint(40, 250))
        # 5% cơ hội gõ sai và ấn backspace (như người thật)
        if random.random() < 0.05:
            human_delay(0.1, 0.4)
            page.keyboard.press("Backspace")
            page.keyboard.type(char, delay=random.randint(40, 250))

def human_scroll(page):
    """Cuộn chuột mượt mà, thi thoảng cuộn ngược lại một chút (đọc lại)"""
    scroll_steps = random.randint(3, 7)
    for _ in range(scroll_steps):
        # 80% cuộn xuống, 20% cuộn lên
        direction = 1 if random.random() < 0.8 else -0.5
        amount = int(random.uniform(200, 800) * direction)
        page.mouse.wheel(0, amount)
        human_delay(0.5, 2.5)

def erratic_mouse_move(page):
    """Di chuyển chuột loạn xạ trên màn hình (như tay cầm chuột bị rung)"""
    viewport = page.viewport_size
    if not viewport:
        return
    for _ in range(random.randint(3, 8)):
        x = random.randint(0, viewport['width'])
        y = random.randint(0, viewport['height'])
        page.mouse.move(x, y, steps=random.randint(10, 30))
        human_delay(0.1, 0.5)

# ==========================================
# LỚP NÔNG DÂN CHUYÊN NGHIỆP (ADVANCED FARMER)
# ==========================================
class FacebookFarmer:
    def __init__(self, ws_endpoint):
        self.ws_endpoint = ws_endpoint

    def run(self):
        print("[Farmer] Kết nối vào trình duyệt qua Playwright (CDP)...")
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(self.ws_endpoint)
            # Lấy context đầu tiên, giúp giữ nguyên cookie đăng nhập
            context = browser.contexts[0]
            # Chặn tải một số tài nguyên không cần thiết để tăng tốc độ và tránh lỗi
            # context.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media"] else route.continue_())
            
            page = context.pages[0] if context.pages else context.new_page()

            try:
                # Đóng các pop-ups (Thông báo, Allow cookies...)
                context.grant_permissions(["notifications"])
                
                # Mở giao diện Desktop www thay vì m.facebook.com để làm nhiều trò phức tạp
                print("[Farmer] Truy cập www.facebook.com...")
                page.goto("https://www.facebook.com", timeout=60000, wait_until="domcontentloaded")
                human_delay(3, 7)

                if "login" in page.url:
                    print("[Farmer] ⚠️ Nick bị văng đăng nhập hoặc checkpoint! Bỏ qua.")
                    return

                # --- MÁY TRẠNG THÁI (STATE MACHINE) CHỌN HÀNH ĐỘNG NGẪU NHIÊN ---
                # Trọng số: 50% lướt newfeed, 20% xem video, 20% vào group, 10% xem story
                actions = [
                    (self.surf_newsfeed, 50),
                    (self.watch_videos, 20),
                    (self.visit_random_group, 20),
                    (self.watch_stories, 10)
                ]
                
                # Lặp 2-4 hành động tạo ra 1 "session" người dùng thật (10-20 phút)
                session_actions = random.randint(2, 4)
                print(f"[Farmer] Sẽ thực hiện {session_actions} chuỗi hành động ngẫu nhiên cho nick này.")
                
                for step in range(session_actions):
                    print(f"\n[Farmer] --- Bước {step + 1}/{session_actions} ---")
                    # Chọn ngẫu nhiên có trọng số
                    action_func = random.choices([a[0] for a in actions], weights=[a[1] for a in actions])[0]
                    action_func(page)
                    
                    # Rê chuột idle (đi vệ sinh, đi uống nước)
                    print("[Farmer] Nghỉ xả hơi (cắm chuột)...")
                    erratic_mouse_move(page)
                    human_delay(5, 15)

            except Exception as e:
                print(f"[Farmer] ❌ Gặp lỗi bất ngờ: {e}")
            finally:
                print("[Farmer] Ngắt kết nối Playwright. Đóng phiên!")
                browser.disconnect()

    def surf_newsfeed(self, page):
        """Hành vi: Lướt Newsfeed, click Xem thêm, Like ngẫu nhiên"""
        print("[Hành động] Lướt Newsfeed...")
        page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
        human_delay(4, 8)
        
        for _ in range(random.randint(5, 10)): # Scroll 5-10 đoạn
            human_scroll(page)
            erratic_mouse_move(page)
            
            # Khả năng ấn nút "Xem thêm / See more"
            try:
                see_more_btn = page.locator('div[role="button"]:has-text("Xem thêm"), div[role="button"]:has-text("See more")').first
                if see_more_btn.is_visible(timeout=1000):
                    see_more_btn.click()
                    print("  -> Bấm [Xem thêm] để đọc bài dài.")
                    human_delay(2, 5)
            except: pass

            # 15% cơ hội Like/Thả tim bài viết
            if random.random() < 0.15:
                self.random_reaction(page)

    def random_reaction(self, page):
        """Hover qua nút Like và chọn ngẫu nhiên Like/Love/Haha"""
        try:
            like_bts = page.locator('div[aria-label="Thích"], div[aria-label="Like"]').all()
            if like_bts:
                btn = random.choice(like_bts[:3]) # Thấy nút nào đang ở trên màn hình thì click
                # Hover để giả vờ đang chọn cảm xúc
                btn.hover()
                human_delay(1, 2)
                # Đôi khi chỉ like, đôi khi thả tim (hiện tại click thẳng cho an toàn)
                btn.click()
                print("  -> Đã thả tương tác (Thích/Tim) bài viết!")
        except: pass

    def watch_videos(self, page):
        """Hành vi: Chuyển sang Watch tab, lướt và xem video 1 lúc"""
        print("[Hành động] Chuyển qua xem Video (Facebook Watch)...")
        page.goto("https://www.facebook.com/watch", wait_until="domcontentloaded")
        human_delay(3, 6)
        
        # Xem khoảng 3-5 video, mỗi video dừng lại khá lâu (15 - 40 giây)
        for i in range(random.randint(3, 5)):
            print(f"  -> Đang xem video thứ {i+1}...")
            human_delay(15, 40) 
            # Cuộn xuống mạnh để qua video tiếp theo
            page.mouse.wheel(0, random.randint(800, 1200))
            erratic_mouse_move(page)

    def visit_random_group(self, page):
        """Hành vi: Vào tab Groups, lướt trong Group ngẫu nhiên"""
        print("[Hành động] Đi dạo trong các Hội Nhóm (Groups)...")
        page.goto("https://www.facebook.com/groups", wait_until="domcontentloaded")
        human_delay(3, 5)
        human_scroll(page)
        # Giả lập lướt bảng tin group
        for _ in range(random.randint(3, 6)):
            human_scroll(page)
            if random.random() < 0.1:
                self.random_reaction(page)

    def watch_stories(self, page):
        """Hành vi: Bấm vào Story trên cùng, đợi, chuyển next"""
        print("[Hành động] Soi Stories...")
        page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
        human_delay(3, 6)
        try:
            # Chọn bừa 1 thẻ có hình ảnh hoặc aria-label chứa cụm Story/Tin
            story_cards = page.locator('div[aria-label*="Tin"], div[aria-label*="Story"]').all()
            if story_cards:
                story_cards[0].click()
                print("  -> Đã mở Story đầu tiên lên xem.")
                # Chờ xem story 10 - 20s
                human_delay(10, 20)
                # Bấm Esc hoặc Close để thoát story
                page.keyboard.press("Escape")
        except:
            print("  -> Không tìm thấy story để bấm.")

def main():
    manager = AdsPowerManager()
    
    try:
        with open("accounts.json", "r") as f:
            accounts = json.load(f)
    except FileNotFoundError:
        print("[Lỗi] Không tìm thấy file accounts.json!")
        return

    for acc in accounts:
        if acc.get("status") != "active":
            continue
            
        user_id = acc["user_id"]
        print(f"\n======================================")
        print(f"BẮT ĐẦU HOẠT ĐỘNG: {acc['name']} (ID: {user_id})")
        print(f"======================================")

        ws_endpoint = manager.start_profile(user_id)
        if ws_endpoint:
            human_delay(5, 10) # Chờ trình duyệt load hẳn (quan trọng)
            
            farmer = FacebookFarmer(ws_endpoint)
            farmer.run()

            manager.stop_profile(user_id)
            
        print(f"[Hoàn thành] ⏳ Farm xong acc này, nghỉ giải lao trước khi đổi IP/Nick mới...")
        human_delay(15, 30)

if __name__ == "__main__":
    main()