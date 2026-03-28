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
                # Lấy ws/puppeteer (Playwright cũng dùng CDP qua URL này)
                ws_endpoint = response["data"]["ws"]["puppeteer"]
                print(f"[AdsPower] Đã mở profile. Websocket: {ws_endpoint}")
                return ws_endpoint
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
