import schedule
import time
import os
import sys
from datetime import datetime

# Add project directory to path
sys.path.append(os.path.dirname(__file__))

from data_pipeline    import run_pipeline
from skill_extractor  import process_all_jobs

LAST_UPDATED = os.path.join("data", "last_updated.txt")


def get_last_updated():
    """Return last update timestamp as string."""
    if not os.path.exists(LAST_UPDATED):
        return "Never"
    with open(LAST_UPDATED, "r") as f:
        return f.read().strip()


def run_full_pipeline():
    """Run data pipeline + skill extractor together."""
    print("\n" + "=" * 55)
    print(f"SCHEDULED UPDATE STARTED")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    try:
        # Step 1 — Fetch fresh jobs
        run_pipeline()

        # Step 2 — Extract skills from fresh jobs
        process_all_jobs()

        print("\n✅ Pipeline completed successfully.")
        print(f"Next update in 24 hours.")

    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")


def start_scheduler():
    """
    Run pipeline immediately on start,
    then schedule every 24 hours.
    """
    print("=" * 55)
    print("JOB NAVIGATOR — AUTO SCHEDULER")
    print("=" * 55)
    print(f"Last updated: {get_last_updated()}")
    print("Running initial pipeline now...")

    # Run immediately on start
    run_full_pipeline()

    # Schedule every 24 hours
    schedule.every(24).hours.do(run_full_pipeline)
    print(f"\n✅ Scheduler active — updates every 24 hours.")
    print("Press Ctrl+C to stop.\n")

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    start_scheduler()