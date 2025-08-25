@echo off
cd /d D:\ZAIN\Madrassa Veluthapoyya\rabee 2025\my flask app
call venv\Scripts\activate.bat

echo.
echo =========================================
echo   Starting Flask in DEBUG (Auto-Reload)
echo =========================================
echo.

:: Get local IPv4 (skips 127.* and 169.254.*)
for /f %%a in ('powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 | ?{ $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } | Select-Object -First 1 -ExpandProperty IPAddress)"') do set IP=%%a

set FLASK_APP=app.py
set FLASK_ENV=development

set URL_PHONE=http://%IP%:5000
set URL_LAPTOP=http://127.0.0.1:5000

echo Your app will be available at:
echo   Laptop: %URL_LAPTOP%
echo   Phone : %URL_PHONE%

:: Copy phone link to clipboard
echo %URL_PHONE% | clip
echo (Phone link has been copied to clipboard)

echo.
flask run --host=0.0.0.0 --port=5000

pause
