@echo off
echo Stopping Job Alert Telegram Bot...
taskkill /F /FI "COMMANDLINE eq *bot.py*" /IM python.exe 2>nul
if %errorlevel% neq 0 (
    echo No separate bot process found or process already stopped.
) else (
    echo Bot stopped successfully.
)
pause
