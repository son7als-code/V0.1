@echo off
setlocal
where py >nul 2>nul || (echo Python not found. Install Python 3.11 x64 first.&pause&exit /b 1)
py -3.11 -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
where ffmpeg >nul 2>nul || echo WARNING: FFmpeg not found in PATH. Install FFmpeg and reopen this terminal.
echo.
echo Installation finished. Run run_windows.bat
pause
