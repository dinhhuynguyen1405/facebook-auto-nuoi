"""
Script test tự động cho toàn bộ pipeline seeding
Chạy: python3 test_seeding_job.py
"""
from jobs.seeding_job import run_seeding_job

def main():
    print("=== BẮT ĐẦU TEST PIPELINE SEEDING ===")
    run_seeding_job()
    print("=== KẾT THÚC TEST ===")

if __name__ == "__main__":
    main()
