@echo off
REM Windows batch script to deploy to remote server
REM Run this from your local machine: deploy-remote.bat

echo ======================================
echo Deploying to contractor portal server
echo ======================================
echo.

ssh bubbles@contractorportal "cd /opt/contractor-portal && git pull origin feature/passwordless-sso && bash deploy.sh"

echo.
echo ======================================
echo Deployment complete!
echo ======================================
pause
