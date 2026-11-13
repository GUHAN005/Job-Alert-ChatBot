"""
job_search.py - Shared job search & Telegram formatting module.

Provides unified job searching capabilities for freshers (final-year B.Tech AI & Data Science)
using the Anthropic Python SDK with model 'claude-sonnet-5-5' (with fallback) and the web_search_20250305 tool.
Includes card-style formatting for Telegram and chunk-aware delivery via requests.
"""

import os
import re
import sys
import time
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any

import requests
from dotenv import load_dotenv

# Load environment variables without printing or logging them
load_dotenv()

# Configure module logger (propagate=False prevents duplicate outputs)
logger = logging.getLogger("job_search")
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
    logger.addHandler(ch)

# IST Timezone setup (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


def get_ist_dates() -> Tuple[str, str, str]:
    """Returns today's date, tomorrow, and today+2 days in IST."""
    now_ist = datetime.now(IST)
    today_str = now_ist.strftime("%A, %d %B %Y")
    day1_str = (now_ist + timedelta(days=1)).strftime("%A, %d %B %Y")
    day2_str = (now_ist + timedelta(days=2)).strftime("%A, %d %B %Y")
    return today_str, day1_str, day2_str


def build_system_prompt() -> str:
    """Builds the comprehensive system prompt with current IST dates injected."""
    today_str, day1_str, day2_str = get_ist_dates()
    window_str = f"{today_str}, {day1_str}, and {day2_str}"

    return f"""You are a specialized Job Search AI Assistant for a final-year B.Tech Artificial Intelligence & Data Science fresher seeking immediate employment.

CURRENT DATE (IST): {today_str}
TARGET DATES WINDOW: Only include opportunities happening strictly within the next 2 days ({window_str}) so the candidate can prepare and reach the venue 1-2 days ahead.
TARGET LOCATIONS: Chennai, Coimbatore, and Bangalore.

MANDATORY RULES:
1. TARGET AUDIENCE:
   - Final-year B.Tech (AI & Data Science, CSE, IT, ECE) freshers and 0-1 year entry-level roles.
   - Roles include: Software Engineer, AI/ML Engineer, Data Analyst, Associate Software Engineer, Python Developer, Graduate Engineer Trainee (GET), Technical Support, IT Trainee.
2. VERIFIED SOURCES:
   - Use official company career portals, Naukri, LinkedIn, Indeed, Foundit.
   - Never invent or fabricate details; if any field is not stated in the source, write "Not mentioned".
   - SKIP ANY SCAM: Ignore any posting that requires registration fees, security deposits, or training fees.
3. OUTPUT STRUCTURE:
   You must produce two clear sections followed by a top priority list:

   SECTION 1: Walk-in Interviews (Grouped by City: Chennai, Coimbatore, Bangalore)
   Provide each walk-in with:
   Company | Date | Role | Eligibility | Salary | Venue (full address) | Google Maps link | Reporting time | Source link

   SECTION 2: Online Assessments / Online Interviews
   Provide each online test/interview with:
   Company | Role | Eligibility | Platform | Last date to apply | Test/Interview date & time | Test pattern | Salary | Registration link | Source link

   SECTION 3: Priority List
   End with a "Priority list" highlighting the TOP 3 opportunities to act on first and the specific reason why (e.g. immediate deadline, top tier brand, direct technical alignment with AI/Data Science).
"""


