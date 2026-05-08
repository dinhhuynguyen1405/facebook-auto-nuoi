"""
scheduler/schedule_plan.py
──────────────────────────────────────────────────────────────────────────────
Lịch nuôi nick 30 ngày dựa trên nghiên cứu hành vi người dùng thực.

Nguyên tắc thiết kế:
  • Tuần 1  (ngày 01-07): "Người mới" — chỉ xem, hầu như không tương tác
  • Tuần 2  (ngày 08-14): "Làm quen"  — bắt đầu like dạo, kết bạn ít
  • Tuần 3  (ngày 15-21): "Hoà nhập"  — comment thật, tham gia group, story
  • Tuần 4+ (ngày 22+)  : "Người thật" — full action, seeding được phép

Mỗi ngày gồm:
  actions   : list (method_name, weight) — pool action cho ngày đó
  sessions  : số phiên chạy trong ngày (mỗi phiên 3-5 action lớn)
  window    : khung giờ hợp lệ để chạy "09:00-22:00" (tránh 2-5 giờ sáng)
  allow_seeding: False/True — ngày này có được comment seeding không
  notes     : mô tả ngắn để log
──────────────────────────────────────────────────────────────────────────────
"""
from typing import Dict, List, Tuple, Any

# Type alias
DayPlan = Dict[str, Any]

# ──────────────────────────────────────────────────────────────────────────────
# HELPER: tạo plan nhanh
# ──────────────────────────────────────────────────────────────────────────────
def _plan(
    actions: List[Tuple[str, int]],
    sessions: int = 2,
    window: str = "09:00-22:00",
    allow_seeding: bool = False,
    notes: str = "",
) -> DayPlan:
    return {
        "actions": actions,
        "sessions": sessions,
        "window": window,
        "allow_seeding": allow_seeding,
        "notes": notes,
    }


