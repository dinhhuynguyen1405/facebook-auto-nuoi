import os
import re
import random
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

from dotenv import load_dotenv
load_dotenv()

# --- 1. SPIN CONTENT MẠNH MẼ ---
def spin_text(text):
    """
    Xử lý cấu trúc spin nội dung. Ví dụ: "{Hay quá|Tuyệt vời} {bạn ơi|nha}!"
    """
    def replace_spin(match):
        options = match.group(1).split('|')
        return random.choice(options)
    
    while '{' in text and '}' in text:
        text = re.sub(r'\{([^{}]+)\}', replace_spin, text)
    return text

# --- 2. AI CONTENT CHATGPT/GEMINI ---
def get_ai_comment_or_spin(post_text="", context_type="post"):
    """
    Sinh nội dung thả Comment / Reply mồi bằng Spintax kết hợp AI.
    Với Facebook Auto, nếu cung cấp post_text, AI sẽ đọc bài và trả comment context tự nhiên.
    """
    API_KEY = os.getenv("GEMINI_API_KEY")
    if API_KEY and HAS_GEMINI:
        try:
            genai.configure(api_key=API_KEY)
            model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"temperature": 0.8})
            
            if post_text:
                prompt = f"""Đóng vai người dùng MXH bình thường. Bạn vừa xem một status với nội dung sau: "{post_text}". 
                Hãy comment ngắn bằng tiếng Việt (2-10 chữ), biểu lộ cảm xúc thân thiện, khen ngợi, hoặc đồng cảm. VD: "Đúng rồi đó", "Quá đã", "Tuyệt vời".
                Trả về KHÔNG CÓ ngoặc kép, KHÔNG CÓ giải thích, chỉ kết quả comment."""
            else:
                prompt = "Viết 1 bình luận dạo trên Facebook, từ 2-6 chữ, khen ngợi một cách tự nhiên thân thiện (ví dụ: Hay quá, chuẩn, xịn xò...). Chỉ trả về đúng text comment."
                
            response = model.generate_content(prompt)
            result = response.text.replace('"', '').strip()
            if result:
                return result
        except Exception as e:
            print(f"[AI Warning] Lỗi sinh text bằng AI: {e}")
            pass # Fallback về Spin thủ công
            
    # --- FALLBACK: SPINTAX ---
    if context_type == "reply":
        spins = [
            "{Chuẩn luôn|Đúng rồi|Haha chuẩn} {bạn ơi|nhé|nha}",
            "{Công nhận|Mình cũng thấy vậy} {luôn|ạ}",
            "{+1|Cảm ơn|Okee} nha"
        ]
    else:
        spins = [
            "{Bài hay quá|Tuyệt vời|Đỉnh|Chất thế} {anh ơi|ạ|nhé|luôn}",
            "{Xin thông tin|Ib mình với|Cho mình xin giá} {ạ|với|nhé}",
            "{Haha|Thú vị ghê|Quá chuẩn} {luôn|đó}",
            "{Chấm hóng|Lên top|Phê quá} {nè|luôn}"
        ]
    return spin_text(random.choice(spins))

def get_ai_status_or_spin():
    """Tạo status vu vơ tự nhiên để đăng lên tường nhà"""
    API_KEY = os.getenv("GEMINI_API_KEY")
    if API_KEY and HAS_GEMINI:
        try:
            genai.configure(api_key=API_KEY)
            model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"temperature": 0.9})
            prompt = "Đóng vai người dùng Facebook bình thường, viết 1 status ngắn (khoảng 10-20 chữ) về một ngày bình thường, hoặc tâm trạng vu vơ, mệt mỏi, hay vui vẻ để nuôi nick. Không được dùng hashtag. Viết đúng 1 câu."
            response = model.generate_content(prompt)
            result = response.text.replace('"', '').strip()
            if result:
                return result
        except:
            pass
            
    spins = [
        "Hôm nay {trời đẹp|nắng ấm|thời tiết dễ chịu} {mà buồn ngủ quá|thật|nhỉ} 😊.",
        "{Có những ngày|Nhiều lúc} chỉ muốn {ngủ một giấc thật dài|đi đâu đó cho khuây khoả|ngồi uống ly cafe tĩnh lặng}.",
        "Mọi người {ăn cơm|nghỉ ngơi|làm việc} {chưa nhỉ|tốt nhé|chăm chỉ nhé}!",
        "Lâu lâu {trồi lên|ngoáp lên} cho mọi người {đỡ quên mặt|nhớ tui} 😂."
    ]
    return spin_text(random.choice(spins))