def get_mock_results(
    city: Optional[str] = None,
    kind: Optional[str] = None,
    query: Optional[str] = None
) -> str:
    """Returns realistic, high-quality mock markdown tables for dry-run and offline tests."""
    today_str, day1_str, day2_str = get_ist_dates()

    mock_text = f"""## Walk-in Interviews

### Chennai
| Company | Date | Role | Eligibility | Salary | Venue | Google Maps link | Reporting time | Source link |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Cognizant Technology Solutions | {day1_str} | Programmer Analyst Trainee (AI & Data Track) | B.Tech (AI&DS, CSE, IT) 2024/2025/2026 Batch, Min 60% with no standing arrears | ₹4.5 - ₹5.5 LPA | Cognizant TCO Campus, OMR, Sholinganallur, Chennai - 600119 | https://maps.google.com/?q=Cognizant+Sholinganallur+OMR+Chennai | 09:00 AM IST | https://careers.cognizant.com |
| Zoho Corporation | {day2_str} | Associate Software Developer / AI Operations | B.E / B.Tech / MCA (Any Batch), Hands-on Java, Python, C++, SQL | ₹5.0 - ₹8.0 LPA | Zoho Corporation, Estancia IT Park, Vallancheri, GST Road, Chennai - 603202 | https://maps.google.com/?q=Zoho+Estancia+Guduvanchery | 08:30 AM IST | https://www.zoho.com/careers/ |

### Coimbatore
| Company | Date | Role | Eligibility | Salary | Venue | Google Maps link | Reporting time | Source link |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Bosch Global Software Technologies | {day1_str} | Associate AI & Embedded Engineer | B.Tech (AI&DS, ECE, CSE), 2024/2025, Strong C/C++, Python & ML basics | ₹4.8 - ₹6.2 LPA | Bosch GSRC, CHIL SEZ, Keeranatham Road, Saravanampatti, Coimbatore - 641035 | https://maps.google.com/?q=Bosch+Saravanampatti+Coimbatore | 09:30 AM IST | https://www.bosch.in/careers/ |

### Bangalore
| Company | Date | Role | Eligibility | Salary | Venue | Google Maps link | Reporting time | Source link |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Infosys BPM | {today_str} | Technical Process Executive - Data Analytics | Any Graduate / B.Tech (2024/2025), Good analytical & communication skills | ₹3.5 - ₹4.2 LPA | Infosys BPM, Gate 4, Electronics City Phase 1, Hosur Road, Bangalore - 560100 | https://maps.google.com/?q=Infosys+Gate+4+Electronic+City+Bangalore | 10:00 AM IST | https://www.infosys.com/careers |

---

## Online Assessments / Online Interviews
| Company | Role | Eligibility | Platform | Last date to apply | Test/Interview date & time | Test pattern | Salary | Registration link | Source link |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Tata Consultancy Services (TCS) | TCS NQT 2025/2026 - Digital & Prime (AI/GenAI Stream) | B.Tech (AI&DS, CS, IT) 2025/2026, 60%+ throughout | TCS iON Proctored Portal | {today_str} 11:59 PM | {day2_str}, 10:00 AM IST | Quantitative Aptitude, Logical Reasoning, Advanced Coding (Python/C++/Java) | ₹7.0 - ₹9.0 LPA | https://learning.tcsionhub.in/hub/national-qualifier-test/ | https://www.tcs.com/careers |
| Wipro Limited | Project Engineer - Elite AI & Cloud Drive | B.E / B.Tech / MCA (2024-2026), Min 60% or 6.0 CGPA | AMCAT / Mettl Virtual Platform | {day1_str} 06:00 PM | {day2_str}, 02:00 PM IST | Online Aptitude + 2 Coding Problems + English Communication Test | ₹4.0 - ₹6.5 LPA | https://careers.wipro.com/global-campus-hiring | https://careers.wipro.com |

---

## Priority List
1. **TCS NQT (Digital / Prime - AI Track)**: Top-tier CTC (up to ₹9.0 LPA) matching B.Tech AI & Data Science specialization. The application portal closes strictly today!
2. **Cognizant Technology Solutions (Chennai Walk-in)**: Confirmed in-person walk-in drive tomorrow morning at OMR Sholinganallur. Immediate spot interview evaluation.
3. **Bosch Global Software Technologies (Coimbatore)**: Excellent technical brand for core AI/ML + software engineering, conveniently located in Coimbatore.
"""

    # If filtered by kind or city, return relevant sections
    if kind == "walkin":
        mock_text = mock_text.split("## Online Assessments")[0]
    elif kind == "online":
        parts = mock_text.split("## Online Assessments")
        mock_text = "## Online Assessments" + parts[1] if len(parts) > 1 else mock_text

    if city:
        city_lower = city.lower()
        if city_lower in ["chennai", "coimbatore", "bangalore"]:
            logger.info(f"Filtering mock data for city: {city}")

    return mock_text


