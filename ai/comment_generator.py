"""
Module: ai/comment_generator.py
Chức năng: Sinh comment seeding dựa trên nội dung bài post và loại post
"""
from typing import Dict

def generate_comment(post: Dict, web_link: str) -> str:
    """
    Sinh comment dựa trên loại post và nội dung post
    """
    if post["post_type"] == "tuyen_vang_lai":
        return f"Bài đăng của bạn đã được tự động thêm vào hệ thống Badminton GO để nhiều người biết hơn nhé! Xem chi tiết tại: {web_link}"
    elif post["post_type"] == "tim_san_vang_lai":
        return f"Bạn tham khảo thêm các kèo vãng lai tại các khung giờ phù hợp trên Badminton GO nhé: {web_link}"
    else:
        return f"Tham khảo thêm các kèo cầu lông mới nhất tại Badminton GO: {web_link}"
