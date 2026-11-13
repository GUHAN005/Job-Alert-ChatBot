"""
bot.py - Interactive Telegram Bot for Job Alerts.

Key Features:
- Pure long-polling using 'requests' library only (no external frameworks).
- Calls deleteWebhook at startup to guarantee polling functions.
- Security: Strictly ignores all users except TELEGRAM_CHAT_ID (silent drop).
- Security: Never prints or logs bot tokens or API keys.
- Commands: /start, /help, /today, /chennai, /coimbatore, /bangalore, /online, /walkin, and custom text queries.
- Instant response: Sends 'Searching... please wait' immediately.
- 30-minute cache per command to conserve API credits.
- Rate limiting: Maximum 20 searches per day.
- Offset tracking in .bot_offset to prevent duplicate message processing.
- Robust error handling with friendly user notifications.
- --dry-run mode for offline testing without Telegram calls.
"""

import os
import sys
import time
import json
import logging
import argparse
from datetime import datetime, date, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any

import requests
from dotenv import load_dotenv

# Load environment variables quietly
load_dotenv()

from job_search import (
    search_jobs,
    format_for_telegram,
    split_message_chunks,
    get_ist_dates
)

# Configure logger (ensuring no tokens or keys are printed)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("telegram_bot")

OFFSET_FILE = ".bot_offset"
RATE_LIMIT_FILE = ".bot_rate_limit.json"
CACHE_EXPIRY_SECONDS = 1800  # 30 minutes
MAX_DAILY_SEARCHES = 20

# In-memory query cache: command_or_query -> {"timestamp": float, "text": str}
QUERY_CACHE: Dict[str, Dict[str, Any]] = {}

IST = timezone(timedelta(hours=5, minutes=30))