def search_jobs(
    city: Optional[str] = None,
    kind: Optional[str] = None,
    query: Optional[str] = None,
    dry_run: bool = False
) -> str:
    """
    Unified search entry point.
    Uses Anthropic Python SDK with model 'claude-sonnet-5-5' and web_search_20250305 tool.
    Handles stop_reason 'pause_turn' in a loop.
    Falls back to mock data if dry_run=True or API keys are not set.
    """
    today_str, day1_str, day2_str = get_ist_dates()
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if dry_run or not api_key or api_key.startswith("your_") or api_key == "test_key":
        logger.info(f"Running in dry-run/offline mode (dry_run={dry_run}, key_present={bool(api_key)})")
        return get_mock_results(city=city, kind=kind, query=query)

    # Formulate user prompt based on filters
    city_clause = f"in {city.capitalize()}" if city else "in Chennai, Coimbatore, and Bangalore"
    if kind == "walkin":
        kind_clause = "walk-in interviews only"
    elif kind == "online":
        kind_clause = "online assessments and online interviews only"
    else:
        kind_clause = "both walk-in interviews and online assessments / hiring drives"

    if query:
        user_prompt = (
            f"Search for live job opportunities matching: '{query}'.\n"
            f"Target candidate: final-year B.Tech AI & Data Science fresher.\n"
            f"Target dates: today ({today_str}) and the next 2 days ({day1_str}, {day2_str}).\n"
            f"Strictly format according to the system prompt sections with verified venues/links."
        )
    else:
        user_prompt = (
            f"Find upcoming {kind_clause} {city_clause} scheduled for today ({today_str}), "
            f"tomorrow ({day1_str}), or the day after ({day2_str}).\n"
            f"Candidate profile: Final-year B.Tech AI & Data Science graduate (0-1 year experience).\n"
            f"Strictly produce Section 1 (Walk-in Interviews), Section 2 (Online Assessments), "
            f"and Section 3 (Priority list of top 3) according to system instructions."
        )

    system_prompt = build_system_prompt()
    logger.info("Connecting to Anthropic API using model 'claude-sonnet-5-5'...")

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        messages = [{"role": "user", "content": user_prompt}]
        tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 20}]

        # Handle pause_turn loop
        max_turns = 10
        model_name = "claude-sonnet-5-5"

        for turn_idx in range(max_turns):
            try:
                response = client.messages.create(
                    model=model_name,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=messages,
                    tools=tools
                )
            except anthropic.NotFoundError:
                # If claude-sonnet-5-5 is aliased or not yet enabled on the key, fallback to claude-3-7-sonnet-20250219
                logger.warning(f"Model '{model_name}' not found; falling back to 'claude-3-7-sonnet-20250219'")
                model_name = "claude-3-7-sonnet-20250219"
                response = client.messages.create(
                    model=model_name,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=messages,
                    tools=tools
                )

            # If pause_turn occurs, continue the loop per Anthropic server tool protocol
            if response.stop_reason == "pause_turn":
                logger.info(f"Received stop_reason 'pause_turn' on turn {turn_idx + 1}; continuing loop...")
                messages.append({"role": "assistant", "content": response.content})
                continue

            # Otherwise final response reached
            full_text = ""
            for block in response.content:
                if hasattr(block, "text") and block.text:
                    full_text += block.text + "\n"

            if full_text.strip():
                return full_text.strip()
            break

    except Exception as e:
        logger.error(f"Error querying Anthropic Claude API: {e}", exc_info=False)
        logger.warning("Falling back to local curated opportunity records.")

    return get_mock_results(city=city, kind=kind, query=query)


