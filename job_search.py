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


def has_anthropic_key() -> bool:
    """Checks whether a valid Anthropic API key is configured in .env."""
    key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    return bool(key and not key.startswith("your_") and key != "test_key")


def get_ist_dates() -> Tuple[str, str, str]:
    """Returns today's date, tomorrow, and today+2 days in IST for legacy compatibility."""
    now_ist = datetime.now(IST)
    today_str = now_ist.strftime("%A, %d %B %Y")
    day1_str = (now_ist + timedelta(days=1)).strftime("%A, %d %B %Y")
    day2_str = (now_ist + timedelta(days=2)).strftime("%A, %d %B %Y")
    return today_str, day1_str, day2_str


def get_ist_date_window(days: int = 5) -> Dict[str, str]:
    """Returns formatted dates for today and the next N days (up to 5 days ahead) in IST."""
    now_ist = datetime.now(IST)
    d = {}
    for i in range(days + 1):
        d[f"day{i}"] = (now_ist + timedelta(days=i)).strftime("%A, %d %B %Y")
    d["today"] = d["day0"]
    d["start_date"] = d["day0"]
    d["end_date"] = d[f"day{days}"]
    d["window_str"] = f"{d['day0']} to {d[f'day{days}']}"
    return d


def build_system_prompt() -> str:
    """Builds the comprehensive system prompt with up to 5 days advance notice window in IST."""
    dw = get_ist_date_window(days=5)
    today_str = dw["today"]
    window_str = dw["window_str"]

    return f"""You are a specialized Job Search AI Assistant prioritizing IT & CSE cluster jobs for final-year engineering students and tech freshers (0-1 year experience).

CURRENT DATE (IST): {today_str}
ADVANCE NOTICE WINDOW (UP TO 5 DAYS AHEAD): Only include opportunities scheduled strictly within the next 5 days ({window_str}) so the candidate receives updates up to 5 days in advance to plan travel, book transit, and reach the company venue in Chennai, Coimbatore, or Bangalore directly.
TARGET LOCATIONS: Chennai, Coimbatore, and Bangalore (plus pan-India Online Assessments).

MANDATORY RULES:
1. TARGET AUDIENCE & IT/CSE CLUSTER PRIORITY:
   Prioritize IT & CSE cluster jobs only. Preferred roles:
   - Software Developer / Software Engineer
   - Java Developer
   - Full Stack / MERN Developer
   - Web Developer
   - AI / ML Engineer
   - Data Analyst / Data Engineer
   - QA / Testing Engineer
   - IT Support / Systems Engineer

2. MINIMUM 10 JOBS REQUIREMENT:
   Provide AT LEAST 10 verified job opportunities in every comprehensive search / daily digest:
   - At least 7-8 in-person Walk-in drives distributed across Chennai, Coimbatore, and Bangalore scheduled over the next 5 days.
   - At least 3-4 Online Assessments or Virtual Coding Interviews.

3. ADVANCE NOTICE SCHEDULING (UP TO 5 DAYS AHEAD):
   Every opportunity must be scheduled within the 5-day window so the candidate can prepare and reach the venue directly. Clearly display the interview date and reporting time for each walk-in.

4. DIRECT SCANNING OF ALL OFFICIAL COMPANY CAREER WEBSITES:
   - You MUST prioritize direct searches across official company career websites:
     * Zoho Careers (https://www.zoho.com/careers/)
     * Cognizant Careers (https://careers.cognizant.com/global/en)
     * TCS Careers & iON Hub (https://www.tcs.com/careers, https://www.tcsion.com/hub/national-qualifier-test/)
     * Infosys Careers (https://career.infosys.com/)
     * Wipro Careers (https://careers.wipro.com/careers-home/jobs)
     * HCLTech Careers (https://www.hcltech.com/careers)
     * Bosch India Careers (https://www.bosch.in/careers/)
     * Tech Mahindra Careers (https://careers.techmahindra.com/)
     * Accenture India (https://www.accenture.com/in-en/careers/jobsearch?jk=Associate%20Software%20Engineer)
     * Capgemini Careers (https://www.capgemini.com/in-en/careers/job-search/)
     * LTIMindtree, Hexaware, KGISL, Virtusa, and product companies in Chennai, Coimbatore, Bangalore.
   - Registration links and source links MUST lead directly to the company's official career portal or active registration form.
   - NEVER output broken/guessed subdomains (always use verified live domains).
   - All Google Maps links MUST use universal format: https://www.google.com/maps/search/?api=1&query=<Company+and+Venue+Name>
   - SKIP ANY SCAM: Ignore any posting that requires registration fees, security deposits, or training fees.

5. OUTPUT STRUCTURE:
   SECTION 1: Walk-in Interviews (Grouped by City: Chennai, Coimbatore, Bangalore)
   Provide each walk-in with:
   Company | Date | Role | Eligibility | Salary | Venue (full address) | Google Maps link | Reporting time | Source link

   SECTION 2: Online Assessments / Online Interviews
   Provide each online test/interview with:
   Company | Role | Eligibility | Platform | Last date to apply | Test/Interview date & time | Test pattern | Salary | Registration link | Source link

   SECTION 3: Priority List
   End with a "Priority list" highlighting the TOP 3 opportunities to act on first with specific reasoning (deadline urgency, top tier brand, technical role match).
"""


