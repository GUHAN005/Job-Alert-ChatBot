"""
agent.py - Daily 8:00 AM IST Job Digest Agent.

Finds walk-in interviews and online assessments / online interviews
in Chennai, Coimbatore, and Bangalore for a final-year B.Tech AI & Data Science fresher.
Formats results into card-style messages and delivers them to Telegram.

Can be run via GitHub Actions or locally with --dry-run.
"""

import sys
import logging
import argparse
from dotenv import load_dotenv

# Load environment variables quietly
load_dotenv()

from job_search import (
    search_jobs,
    format_for_telegram,
    send_telegram,
    get_ist_dates
)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("daily_agent")


def run_daily_digest(dry_run: bool = False) -> None:
    """Executes the daily 8:00 AM job search and Telegram delivery."""
    today_str, _, _ = get_ist_dates()
    logger.info(f"Starting daily job search for {today_str} (dry_run={dry_run})...")

    try:
        raw_result = search_jobs(city=None, kind=None, query=None, dry_run=dry_run)

        if not raw_result or not raw_result.strip():
            empty_msg = f"📅 *Daily Job Alert ({today_str})*\n\nNo new openings today."
            if dry_run:
                print("\n" + "=" * 60)
                print("DAILY DIGEST DRY-RUN RESULT")
                print("=" * 60)
                print(empty_msg)
            else:
                send_telegram(empty_msg)
            return

        # Format into clean Telegram card-style message
        formatted_message = (
            f"🚀 *DAILY JOB DIGEST (AI & DATA SCIENCE / TECH FRESHERS)*\n"
            f"📅 *Date:* {today_str} (Today & Next 2 Days)\n"
            f"📍 *Locations:* Chennai, Coimbatore, Bangalore\n\n"
            + format_for_telegram(raw_result)
        )

        if dry_run:
            print("\n" + "=" * 60)
            print("🚀 DAILY DIGEST DRY-RUN RESULT (Printed to stdout, no Telegram call)")
            print("=" * 60 + "\n")
            print(formatted_message)
            print("\n" + "=" * 60)
            print(f"Total message character length: {len(formatted_message)}")
            print("✅ Daily digest dry-run completed successfully.")
            print("=" * 60 + "\n")
            return

        # Send to Telegram
        success = send_telegram(formatted_message)
        if success:
            logger.info("Daily job digest delivered to Telegram successfully!")
        else:
            logger.error("Failed to deliver complete daily digest to Telegram.")
            send_telegram("⚠️ *Notice:* Daily job digest delivery encountered an error.")

    except Exception as e:
        logger.error(f"Error occurred during daily digest run: {e}", exc_info=True)
        if not dry_run:
            error_notice = (
                f"⚠️ *Daily Job Digest Error ({today_str})*\n\n"
                f"The scheduled agent encountered an issue while searching for jobs. "
                f"Please check GitHub Actions logs."
            )
            send_telegram(error_notice)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Daily 8 AM Job Digest Agent")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run search and format results to stdout without sending to Telegram."
    )
    args = parser.parse_args()

    run_daily_digest(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