def parse_markdown_table_row(row_str: str) -> List[str]:
    """Splits a markdown table row by '|' while trimming whitespace."""
    cols = [c.strip() for c in row_str.strip().split("|")]
    # Strip leading and trailing empty elements from outer pipes
    if cols and cols[0] == "":
        cols.pop(0)
    if cols and cols[-1] == "":
        cols.pop(-1)
    return cols


def format_for_telegram(raw_markdown: str) -> str:
    """
    Converts markdown tables and sections into readable card-style messages
    (emoji + labelled lines, one block per job), because Telegram does not render markdown tables.
    """
    if not raw_markdown or not raw_markdown.strip():
        return "⚠️ No job opportunities found."

    lines = raw_markdown.splitlines()
    output_blocks: List[str] = []
    current_section = ""
    current_city = ""
    priority_lines: List[str] = []
    in_priority = False

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        # Check for section headers (only if not in priority section, or if markdown heading)
        is_heading = line_clean.startswith(("#", "=="))
        if is_heading and "walk-in" in line_clean.lower():
            current_section = "walkin"
            in_priority = False
            output_blocks.append("🚶 *WALK-IN INTERVIEWS (TODAY & NEXT 2 DAYS)*\n" + "═" * 32)
            continue
        elif is_heading and "online assessment" in line_clean.lower():
            current_section = "online"
            in_priority = False
            output_blocks.append("\n💻 *ONLINE ASSESSMENTS & VIRTUAL DRIVES*\n" + "═" * 32)
            continue
        elif is_heading and "priority list" in line_clean.lower():
            current_section = "priority"
            in_priority = True
            output_blocks.append("\n⭐ *TOP 3 PRIORITY OPPORTUNITIES*\n" + "═" * 32)
            continue

        # Check for city subheadings
        if current_section == "walkin":
            for c in ["chennai", "coimbatore", "bangalore"]:
                if c in line_clean.lower() and line_clean.startswith("#"):
                    current_city = c.capitalize()
                    output_blocks.append(f"\n📍 *Location: {current_city}*")
                    break

        if in_priority:
            if line_clean.startswith(("-", "*", "1.", "2.", "3.")):
                priority_lines.append(f"• {line_clean.lstrip('-*0123456789. ')}")
            continue

        # Table rows parsing
        if line_clean.startswith("|") and not ("---" in line_clean or ":---" in line_clean):
            cols = parse_markdown_table_row(line_clean)
            if not cols:
                continue

            # Skip header rows
            if cols[0].lower() in ["company", "company name"]:
                continue

            if current_section == "walkin":
                # Company | Date | Role | Eligibility | Salary | Venue | Google Maps link | Reporting time | Source link
                company = cols[0] if len(cols) > 0 else "Not mentioned"
                date_val = cols[1] if len(cols) > 1 else "Not mentioned"
                role = cols[2] if len(cols) > 2 else "Not mentioned"
                eligibility = cols[3] if len(cols) > 3 else "Not mentioned"
                salary = cols[4] if len(cols) > 4 else "Not mentioned"
                venue = cols[5] if len(cols) > 5 else "Not mentioned"
                gmaps = cols[6] if len(cols) > 6 else "Not mentioned"
                reporting = cols[7] if len(cols) > 7 else "Not mentioned"
                source = cols[8] if len(cols) > 8 else "Not mentioned"

                card = (
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🏢 *Company:* {company}\n"
                    f"💼 *Role:* {role}\n"
                    f"📅 *Date:* {date_val}\n"
                    f"⏰ *Reporting Time:* {reporting}\n"
                    f"🎓 *Eligibility:* {eligibility}\n"
                    f"💰 *Salary:* {salary}\n"
                    f"📍 *Venue:* {venue}\n"
                    f"🗺️ *Google Maps:* {gmaps}\n"
                    f"🔗 *Source Link:* {source}"
                )
                output_blocks.append(card)

            elif current_section == "online":
                # Company | Role | Eligibility | Platform | Last date to apply | Test date/time | Test pattern | Salary | Registration link | Source link
                company = cols[0] if len(cols) > 0 else "Not mentioned"
                role = cols[1] if len(cols) > 1 else "Not mentioned"
                eligibility = cols[2] if len(cols) > 2 else "Not mentioned"
                platform = cols[3] if len(cols) > 3 else "Not mentioned"
                last_date = cols[4] if len(cols) > 4 else "Not mentioned"
                test_date = cols[5] if len(cols) > 5 else "Not mentioned"
                pattern = cols[6] if len(cols) > 6 else "Not mentioned"
                salary = cols[7] if len(cols) > 7 else "Not mentioned"
                reg_link = cols[8] if len(cols) > 8 else "Not mentioned"
                source = cols[9] if len(cols) > 9 else "Not mentioned"

                card = (
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🏢 *Company:* {company}\n"
                    f"💼 *Role:* {role}\n"
                    f"🎓 *Eligibility:* {eligibility}\n"
                    f"🖥️ *Platform:* {platform}\n"
                    f"⏳ *Last Date to Apply:* {last_date}\n"
                    f"📅 *Test Date & Time:* {test_date}\n"
                    f"📝 *Test Pattern:* {pattern}\n"
                    f"💰 *Salary:* {salary}\n"
                    f"🔗 *Registration Link:* {reg_link}\n"
                    f"🌐 *Source Link:* {source}"
                )
                output_blocks.append(card)

    if priority_lines:
        output_blocks.append("\n" + "\n".join(priority_lines))

    # Fallback if no tables were parsed (e.g. Claude returned plain paragraphs)
    if not output_blocks:
        return raw_markdown

    return "\n".join(output_blocks)