def get_mock_results(
    city: Optional[str] = None,
    kind: Optional[str] = None,
    query: Optional[str] = None
) -> str:
    """Returns realistic, high-quality mock markdown tables for dry-run and offline tests (10+ IT & CSE jobs, 5-day advance window)."""
    dw = get_ist_date_window(days=5)
    today_str = dw["day0"]
    day1_str = dw["day1"]
    day2_str = dw["day2"]
    day3_str = dw["day3"]
    day4_str = dw["day4"]
    day5_str = dw["day5"]

    chennai_table = f"""### Chennai
| Company | Date | Role | Eligibility | Salary | Venue | Google Maps link | Reporting time | Source link |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Cognizant Technology Solutions | {day2_str} (in 2 days) | Programmer Analyst Trainee (Java / Full Stack Track) | B.Tech / B.E (CSE, IT, AI&DS) 2024/2025/2026 Batch, Min 60% with no standing arrears | ₹4.5 - ₹5.5 LPA | Cognizant TCO Campus, OMR, Sholinganallur, Chennai - 600119 | https://www.google.com/maps/search/?api=1&query=Cognizant+Technology+Solutions+Sholinganallur+Chennai | 09:00 AM IST | https://careers.cognizant.com/global/en |
| HCLTech | {day3_str} (in 3 days) | Associate Engineer (QA & Automation Testing) | B.Tech (CSE, IT, ECE, AI&DS), Basic Selenium, Core Java, Python | ₹4.0 - ₹5.0 LPA | HCLTech ELCOT SEZ, Sholinganallur Medavakkam High Road, Chennai - 600119 | https://www.google.com/maps/search/?api=1&query=HCLTech+ELCOT+SEZ+Sholinganallur+Chennai | 09:30 AM IST | https://www.hcltech.com/careers |
| Zoho Corporation | {day4_str} (in 4 days) | Software Developer / Web & Java Developer | B.E / B.Tech / MCA (Any Tech Batch), Hands-on Java, Python, C++, SQL | ₹5.0 - ₹8.5 LPA | Zoho Corporation, Estancia IT Park, Vallancheri, GST Road, Chennai - 603202 | https://www.google.com/maps/search/?api=1&query=Zoho+Corporation+Estancia+Vallancheri+Guduvanchery+Chennai | 08:30 AM IST | https://www.zoho.com/careers/ |"""

    coimbatore_table = f"""### Coimbatore
| Company | Date | Role | Eligibility | Salary | Venue | Google Maps link | Reporting time | Source link |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| KGISL Technologies | {day2_str} (in 2 days) | Web Developer / Full Stack MERN Trainee | B.Tech / B.Sc CS / BCA / MCA (2024-2026), React.js, Node.js, JavaScript | ₹3.6 - ₹4.5 LPA | KGISL Campus, CHIL SEZ, Keeranatham, Coimbatore - 641035 | https://www.google.com/maps/search/?api=1&query=KGISL+Campus+Keeranatham+Saravanampatti+Coimbatore | 10:00 AM IST | https://www.kgisl.com/careers/ |
| Bosch Global Software Technologies | {day3_str} (in 3 days) | Associate AI / ML & Embedded Engineer | B.Tech (AI&DS, CSE, ECE), 2024/2025/2026, Strong Python, ML, C/C++ basics | ₹4.8 - ₹6.5 LPA | Bosch GSRC, CHIL SEZ, Keeranatham Road, Saravanampatti, Coimbatore - 641035 | https://www.google.com/maps/search/?api=1&query=Bosch+Global+Software+CHIL+SEZ+Saravanampatti+Coimbatore | 09:30 AM IST | https://www.bosch.in/careers/ |
| Cognizant Technology Solutions | {day5_str} (in 5 days) | Junior Data Analyst / Data Engineer Trainee | B.Tech / B.E (CSE, IT, AI&DS), Strong SQL, Python, Excel & Tableau | ₹4.2 - ₹5.0 LPA | Cognizant, KCT Tech Park, Saravanampatti, Coimbatore - 641049 | https://www.google.com/maps/search/?api=1&query=Cognizant+KCT+Tech+Park+Saravanampatti+Coimbatore | 09:00 AM IST | https://careers.cognizant.com/global/en |"""

    bangalore_table = f"""### Bangalore
| Company | Date | Role | Eligibility | Salary | Venue | Google Maps link | Reporting time | Source link |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Infosys BPM | {day2_str} (in 2 days) | IT Support / Systems Engineer Trainee | B.Tech / BCA / B.Sc (2024/2025), Windows Server, Networking, Cloud fundamentals | ₹3.5 - ₹4.5 LPA | Infosys BPM, Gate 4, Electronics City Phase 1, Hosur Road, Bangalore - 560100 | https://www.google.com/maps/search/?api=1&query=Infosys+BPM+Gate+4+Electronic+City+Bangalore | 10:00 AM IST | https://career.infosys.com/ |
| Tech Mahindra | {day4_str} (in 4 days) | Full Stack / MERN Developer Trainee | B.Tech (CSE, IT, AI&DS), MongoDB, Express, React, Node.js or Java Spring | ₹4.5 - ₹5.5 LPA | Tech Mahindra, Plot 45-47, KIADB Industrial Area, Electronic City Phase 2, Bangalore - 560100 | https://www.google.com/maps/search/?api=1&query=Tech+Mahindra+Electronic+City+Phase+2+Bangalore | 09:30 AM IST | https://careers.techmahindra.com/ |
| Wipro Limited | {day5_str} (in 5 days) | Junior Java Developer / Software Engineer | B.E / B.Tech (CSE, IT, AI&DS, ECE), Core Java, OOPS, Spring Boot basics | ₹4.5 - ₹6.0 LPA | Wipro Limited, Doddakannelli, Sarjapur Road, Bangalore - 560035 | https://www.google.com/maps/search/?api=1&query=Wipro+Limited+Doddakannelli+Sarjapur+Road+Bangalore | 09:00 AM IST | https://careers.wipro.com/careers-home/jobs |"""

    online_table = f"""## Online Assessments / Online Interviews
| Company | Role | Eligibility | Platform | Last date to apply | Test/Interview date & time | Test pattern | Salary | Registration link | Source link |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Tata Consultancy Services (TCS) | TCS NQT 2025/2026 - Digital & Prime (AI/ML & Software Engineer Track) | B.Tech (CSE, IT, AI&DS, ECE) 2025/2026, 60%+ throughout | TCS iON Proctored Portal | {day2_str} 11:59 PM | {day4_str}, 10:00 AM IST | Quantitative Aptitude, Logical Reasoning, Advanced Coding (Python/Java/C++) | ₹7.0 - ₹9.0 LPA | https://www.tcsion.com/hub/national-qualifier-test/ | https://www.tcs.com/careers |
| Wipro Limited | Project Engineer - Elite Drive (Java & Full Stack Cloud Track) | B.E / B.Tech / MCA (2024-2026), Min 60% or 6.0 CGPA | AMCAT / Mettl Virtual Platform | {day3_str} 06:00 PM | {day5_str}, 02:00 PM IST | Online Aptitude + 2 Coding Problems + English Communication Test | ₹4.0 - ₹6.5 LPA | https://careers.wipro.com/careers-home/jobs | https://careers.wipro.com |
| Accenture India | Associate Software Engineer & QA Testing Virtual Hiring | B.E / B.Tech (All Tech Branches), 0-1 Year Experience | HireVue / HackerRank Virtual Platform | {day2_str} 11:59 PM | {day4_str}, 11:00 AM IST | Cognitive Assessment + Technical MCQs (Cloud, OOPS) + Coding | ₹4.6 - ₹5.4 LPA | https://www.accenture.com/in-en/careers/jobsearch?jk=Associate%20Software%20Engineer | https://www.accenture.com/in-en/careers |
| Capgemini | Exceller Drive - Data Engineer & Web Development Track | B.Tech / MCA (2024/2025/2026), 60% throughout | CoCubes Assessment Engine | {day1_str} 09:00 PM | {day3_str}, 03:00 PM IST | Technical MCQs (Data Structures, SQL) + Hands-on Coding Challenge | ₹4.25 - ₹5.75 LPA | https://www.capgemini.com/in-en/careers/job-search/ | https://www.capgemini.com/in-en/careers/ |"""

    priority_section = f"""## Priority List
1. **TCS NQT (Digital / Prime - AI & Software Track)**: High-tier CTC (up to ₹9.0 LPA) matching IT & CSE specialization. Direct registration live at TCS iON!
2. **Cognizant Technology Solutions (Chennai Java/Full Stack Walk-in - {day2_str})**: Confirmed in-person walk-in drive scheduled in 2 days at OMR Sholinganallur. Immediate spot interview evaluation.
3. **Bosch Global Software Technologies (Coimbatore AI/ML & Embedded - {day3_str})**: Top brand for Core AI/ML and software engineering, located conveniently in Coimbatore."""

    if kind == 'online':
        return f'{online_table}\n\n---\n\n{priority_section}'

    walkin_parts = []
    if city:
        city_lower = city.lower()
        if city_lower == 'chennai':
            walkin_parts.append(chennai_table)
        elif city_lower == 'coimbatore':
            walkin_parts.append(coimbatore_table)
        elif city_lower == 'bangalore':
            walkin_parts.append(bangalore_table)
        else:
            walkin_parts.extend([chennai_table, coimbatore_table, bangalore_table])
    else:
        walkin_parts.extend([chennai_table, coimbatore_table, bangalore_table])

    walkin_section = '## Walk-in Interviews\n\n' + '\n\n'.join(walkin_parts)

    if kind == 'walkin' or city is not None:
        return f'{walkin_section}\n\n---\n\n{priority_section}'

    # Default / Daily Digest: Return all 13 opportunities (9 walk-ins + 4 online assessments)
    return f'{walkin_section}\n\n---\n\n{online_table}\n\n---\n\n{priority_section}'


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

    if dry_run or not has_anthropic_key():
        if not dry_run:
            logger.info("ANTHROPIC_API_KEY is not configured in .env. Serving sample/demo job listings.")
        else:
            logger.info("Running in dry-run mode (SAMPLE DATA, not real jobs)")
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
            f"Search directly across all official company career websites (Zoho, Cognizant, TCS, Infosys, Wipro, HCLTech, Bosch, Tech Mahindra, Accenture, Capgemini) and verified portals for live opportunities matching: '{query}'.\n"
            f"Target candidate: final-year B.Tech AI & Data Science fresher.\n"
            f"Target dates: today and the next 5 days ({today_str} onwards, advance travel window).\n"
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
            response = client.messages.create(
                model=model_name,
                max_tokens=8000,
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
        raise  # never send fake jobs; the caller shows a friendly error

    raise RuntimeError("Claude returned no text. Please try again.")


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
        is_heading = (
            line_clean.startswith(("#", "=="))
            or bool(re.match(r"(?i)^\**\s*section\s*\d", line_clean))
            or (line_clean.startswith("**") and line_clean.endswith("**") and len(line_clean) < 90)
        )
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
                if c in line_clean.lower() and is_heading:
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
