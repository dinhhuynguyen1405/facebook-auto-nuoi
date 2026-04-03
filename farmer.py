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
    """Gõ phím có tốc độ không đều và dễ gõ sai sau đó xóa đi gõ lại"""
    for char in text:
        page.keyboard.type(char, delay=random.randint(40, 250))
        # 3% gõ sai
        if random.random() < 0.03:
            human_delay(0.2, 0.4)
            wrong_chars = random.randint(1, 3)
            for _ in range(wrong_chars):
                page.keyboard.type(random.choice("asdfghjklqwertyuiop"), delay=random.randint(50, 150))
            human_delay(0.3, 0.6)
            for _ in range(wrong_chars):
                page.keyboard.press("Backspace")
                time.sleep(random.uniform(0.1, 0.3))
            human_delay(0.1, 0.3)

def erratic_mouse_move(page, reading_mode=False):
    """Di chuyển chuột với quỹ đạo gợn sóng / ngập ngừng"""
    try:
        viewport = page.viewport_size
        if not viewport: return
        min_x, max_x = int(viewport['width'] * 0.2), int(viewport['width'] * 0.8)
        min_y, max_y = int(viewport['height'] * 0.2), int(viewport['height'] * 0.8)
        
        for _ in range(random.randint(2, 6)):
            if reading_mode:
                # Nếu đang đọc, chuột thường lướt theo dòng ngang hoặc để yên 1 góc gần giữa
                x = random.randint(int(viewport['width'] * 0.3), int(viewport['width'] * 0.7))
                y = random.randint(int(viewport['height'] * 0.4), int(viewport['height'] * 0.6))
            else:
                x, y = random.randint(min_x, max_x), random.randint(min_y, max_y)
            page.mouse.move(x, y, steps=random.randint(15, 45))
            human_delay(0.1, 0.4)
    except Exception: pass

