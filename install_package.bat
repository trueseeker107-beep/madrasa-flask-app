@echo off
REM === Adjust this path if your folder name changes ===
cd /d D:\ZAIN\Madrassa Veluthapoyya\rabee 2025\my flask app
call venv\Scripts\activate.bat

echo.
echo ===========================================
echo   Install packages into this project's venv
echo ===========================================
echo.

REM If packages are passed as arguments, use them; else ask.
IF "%~1"=="" (
  set /p pkgs="Enter package name(s) (e.g. flask pandas requests): "
) ELSE (
  set pkgs=%*
)

echo.
echo Installing: %pkgs%
pip install %pkgs%
IF ERRORLEVEL 1 (
  echo.
  echo Installation failed. Check the package name(s) or internet connection.
  pause
  exit /b 1
)

echo.
echo Updating requirements.txt ...
pip freeze > requirements.txt

echo.
echo Done! Installed [%pkgs%] and updated requirements.txt
pause
