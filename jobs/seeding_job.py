"""
Module: jobs/seeding_job.py
Chức năng: Luồng chính để lấy post, sinh comment, đi comment và cập nhật trạng thái
"""
from db.connector import DBConnector
from ai.comment_generator import generate_comment
from actions.action_comment import comment_to_post
from config.settings import DB_PATH, WEB_LINK_TEMPLATE
from utils.logger import log

def run_seeding_job():
    db = DBConnector(DB_PATH)
    posts = db.fetch_pending_posts()
    for post in posts:
        web_link = WEB_LINK_TEMPLATE.format(post_id=post["id"])
        comment = generate_comment(post, web_link)
        success = comment_to_post(post["url"], comment)
        if success:
            db.update_seeding_status(post["id"], "done")
            log(f"Đã comment thành công cho post {post['id']}")
        else:
            log(f"Comment thất bại cho post {post['id']}")