class InteractiveJobBot:
    def __init__(self, token: str, allowed_chat_id: str):
        self.token = token
        self.allowed_chat_id = str(allowed_chat_id).strip()
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.session = requests.Session()
        self.offset = self._load_offset()
        self.daily_usage = self._load_rate_limit()

    def _load_offset(self) -> Optional[int]:
        """Loads last processed update offset from disk."""
        if os.path.exists(OFFSET_FILE):
            try:
                with open(OFFSET_FILE, "r", encoding="utf-8") as f:
                    val = f.read().strip()
                    if val.isdigit():
                        return int(val)
            except Exception as e:
                logger.warning(f"Could not read offset file: {e}")
        return None

    def _save_offset(self, offset: int) -> None:
        """Persists the update offset to disk."""
        self.offset = offset
        try:
            with open(OFFSET_FILE, "w", encoding="utf-8") as f:
                f.write(str(offset))
        except Exception as e:
            logger.warning(f"Could not write offset file: {e}")

    def _load_rate_limit(self) -> Dict[str, Any]:
        """Loads daily search usage from disk."""
        today_str = datetime.now(IST).strftime("%Y-%m-%d")
        default_state = {"date": today_str, "count": 0}

        if os.path.exists(RATE_LIMIT_FILE):
            try:
                with open(RATE_LIMIT_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("date") == today_str:
                        return data
            except Exception:
                pass
        return default_state

    def _save_rate_limit(self) -> None:
        """Saves daily search usage to disk."""
        try:
            with open(RATE_LIMIT_FILE, "w", encoding="utf-8") as f:
                json.dump(self.daily_usage, f)
        except Exception as e:
            logger.warning(f"Could not save rate limit file: {e}")

    def can_search_today(self) -> Tuple[bool, int]:
        """Verifies if the user is within the daily rate limit of 20 searches."""
        today_str = datetime.now(IST).strftime("%Y-%m-%d")
        if self.daily_usage.get("date") != today_str:
            self.daily_usage = {"date": today_str, "count": 0}
            self._save_rate_limit()

        current_count = self.daily_usage.get("count", 0)
        remaining = MAX_DAILY_SEARCHES - current_count
        return (current_count < MAX_DAILY_SEARCHES, remaining)

    def increment_search_count(self) -> int:
        """Increments and returns current daily searches."""
        today_str = datetime.now(IST).strftime("%Y-%m-%d")
        if self.daily_usage.get("date") != today_str:
            self.daily_usage = {"date": today_str, "count": 0}

        self.daily_usage["count"] = self.daily_usage.get("count", 0) + 1
        self._save_rate_limit()
        return self.daily_usage["count"]

    def delete_webhook_if_set(self) -> None:
        """Calls deleteWebhook at startup so long polling is guaranteed to work."""
        url = f"{self.base_url}/deleteWebhook"
        try:
            resp = self.session.post(url, json={"drop_pending_updates": False}, timeout=15)
            if resp.status_code == 200:
                logger.info("Checked and cleared any active webhook successfully.")
            else:
                logger.warning(f"deleteWebhook returned status code {resp.status_code}")
        except Exception as e:
            logger.warning(f"Error calling deleteWebhook: {e}")

    def send_message(self, chat_id: str, text: str) -> bool:
        """Sends a message, splitting into chunks under 4000 characters if required."""
        url = f"{self.base_url}/sendMessage"
        chunks = split_message_chunks(text, max_length=3900)
        success = True

        for i, chunk in enumerate(chunks, 1):
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            try:
                resp = self.session.post(url, json=payload, timeout=25)
                if resp.status_code == 200:
                    continue
                elif resp.status_code == 400:
                    # Retry without parse_mode in case Markdown has unescaped characters
                    payload.pop("parse_mode", None)
                    retry = self.session.post(url, json=payload, timeout=25)
                    if retry.status_code != 200:
                        logger.error(f"Failed to send chunk {i}: {retry.text}")
                        success = False
                else:
                    logger.error(f"Telegram API error {resp.status_code}: {resp.text}")
                    success = False
            except Exception as e:
                logger.error(f"Network error while sending message chunk: {e}")
                success = False

            if i < len(chunks):
                time.sleep(0.5)

        return success

    def get_updates(self, timeout: int = 30) -> List[Dict[str, Any]]:
        """Long polls the getUpdates endpoint."""
        url = f"{self.base_url}/getUpdates"
        params = {"timeout": timeout}
        if self.offset is not None:
            params["offset"] = self.offset

        try:
            resp = self.session.get(url, params=params, timeout=timeout + 10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    return data.get("result", [])
        except requests.exceptions.Timeout:
            # Expected during long polling when no new messages exist
            return []
        except requests.exceptions.RequestException as e:
            logger.warning(f"Connection issue in getUpdates: {e}")
            time.sleep(3)
        return []

    def handle_message(self, message: Dict[str, Any]) -> None:
        """
        Processes an incoming message with security check, command dispatch,
        instant waiting message, 30-min cache, and daily rate limit.
        """
        chat_id = str(message.get("chat", {}).get("id", "")).strip()
        first_name = message.get("from", {}).get("first_name", "Candidate")
        text = message.get("text", "").strip()

        # 1. SECURITY CHECK: Only respond to authorized TELEGRAM_CHAT_ID
        if chat_id != self.allowed_chat_id:
            # Ignore every other user silently without replying
            logger.warning(f"Silently ignored message from unauthorized chat_id={chat_id}")
            return

        if not text:
            return

        logger.info(f"Processing authorized message: '{text}'")

        # 2. COMMAND HANDLING
        cmd = text.split()[0].lower() if text.startswith("/") else ""

        if cmd in ["/start", "/help"]:
            welcome_text = (
                f"👋 *Hello {first_name}! Welcome to Walk-in Job Alert Agent.*\n\n"
                "I scan live opportunities for *final-year B.Tech AI & Data Science* "
                "freshers happening today or in the next 2 days across Chennai, Coimbatore, and Bangalore.\n\n"
                "📌 *Available Commands:*\n"
                "• /today — All walk-ins & online tests for today and next 2 days\n"
                "• /chennai — Openings in Chennai only\n"
                "• /coimbatore — Openings in Coimbatore only\n"
                "• /bangalore — Openings in Bangalore only\n"
                "• /online — Online assessments & virtual coding tests only\n"
                "• /walkin — In-person walk-in interviews only\n"
                "• /help — Show this help message\n\n"
                "🔍 *Custom Query:*\n"
                "Send any regular text (e.g. _\"AI jobs in Chennai tomorrow\"_, _\"Data analyst walkin Bangalore\"_) "
                "to execute a real-time web search."
            )
            self.send_message(chat_id, welcome_text)
            return

        # Map commands to search criteria
        city = None
        kind = None
        query = None

        if cmd == "/today":
            city = None
            kind = None
        elif cmd == "/chennai":
            city = "chennai"
        elif cmd == "/coimbatore":
            city = "coimbatore"
        elif cmd == "/bangalore":
            city = "bangalore"
        elif cmd == "/online":
            kind = "online"
        elif cmd == "/walkin":
            kind = "walkin"
        else:
            query = text

        cache_key = (cmd if cmd else query.strip().lower())

        # 3. 30-MINUTE CACHE CHECK
        now_ts = time.time()
        if cache_key in QUERY_CACHE:
            entry = QUERY_CACHE[cache_key]
            if now_ts - entry["timestamp"] < CACHE_EXPIRY_SECONDS:
                mins_ago = int((now_ts - entry["timestamp"]) // 60)
                logger.info(f"Serving cached result for '{cache_key}' ({mins_ago}m old).")
                self.send_message(
                    chat_id,
                    f"⚡ *Showing cached result from {mins_ago} min ago* (conserves API credits):\n\n"
                    + entry["text"]
                )
                return

        # 4. RATE LIMIT CHECK (Max 20 searches per day)
        allowed, remaining = self.can_search_today()
        if not allowed:
            limit_msg = (
                "⚠️ *Daily Search Limit Reached*\n\n"
                f"You have used all {MAX_DAILY_SEARCHES} searches for today.\n"
                "Your limit will reset at midnight. Please try again tomorrow!"
            )
            self.send_message(chat_id, limit_msg)
            return

        # 5. IMMEDIATE "Searching... please wait" NOTICE
        self.send_message(
            chat_id,
            "🔍 *Searching for fresh opportunities...*\n"
            "Please wait, scanning verified portals and company pages (takes 30-90 seconds) ⏳"
        )

        # 6. EXECUTE SEARCH WITH TRY/EXCEPT
        try:
            today_str, _, _ = get_ist_dates()
            logger.info(f"Running search: city={city}, kind={kind}, query={query}")

            raw_result = search_jobs(city=city, kind=kind, query=query, dry_run=False)

            if not raw_result or not raw_result.strip():
                formatted_message = f"📅 *Job Search Update ({today_str})*\n\nNo matching openings found right now."
            else:
                scope_title = (
                    f"Search Query: '{query}'" if query else
                    f"City: {city.capitalize()}" if city else
                    f"Category: {'Walk-ins Only' if kind == 'walkin' else 'Online Only' if kind == 'online' else 'All Openings'}"
                )
                formatted_message = (
                    f"🚀 *JOB ALERTS — {scope_title.upper()}*\n"
                    f"📅 *Window:* Today & Next 2 Days\n\n"
                    + format_for_telegram(raw_result)
                )

            # Store in 30-minute cache
            QUERY_CACHE[cache_key] = {
                "timestamp": now_ts,
                "text": formatted_message
            }

            # Increment daily usage
            used = self.increment_search_count()
            logger.info(f"Search completed. Daily searches used: {used}/{MAX_DAILY_SEARCHES}")

            # Send formatted cards
            self.send_message(chat_id, formatted_message)

        except Exception as e:
            logger.error(f"Error handling user request: {e}", exc_info=True)
            self.send_message(
                chat_id,
                "⚠️ *Temporary Error:* Could not complete the job search at this time. "
                "Please try again in a few minutes."
            )

    def run(self) -> None:
        """Starts the Telegram bot polling loop."""
        logger.info("Initializing Walk-in Job Alert Bot...")
        # Clear any dangling webhook first
        self.delete_webhook_if_set()
        logger.info(f"Starting long polling (only responding to chat_id={self.allowed_chat_id})...")

        while True:
            try:
                updates = self.get_updates(timeout=30)
                for update in updates:
                    update_id = update.get("update_id")
                    if update_id is not None:
                        # Advance offset immediately
                        self._save_offset(update_id + 1)

                    if "message" in update:
                        self.handle_message(update["message"])

            except KeyboardInterrupt:
                logger.info("Bot execution halted by user.")
                break
            except Exception as e:
                logger.error(f"Unexpected error in polling loop: {e}", exc_info=True)
                time.sleep(5)


def run_dry_run(query: Optional[str] = None) -> None:
    """
    Executes dry-run mode:
    Simulates command processing, converts tables to card-style Telegram blocks,
    checks chunk limits (<4000 chars), and tests caching & rate limiting offline.
    """
    today_str, _, _ = get_ist_dates()
    print("\n" + "=" * 60)
    print("🚀 BOT DRY-RUN MODE (Testing offline without Telegram)")
    print("=" * 60)

    test_queries = [query] if query else [
        "/today",
        "/chennai",
        "/online",
        "AI jobs in Chennai tomorrow"
    ]

    for q in test_queries:
        print(f"\n--- Simulating Command: '{q}' ---")
        city = None
        kind = None
        user_query = None

        if q == "/today":
            city, kind = None, None
        elif q == "/chennai":
            city = "chennai"
        elif q == "/coimbatore":
            city = "coimbatore"
        elif q == "/bangalore":
            city = "bangalore"
        elif q == "/online":
            kind = "online"
        elif q == "/walkin":
            kind = "walkin"
        else:
            user_query = q

        raw = search_jobs(city=city, kind=kind, query=user_query, dry_run=True)
        formatted = (
            f"🚀 *JOB ALERTS — {q.upper()}*\n"
            f"📅 *Date:* {today_str}\n\n"
            + format_for_telegram(raw)
        )
        chunks = split_message_chunks(formatted, max_length=3900)

        print(f"Total chunks: {len(chunks)}")
        for idx, chunk in enumerate(chunks, 1):
            print(f"[Chunk {idx} length: {len(chunk)} characters]")
            print(chunk[:300] + ("...\n(truncated preview)" if len(chunk) > 300 else ""))
            assert len(chunk) <= 4000, f"Chunk {idx} exceeds 4000 chars: {len(chunk)}"

    # Test Cache Simulation
    print("\n--- Testing 30-Minute Cache Simulation ---")
    mock_key = "/today"
    QUERY_CACHE[mock_key] = {"timestamp": time.time(), "text": "Sample Cached Content"}
    hit = (time.time() - QUERY_CACHE[mock_key]["timestamp"]) < CACHE_EXPIRY_SECONDS
    print(f"Cache key '{mock_key}' active: {hit} (Expires in 30 minutes)")

    # Test Rate Limiting Simulation
    print("\n--- Testing Daily 20-Search Rate Limiting Simulation ---")
    dummy = InteractiveJobBot(token="DUMMY_TOKEN", allowed_chat_id="123456789")
    dummy.daily_usage = {"date": datetime.now(IST).strftime("%Y-%m-%d"), "count": 19}
    can_19, rem_19 = dummy.can_search_today()
    print(f"Usage at 19/20: can_search={can_19}, remaining={rem_19}")
    dummy.daily_usage["count"] = 20
    can_20, rem_20 = dummy.can_search_today()
    print(f"Usage at 20/20: can_search={can_20}, remaining={rem_20} (Blocked as required)")
    assert not can_20, "Rate limiter failed to block at 20 searches."

    print("\n" + "=" * 60)
    print("✅ Bot dry-run finished successfully! All checks passed.")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Interactive Walk-in Job Alert Telegram Bot")
    parser.add_argument(
        "--dry-run",
        nargs="?",
        const="default",
        help="Run offline dry-run simulation with sample queries without contacting Telegram."
    )
    args = parser.parse_args()

    if args.dry_run is not None:
        sample_q = None if args.dry_run == "default" else args.dry_run
        run_dry_run(sample_q)
        return

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        logger.error(
            "Missing environment variables! Please configure TELEGRAM_BOT_TOKEN and "
            "TELEGRAM_CHAT_ID in .env."
        )
        logger.info("Tip: You can test offline using: python bot.py --dry-run")
        sys.exit(1)

    bot = InteractiveJobBot(token=bot_token, allowed_chat_id=chat_id)
    bot.run()


if __name__ == "__main__":
    main()