def human_scroll(page):
    """Cuộn chuột mượt mà hơn, ngắt quãng, thỉnh thoảng cuộn ngược lên xíu (re-read)"""
    try:
        viewport = page.viewport_size
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
    def __init__(self, ws_endpoint):
        self.ws_endpoint = ws_endpoint

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

    def run(self):
        print("[Farmer] Kết nối vào trình duyệt qua Playwright (CDP)...")
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(self.ws_endpoint)
            context = browser.contexts[0]
            # Randomize user agent user-agent strings is already managed by AdsPower, we just use the default
            page = context.pages[0] if context.pages else context.new_page()

            try:
                context.grant_permissions(["notifications"])
                print("[Farmer] Truy cập www.facebook.com...")
                page.goto("https://www.facebook.com", timeout=60000, wait_until="domcontentloaded")
                human_delay(5, 10)

                if "login" in page.url or "checkpoint" in page.url:
                    print("[Farmer] ⚠️ Nick bị văng hoặc checkpoint! Dừng lại.")
                    return

                # Phân rã lịch trình làm việc
                actions = [
                    (self.surf_newsfeed, 35),
                    (self.watch_reels, 15),
                    (self.watch_videos, 10),
                    (self.watch_stories, 15),
                    (self.view_own_profile, 5),
                    (self.search_something, 5),
                    (self.create_text_story, 5),
                    (self.post_status, 5),
                    (self.visit_groups, 5)
                ]
                
                # Giảm số lượng hành động lớn mỗi phiên để chạy không quá lê thê
                session_actions = random.randint(3, 5)
                print(f"[Farmer] Thực thi lượng công việc sâu ({session_actions} thao tác lớn)...")
                
                for step in range(session_actions):
                    print(f"\n[Farmer] --- Bước {step + 1}/{session_actions} ---")
                    action_func = random.choices([a[0] for a in actions], weights=[a[1] for a in actions])[0]
                    action_func(page)
                    
                    print("[Farmer] Chuyển qua hành động tiếp theo...")
                    erratic_mouse_move(page)
                    human_delay(2, 5)

            except Exception as e:
                print(f"[Farmer] ❌ Gặp lỗi trong phiên: {e}")
            finally:
                print("[Farmer] Đóng kết nối.")
                browser.disconnect()

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
        """BỘ NÃO TƯƠNG TÁC (Tích hợp Share/Chia sẻ mồi)"""
        choice = random.choices(
            ["view_photo", "react_emotion", "comment_and_read", "share"], 
            weights=[30, 40, 25, 5]
        )[0]

        if choice == "view_photo":
            self.action_view_image(page)
        elif choice == "react_emotion":
            self.action_smart_reaction(page)
        elif choice == "comment_and_read":
            self.action_read_and_engage_comments(page)
        elif choice == "share":
            self.action_share_post(page)

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
        try:
            like_bts = page.locator('div[aria-label="Thích"], div[aria-label="Like"]').all()
            safe_likes = self.get_elements_in_center(page, like_bts)
            if safe_likes:
                btn = random.choice(safe_likes)
                coords = self.get_safe_center_coords(btn)
                if coords:
                    page.mouse.move(coords[0], coords[1], steps=15)
                    human_delay(1, 2)
                    
                    if random.random() < 0.5:
                        page.mouse.click(coords[0], coords[1])
                        print("  -> (Hành vi) Bấm nút Like nhanh.")
                    else:
                        print("  -> (Hành vi) Hover để thả tim/haha.")
                        # Hover cẩn thận
                        page.mouse.move(coords[0], coords[1], steps=5)
                        # trigger hover for elements
                        page.evaluate("(el) => el.dispatchEvent(new MouseEvent('mouseover', {bubbles: true}))", btn.element_handle())
                        human_delay(1.5, 2.5) 
                        # Di chuột nhẹ lên trên để chọn biểu tượng (Tâm nút tim/haha thường ở trên nút Like 50-60px)
                        page.mouse.move(coords[0] + random.randint(10, 80), coords[1] - random.randint(40, 60), steps=15)
                        human_delay(0.5, 1)
                        page.mouse.click() # Click ngẫu nhiên 1 biểu tượng
        except Exception: pass

    def action_read_and_engage_comments(self, page):
        """Mở bình luận ra đọc, like bình luận của người khác, reply hoặc thả comment mới"""
        try:
            # 1. Tìm nút Bình luận của bài viết để mở popup/phần comment
            open_cmt_btns = page.locator('div[role="button"]:has-text("Bình luận"), div[role="button"]:has-text("Comment"), div[aria-label="Viết bình luận"], div[aria-label="Write a comment"]').all()
            safe_open_btns = self.get_elements_in_center(page, open_cmt_btns)
            if safe_open_btns:
                # Bấm vào nút đầu tiên hợp lệ tìm thấy
                btn = safe_open_btns[0]
                coords = self.get_safe_center_coords(btn)
                if coords:
                    page.mouse.move(coords[0], coords[1], steps=15)
                    human_delay(0.5, 1)
                    page.mouse.click(coords[0], coords[1])
                    print("  -> (Hành vi) Mở luồng Bình luận để đọc.")
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
                        
                        reply_content = random.choice(SAFE_REPLIES)
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
                        
                        content = random.choice(SAFE_COMMENTS)
                        human_typing(page, content)
                        human_delay(1, 2)
                        page.keyboard.press("Enter")
                        print(f"  -> (Hành vi) Đã thả comment mới: '{content}'")
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

    def create_text_story(self, page):
        print("[Hành động] Tạo nhanh một Story chữ...")
        page.goto("https://www.facebook.com/stories/create", wait_until="domcontentloaded")
        human_delay(4, 7)
        try:
            text_story_btn = page.locator('div[aria-label="Tạo tin dạng văn bản"], div[aria-label="Create a Text Story"]').first
            if text_story_btn.is_visible(timeout=5000):
                text_story_btn.click()
                human_delay(2, 4)
                
                content = random.choice(STORY_TEXTS)
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
                
                content = random.choice(STATUS_TEXTS)
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
