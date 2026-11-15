@echo off
title Walk-in Job Alert Telegram Bot
cd /d "%~dp0"
echo ===================================================
echo   Starting Walk-in Job Alert Telegram Bot
echo   (IT ^& CSE Cluster - 5-Day Advance Notice)
echo ===================================================
echo This bot will run independently of Antigravity.
echo Keep this window minimized to keep the bot active.
echo.
python bot.py
pause
