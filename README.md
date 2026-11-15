# 🤖 walkin-job-alert-agent

An intelligent job alert assistant designed for **final-year B.Tech AI & Data Science freshers** (and 0-1 year tech job seekers). It searches for upcoming walk-in interviews and online assessments in **Chennai, Coimbatore, and Bangalore** scheduled strictly for today or within the next 2 days, so you can reach the company 1-2 days ahead.

The project contains two parts:
1. **Daily Job Digest (`agent.py`)**: An automated agent scheduled to run at 8:00 AM IST every morning via GitHub Actions.
2. **Interactive Telegram Bot (`bot.py`)**: A bot that replies on-demand to commands (`/today`, `/chennai`, `/coimbatore`, `/bangalore`, `/online`, `/walkin`) and custom search queries using Anthropic Claude with web search.

---

## 📋 Features

- **Model & Web Search**: Uses the Anthropic Python SDK with model `claude-sonnet-5-5` and the `web_search_20250305` tool (`max_uses 20`).
- **pause_turn Handling**: Fully supports multi-step server tool loops by continuing turns when `stop_reason == "pause_turn"`.
- **IST Time Injection**: Calculates current date and date + 2 days in Indian Standard Time (`Asia/Kolkata`) and feeds them into the system prompt.
- **Strict Verification**: Filters out scam fees, prioritizes official career pages and top job platforms (Naukri, LinkedIn, Indeed, Foundit).
- **Telegram Card Formatting**: Converts raw markdown tables into card-style messages with emojis and labels, cleanly split under 4,000 characters.
- **Security**: Only responds to your personal `TELEGRAM_CHAT_ID`. Silently ignores any message from unauthorized users. Never logs API keys or tokens.
- **Smart 30-Minute Cache**: Caches identical queries for 30 minutes to conserve Claude API credits.
- **Daily Rate Limiting**: Caps searches at 20 queries/day to prevent accidental credit exhaustion.
- **Polling & Webhook Clearing**: Uses standard `requests` long polling (`getUpdates`, timeout 30s) and calls `deleteWebhook` on startup.

---

## 🛠️ Step 1: Getting Telegram Credentials