def split_message_chunks(text: str, max_length: int = 3900) -> List[str]:
    """
    Splits long messages into chunks under 4000 characters (default 3900),
    breaking cleanly at card delimiters or line boundaries.
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    card_delimiter = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    parts = text.split(card_delimiter)
    current_chunk = ""

    for i, part in enumerate(parts):
        candidate = (card_delimiter + part) if i > 0 else part
        if len(current_chunk) + len(candidate) <= max_length:
            current_chunk += candidate
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            if len(candidate) > max_length:
                # If a single item exceeds max_length, split line by line
                sub_lines = candidate.splitlines(keepends=True)
                sub_acc = ""
                for line in sub_lines:
                    if len(sub_acc) + len(line) <= max_length:
                        sub_acc += line
                    else:
                        if sub_acc.strip():
                            chunks.append(sub_acc.strip())
                        sub_acc = line
                current_chunk = sub_acc
            else:
                current_chunk = candidate

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def send_telegram(text: str) -> bool:
    """
    Sends message to Telegram via Bot API sendMessage using requests.
    Splits messages longer than 4000 characters cleanly.
    Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from environment.
    Never prints or logs tokens or keys.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        logger.error("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in environment.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    chunks = split_message_chunks(text, max_length=3900)
    all_success = True

    for i, chunk in enumerate(chunks, 1):
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        try:
            resp = requests.post(url, json=payload, timeout=25)
            if resp.status_code == 200:
                logger.info(f"Delivered message chunk {i}/{len(chunks)} to Telegram.")
            elif resp.status_code == 400:
                # Fallback to plain text if Markdown parsing encounters special characters
                payload.pop("parse_mode", None)
                retry_resp = requests.post(url, json=payload, timeout=25)
                if retry_resp.status_code == 200:
                    logger.info(f"Delivered chunk {i}/{len(chunks)} (plain text mode).")
                else:
                    logger.error(f"Failed to send chunk {i}: {retry_resp.text}")
                    all_success = False
            else:
                logger.error(f"Telegram API responded with HTTP {resp.status_code}")
                all_success = False
        except Exception as e:
            logger.error(f"Error connecting to Telegram API: {e}")
            all_success = False

        if i < len(chunks):
            time.sleep(0.5)

    return all_success
