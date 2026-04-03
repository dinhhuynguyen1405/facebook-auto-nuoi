import requests
import time
import os
from dotenv import load_dotenv

# Tải biến môi trường từ file .env
load_dotenv()

# Cấu hình API AdsPower
ADSPOWER_API_URL = "http://local.adspower.net:50325"
API_KEY = os.getenv("ADSPOWER_API_KEY", "")

class AdsPowerManager:
    def __init__(self, api_url=ADSPOWER_API_URL, api_key=API_KEY):
        self.api_url = api_url
        self.api_key = api_key
        # Header xác thực nếu AdsPower yêu cầu
        self.headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key,
            "Authorization": f"Bearer {self.api_key}"
        }

    def start_profile(self, user_id):
        """Khởi động browser profile trên AdsPower và trả về websocket URL để connect"""
        print(f"[AdsPower] Bắt đầu khởi chạy profile: {user_id}...")
        try:
            url = f"{self.api_url}/api/v1/browser/start?user_id={user_id}"
            response = requests.get(url, headers=self.headers).json()
            
            if response.get("code") == 0:
                print(f"[AdsPower Debug] Phản hồi từ API: {response}")
                # Lấy ws/puppeteer (Playwright cũng dùng CDP qua URL này)
                data = response.get("data", {})
                ws_entry = data.get("ws", {})
                ws_endpoint = ws_entry.get("puppeteer", "")
                
                # Cố gắng lấy dự phòng nếu 'puppeteer' bị rỗng
                if not ws_endpoint and data.get("debug_port"):
                    port = data.get("debug_port")
                    print(f"[AdsPower] Không tìm thấy link thư mục ws.puppeteer, thử tạo url cdp từ debug_port: {port}")
                    try:
                        # Thử gọi API http://127.0.0.1:{port}/json/version để lấy chình xác webSocketDebuggerUrl
                        dbg_res = requests.get(f"http://127.0.0.1:{port}/json/version").json()
                        ws_endpoint = dbg_res.get("webSocketDebuggerUrl", "")
                    except Exception as ex:
                        print(f"[AdsPower] Không lấy được DebuggerUrl từ cổng {port}: {ex}")

                print(f"[AdsPower] Đã mở profile. Websocket: {ws_endpoint}")
                return ws_endpoint if ws_endpoint else None
            else:
                print(f"[AdsPower] Lỗi khởi chạy: {response.get('msg')}")
                return None
        except Exception as e:
            print(f"[AdsPower] Lỗi kết nối API AdsPower: {e}")
            return None

    def stop_profile(self, user_id):
        """Tắt browser profile"""
        print(f"[AdsPower] Đang tắt profile: {user_id}...")
        try:
            url = f"{self.api_url}/api/v1/browser/stop?user_id={user_id}"
            response = requests.get(url, headers=self.headers).json()
            if response.get("code") == 0:
                print(f"[AdsPower] Đã tắt profile {user_id} thành công.")
            else:
                print(f"[AdsPower] Lỗi khi tắt profile: {response.get('msg')}")
        except Exception as e:
            print(f"[AdsPower] Lỗi kết nối API AdsPower: {e}")
