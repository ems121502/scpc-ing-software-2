@echo off
cd /d "%~dp0"
call .venv\Scripts\activate
start "" cmd /c "timeout /t 3 >nul & start http://127.0.0.1:8000/"
python manage.py runserver