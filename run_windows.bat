@echo off
setlocal
if not exist .venv\Scripts\python.exe (
  echo Chua cai VietDub. Hay chay install_windows.bat truoc.
  pause
  exit /b 1
)
call .venv\Scripts\activate
python run.py
pause