# ──────────────────────────────────────────────────────────────────────────────
# SCHEDULE: 30 NGÀY
# key = số ngày nuôi (int), value = DayPlan
# Ngày > 30 sẽ map về plan ngày 30 (full mature)
# ──────────────────────────────────────────────────────────────────────────────
SCHEDULE: Dict[int, DayPlan] = {

    # ════════════════════════════════════════
    # TUẦN 1 — "NGƯỜI MỚI" (chỉ xem, không tương tác)
    # Mục tiêu: tạo lịch sử duyệt, không trigger heuristic
    # ════════════════════════════════════════
    1: _plan(
        actions=[
            ("surf_newsfeed_no_engagement", 60),
            ("check_notifications",         40),
        ],
        sessions=1,
        window="10:00-21:00",
        allow_seeding=False,
        notes="Ngày 1: Chỉ lướt newsfeed nhẹ, xem thông báo. Thời gian online ngắn.",
    ),
    2: _plan(
        actions=[
            ("surf_newsfeed_no_engagement", 40),
            ("watch_reels_no_engagement",   30),
            ("check_notifications",         20),
            ("view_own_profile",            10),
        ],
        sessions=2,
        window="09:30-22:00",
        allow_seeding=False,
        notes="Ngày 2: Lướt thêm Reels, nhìn lại profile bản thân.",
    ),
    3: _plan(
        actions=[
            ("surf_newsfeed_no_engagement", 35),
            ("watch_videos_no_engagement",  25),
            ("watch_reels_no_engagement",   25),
            ("check_notifications",         15),
        ],
        sessions=2,
        window="09:00-22:00",
        allow_seeding=False,
        notes="Ngày 3: Xem Watch video dài, tạo thêm lịch sử xem.",
    ),
    4: _plan(
        actions=[
            ("surf_newsfeed_no_engagement", 30),
            ("search_something",            35),
            ("visit_groups_no_engagement",  25),
            ("check_notifications",         10),
        ],
        sessions=2,
        window="09:00-22:00",
        allow_seeding=False,
        notes="Ngày 4: Tìm kiếm từ khoá, dạo trang Groups (không join).",
    ),
    5: _plan(
        actions=[
            ("surf_newsfeed_no_engagement", 20),
            ("watch_stories",               20),
            ("search_something",            25),
            ("visit_groups_no_engagement",  25),
            ("view_own_profile",            10),
        ],
        sessions=2,
        window="09:00-22:00",
        allow_seeding=False,
        notes="Ngày 5: Xem Stories, tiếp tục tìm kiếm, nhìn Groups.",
    ),
    6: _plan(
        actions=[
            ("surf_newsfeed_no_engagement", 30),
            ("watch_reels_no_engagement",   30),
            ("visit_groups_no_engagement",  20),
            ("check_messages",              10),
            ("view_own_profile",            10),
        ],
        sessions=2,
        window="09:00-22:00",
        allow_seeding=False,
        notes="Ngày 6: Mở Messenger (đừng nhắn gì), xem nhóm.",
    ),
    7: _plan(
        actions=[
            ("surf_newsfeed_no_engagement", 25),
            ("visit_marketplace",           30),
            ("search_something",            25),
            ("check_notifications",         10),
            ("view_own_profile",            10),
        ],
        sessions=2,
        window="09:00-22:00",
        allow_seeding=False,
        notes="Ngày 7: Dạo Marketplace (window shopping), kết thúc tuần 1.",
    ),

    # ════════════════════════════════════════
    # TUẦN 2 — "LÀM QUEN" (bắt đầu like nhẹ, kết bạn ít)
    # Mục tiêu: thêm tín hiệu xã hội, trust score tăng nhẹ
    # ════════════════════════════════════════
    8: _plan(
        actions=[
            ("surf_newsfeed",               30),   # surf CÓ like nhẹ
            ("watch_reels_no_engagement",   25),
            ("search_something",            25),
            ("check_notifications",         20),
        ],
        sessions=2,
        window="09:00-22:00",
        allow_seeding=False,
        notes="Ngày 8: Lần đầu surf có tương tác nhẹ (like dạo). Chưa comment.",
    ),
    9: _plan(
        actions=[
            ("surf_newsfeed",               25),
            ("add_friends_suggested",       30),   # kết bạn nhẹ (1-2 người)
            ("watch_videos",                25),
            ("view_own_profile",            20),
        ],
        sessions=2,
        window="09:00-22:00",
        allow_seeding=False,
        notes="Ngày 9: Kết bạn gợi ý đầu tiên (1-2 người), xem video.",
    ),
    10: _plan(
        actions=[
            ("surf_newsfeed",               25),
            ("visit_groups_no_engagement",  25),
            ("search_something",            25),
            ("add_friends_suggested",       15),
            ("check_messages",              10),
        ],
        sessions=2,
        window="09:00-22:00",
        allow_seeding=False,
        notes="Ngày 10: Kết bạn thêm, bắt đầu dạo Groups sâu hơn.",
    ),
    11: _plan(
        actions=[
            ("surf_newsfeed",               20),
            ("watch_reels",                 20),   # xem reel CÓ thể like
            ("join_target_groups",          30),   # xin vào nhóm đầu tiên
            ("add_friends_suggested",       20),
            ("check_notifications",         10),
        ],
        sessions=2,
        window="09:00-22:00",
        allow_seeding=False,
        notes="Ngày 11: Xin tham gia nhóm đầu tiên (1-2 nhóm). Xem Reels có like.",
    ),
    12: _plan(
        actions=[
            ("surf_newsfeed",               25),
            ("visit_marketplace",           25),
            ("browse_events",               25),
            ("add_friends_suggested",       15),
            ("check_notifications",         10),
        ],
        sessions=2,
        window="09:00-22:00",
        allow_seeding=False,
        notes="Ngày 12: Dạo Events, Marketplace. Tăng breadth profile.",
    ),
    13: _plan(
        actions=[
            ("surf_newsfeed",               20),
            ("join_target_groups",          25),
            ("add_friends_suggested",       25),
            ("watch_stories",               20),
            ("view_own_profile",            10),
        ],
        sessions=3,
        window="09:00-22:00",
        allow_seeding=False,
        notes="Ngày 13: Tăng số phiên lên 3. Tiếp tục xin vào nhóm.",
    ),
    14: _plan(
        actions=[
            ("surf_newsfeed",               20),
            ("watch_videos",                15),
            ("visit_groups",                25),   # visit groups đã vào
            ("add_friends_suggested",       25),
            ("check_messages",              15),
        ],
        sessions=3,
        window="09:00-22:00",
        allow_seeding=False,
        notes="Ngày 14: Kết thúc tuần 2. Dạo trong nhóm đã tham gia.",
    ),

    # ════════════════════════════════════════
    # TUẦN 3 — "HOÀ NHẬP" (comment thật, story, đăng bài)
    # Mục tiêu: tạo nội dung người thật, không seeding link
    # ════════════════════════════════════════
    15: _plan(
        actions=[
            ("surf_newsfeed",               20),
            ("visit_groups",                20),
            ("action_read_and_engage_comments", 25),  # đọc + comment thật
            ("add_friends_suggested",       20),
            ("check_notifications",         15),
        ],
        sessions=3,
        window="09:00-22:00",
        allow_seeding=False,
        notes="Ngày 15: Comment thật đầu tiên (không có link). Tự nhiên.",
    ),
    16: _plan(
        actions=[
            ("surf_newsfeed",               15),
            ("action_read_and_engage_comments", 25),
            ("post_status",                 20),   # đăng status tâm trạng
            ("visit_groups",                25),
            ("check_messages",              15),
        ],
        sessions=3,
        window="09:00-22:00",
        allow_seeding=False,
        notes="Ngày 16: Đăng status đầu tiên. Comment trong nhóm.",
    ),
    17: _plan(
        actions=[
            ("surf_newsfeed",               15),
            ("create_text_story",           20),   # đăng story
            ("action_read_and_engage_comments", 25),
            ("visit_groups",                25),
            ("browse_events",               15),
        ],
        sessions=3,
        window="09:00-22:00",
        allow_seeding=False,
        notes="Ngày 17: Tạo Story chữ. Comment tiếp tục.",
    ),
    18: _plan(
        actions=[
            ("surf_newsfeed",               15),
            ("action_read_and_engage_comments", 20),
            ("visit_groups",                20),
            ("post_status",                 15),
            ("add_friends_suggested",       20),
            ("check_messages",              10),
        ],
        sessions=3,
        window="09:00-22:00",
        allow_seeding=False,
        notes="Ngày 18: Đẩy mạnh comment + kết bạn trong nhóm.",
    ),
    19: _plan(
        actions=[
            ("surf_newsfeed",               15),
            ("action_read_and_engage_comments", 20),
            ("visit_groups",                20),
            ("action_copy_post_text",       10),
            ("action_open_link_in_new_tab", 10),
            ("add_friends_suggested",       15),
            ("check_notifications",         10),
        ],
        sessions=3,
        window="09:00-22:00",
        allow_seeding=False,
        notes="Ngày 19: Thêm hành vi copy text, mở link ngoài — tăng fingerprint đa dạng.",
    ),
    20: _plan(
        actions=[
            ("surf_newsfeed",               15),
            ("watch_reels",                 15),
            ("action_read_and_engage_comments", 20),
            ("create_text_story",           15),
            ("post_status",                 15),
            ("visit_groups",                20),
        ],
        sessions=3,
        window="09:00-22:00",
        allow_seeding=False,
        notes="Ngày 20: Đa dạng nội dung tự tạo — story + status + comment.",
    ),
    21: _plan(
        actions=[
            ("surf_newsfeed",               15),
            ("action_read_and_engage_comments", 20),
            ("visit_groups",                20),
            ("visit_marketplace",           15),
            ("add_friends_suggested",       15),
            ("check_messages",              15),
        ],
        sessions=3,
        window="09:00-22:00",
        allow_seeding=False,
        notes="Ngày 21: Kết thúc tuần 3. Nick đã có profile đủ sâu.",
    ),

    # ════════════════════════════════════════
    # TUẦN 4 — "NGƯỜI THẬT" (full action, seeding bắt đầu nhẹ)
    # Mục tiêu: seeding có link nhưng pha loãng với hành vi thường
    # ════════════════════════════════════════
    22: _plan(
        actions=[
            ("surf_newsfeed",               15),
            ("action_read_and_engage_comments", 20),
            ("visit_groups",                20),
            ("post_status",                 10),
            ("add_friends_suggested",       15),
            ("check_notifications",         10),
            ("check_messages",              10),
        ],
        sessions=3,
        window="09:00-22:00",
        allow_seeding=True,     # BẮT ĐẦU seeding từ ngày 22
        notes="Ngày 22: Seeding bắt đầu — chỉ 1-2 comment/phiên, pha loãng nhiều action khác.",
    ),
    23: _plan(
        actions=[
            ("surf_newsfeed",               15),
            ("action_read_and_engage_comments", 20),
            ("visit_groups",                20),
            ("create_text_story",           10),
            ("post_status",                 10),
            ("add_friends_suggested",       15),
            ("browse_events",               10),
        ],
        sessions=3,
        window="09:00-22:00",
        allow_seeding=True,
        notes="Ngày 23: Tiếp tục seeding nhẹ, duy trì đa dạng hành vi.",
    ),
    24: _plan(
        actions=[
            ("surf_newsfeed",               10),
            ("watch_reels",                 10),
            ("action_read_and_engage_comments", 20),
            ("visit_groups",                20),
            ("post_status",                 10),
            ("add_friends_suggested",       15),
            ("action_open_link_in_new_tab", 10),
            ("visit_marketplace",           5),
        ],
        sessions=3,
        window="09:00-22:00",
        allow_seeding=True,
        notes="Ngày 24: Đa dạng tối đa, seeding đan xen.",
    ),
    25: _plan(
        actions=[
            ("surf_newsfeed",               10),
            ("action_read_and_engage_comments", 20),
            ("visit_groups",                20),
            ("create_text_story",           10),
            ("watch_videos",                10),
            ("add_friends_suggested",       15),
            ("check_messages",              10),
            ("browse_events",               5),
        ],
        sessions=3,
        window="09:00-22:00",
        allow_seeding=True,
        notes="Ngày 25: Ổn định, tiếp tục seeding.",
    ),
    26: _plan(
        actions=[
            ("surf_newsfeed",               10),
            ("action_read_and_engage_comments", 20),
            ("visit_groups",                20),
            ("post_status",                 10),
            ("add_friends_suggested",       10),
            ("watch_reels",                 10),
            ("action_copy_post_text",       5),
            ("check_notifications",         10),
            ("visit_marketplace",           5),
        ],
        sessions=3,
        window="09:00-22:00",
        allow_seeding=True,
        notes="Ngày 26: Duy trì fingerprint đa dạng.",
    ),
    27: _plan(
        actions=[
            ("surf_newsfeed",               10),
            ("action_read_and_engage_comments", 20),
            ("visit_groups",                20),
            ("create_text_story",           10),
            ("post_status",                 10),
            ("add_friends_suggested",       10),
            ("browse_events",               10),
            ("watch_stories",               10),
        ],
        sessions=4,
        window="09:00-22:00",
        allow_seeding=True,
        notes="Ngày 27: Tăng 4 phiên/ngày — nick đã mature.",
    ),
    28: _plan(
        actions=[
            ("surf_newsfeed",               10),
            ("action_read_and_engage_comments", 20),
            ("visit_groups",                20),
            ("post_status",                 10),
            ("watch_reels",                 10),
            ("add_friends_suggested",       10),
            ("check_messages",              10),
            ("action_open_link_in_new_tab", 10),
        ],
        sessions=4,
        window="09:00-22:00",
        allow_seeding=True,
        notes="Ngày 28: Tiếp tục full action.",
    ),
    29: _plan(
        actions=[
            ("surf_newsfeed",               10),
            ("action_read_and_engage_comments", 20),
            ("visit_groups",                20),
            ("create_text_story",           8),
            ("post_status",                 8),
            ("add_friends_suggested",       10),
            ("browse_events",               8),
            ("watch_videos",                8),
            ("visit_marketplace",           8),
        ],
        sessions=4,
        window="09:00-22:00",
        allow_seeding=True,
        notes="Ngày 29: Hành vi đa dạng nhất, nick trust cao.",
    ),
    30: _plan(
        actions=[
            ("surf_newsfeed",               10),
            ("action_read_and_engage_comments", 20),
            ("visit_groups",                20),
            ("create_text_story",           8),
            ("post_status",                 8),
            ("add_friends_suggested",       10),
            ("watch_reels",                 8),
            ("browse_events",               6),
            ("check_messages",              5),
            ("action_open_link_in_new_tab", 5),
        ],
        sessions=4,
        window="09:00-22:00",
        allow_seeding=True,
        notes="Ngày 30+: Nick trưởng thành — full action + seeding bình thường.",
    ),
}


def get_plan(day: int) -> DayPlan:
    """
    Lấy plan cho ngày nuôi `day`.
    Ngày > 30 dùng plan ngày 30 (mature).
    """
    return SCHEDULE.get(min(day, 30), SCHEDULE[30])


def get_window_hours(plan: DayPlan) -> tuple[int, int]:
    """Parse window '09:00-22:00' → (9, 22)."""
    start, end = plan["window"].split("-")
    return int(start.split(":")[0]), int(end.split(":")[0])