### 1. Create your Telegram Bot with @BotFather
1. Open the Telegram app on your phone or desktop.
2. Search for the verified **@BotFather** bot (with a blue verification checkmark) or visit [t.me/BotFather](https://t.me/BotFather).
3. Send the command:
   ```text
   /newbot
   ```
4. Enter a name for your bot (e.g. `Guhan Job Alert Bot`).
5. Enter a unique username ending in `bot` (e.g. `guhan_job_alert_bot`).
6. BotFather will reply with your **HTTP API Token** (e.g., `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`). Copy this token.

### 2. Get Your Personal Chat ID
1. Search for **@userinfobot** on Telegram or open [t.me/userinfobot](https://t.me/userinfobot).
2. Tap **Start** or send `/start`.
3. The bot will reply with your profile info. Copy your numerical **Id** (e.g. `1234567890`).
4. **Important**: Open your new bot in Telegram and tap **Start** once so it has permission to send you messages.

---

## ⚙️ Step 2: Environment Setup

Create a `.env` file in the project directory (or use your existing `.env`):
```ini
ANTHROPIC_API_KEY=sk-ant-api03-...
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
TELEGRAM_CHAT_ID=1234567890
```

Install the required packages:
```bash
pip install -r requirements.txt
```

---

## 🧪 Step 3: Testing with `--dry-run`

Before starting live searches or setting up scheduled runs, you can test everything offline without consuming API credits or sending Telegram messages:

### 1. Test Daily Digest Agent
```bash
python agent.py --dry-run
```
This performs a mock search, formats the job opportunities into card-style messages, verifies the message size, and prints the result to your terminal.

### 2. Test Interactive Bot
```bash
# Test default command suite (/today, /chennai, /online, custom query)
python bot.py --dry-run

# Test with a specific custom query
python bot.py --dry-run "AI jobs in Chennai tomorrow"
```
This tests card conversion, chunk size (< 4,000 characters), 30-minute caching, and 20-search daily rate-limiting.

---

## 🚀 Step 4: Running `bot.py` Locally

To start the bot and have it reply to your Telegram messages:
```bash
python bot.py
```
Leave this terminal window open. You can now send messages to your bot on Telegram:
- `/start` or `/help` — View available commands.
- `/today` — Walk-ins and online tests for today and next 2 days across all 3 cities.
- `/chennai` — Chennai openings only.
- `/coimbatore` — Coimbatore openings only.
- `/bangalore` — Bangalore openings only.
- `/online` — Online tests and virtual drives only.
- `/walkin` — In-person walk-in drives only.
- Any regular text like `"AI fresher walkin Bangalore"` — Claude will search the web and answer.

---

## 🌐 Step 5: Keeping `bot.py` Running 24/7

To receive on-demand replies at any time without keeping your personal computer turned on, deploy `bot.py` using either Render or Railway.

### Method A: Deploy Free on Render (Recommended)
1. Go to [render.com](https://render.com) and sign in with your GitHub account.
2. Click **New +** → **Blueprint** and select this repository. Render will use the included `render.yaml` to create a Background Worker that runs `python bot.py`.
3. Enter the values for `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` when prompted. Enter `ANTHROPIC_API_KEY` as well to enable live job searches.
4. Create the Blueprint. Render will install `requirements.txt` and keep the bot worker running.

This bot uses Telegram long polling and must run as a persistent background worker. It is not compatible with Vercel's serverless Python functions; deploying this repository on Vercel will fail because it has no serverless Python entry point.

---

### Method B: Deploy on Railway
1. Go to [railway.app](https://railway.app) and sign in with GitHub.
2. Click **New Project** → **Deploy from GitHub repo**.
3. Select this repository.
4. Click on the created service card and open the **Variables** tab.
5. Add the 3 environment variables:
   - `ANTHROPIC_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
6. Go to the **Settings** tab:
   - Under **Deploy**, set the **Custom Start Command** to:
     ```text
     python bot.py
     ```
7. Railway will deploy and keep `bot.py` active around the clock.

---

### Method C: Keep Running on Your Local PC
If you prefer running it on your own computer:
- **Windows**: Use Task Scheduler or keep a PowerShell terminal open running `python bot.py`.
- **Background process (PM2)**:
  ```powershell
  npm install -g pm2
  pm2 start bot.py --name "job-bot" --interpreter python
  pm2 save
  ```

---

## ⏰ Step 6: Automated 8:00 AM Daily Digest (GitHub Actions)

The scheduled morning digest runs via `.github/workflows/jobs.yml`. It triggers at **8:00 AM IST (2:30 AM UTC)** every morning automatically without needing your PC or bot server to be running.

### Setting GitHub Secrets:
1. Open your repository on GitHub.
2. Navigate to **Settings** → **Secrets and variables** → **Actions**.
3. Click **New repository secret** and add each of these:
   - Name: `ANTHROPIC_API_KEY` | Value: *Your Anthropic API key*
   - Name: `TELEGRAM_BOT_TOKEN` | Value: *Your Telegram bot token*
   - Name: `TELEGRAM_CHAT_ID` | Value: *Your numerical chat ID*
4. Test the workflow:
   - Go to the **Actions** tab on GitHub.
   - Click **Daily Walk-in & Job Alert Digest** on the left.
   - Click **Run workflow** → **Run workflow**.
   - Your bot will send the morning digest straight to your Telegram!

---

## 📂 Project Architecture

```
walkin-job-alert-agent/
├── job_search.py              # Shared engine: Anthropic SDK, web_search, IST dates, card formatter, sender
├── agent.py                   # Automated daily 8 AM digest script
├── bot.py                     # Long-polling interactive Telegram bot (requests only)
├── requirements.txt           # anthropic, requests, python-dotenv
├── .env.example               # Template for configuration
├── .gitignore                 # Excludes .env and temporary state files
├── .github/
│   └── workflows/
│       └── jobs.yml           # Daily 8:00 AM IST GitHub Actions workflow
└── README.md                  # Complete documentation and setup guide
```
