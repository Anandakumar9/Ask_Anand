@echo off
REM StudyPulse API Endpoint Tester - Windows Batch Script
REM Runs comprehensive tests on both localhost and Railway production

echo.
echo ========================================
echo StudyPulse API Endpoint Tester
echo ========================================
echo.
echo This script will test all key API endpoints on:
echo - Localhost: http://localhost:8001
echo - Production: https://askanand-simba.up.railway.app
echo.
echo Press any key to start testing...
pause > nul

echo.
echo Installing required Python packages...
python -m pip install requests --quiet

echo.
echo Running API tests...
echo.

python test_all_endpoints.py

echo.
echo ========================================
echo Test Complete!
echo ========================================
echo.
echo Check the output above for detailed results.
echo For more information, see: STUDYPULSE_API_TEST_REPORT.md
echo.
pause
