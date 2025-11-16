@echo off
REM Quick update script for snow-contractor.com
echo ================================
echo Contractor Portal Quick Update
echo ================================
echo.
echo Connecting to VPS and pulling latest changes...
echo.

ssh root@72.61.0.186 "cd /opt/contractor-portal && git pull origin beta && systemctl restart contractor-portal && echo '=== UPDATE COMPLETE ===' && systemctl status contractor-portal --no-pager -l"

echo.
echo Update complete! Check the status above.
echo Application should be live at: https://snow-contractor.com
pause
