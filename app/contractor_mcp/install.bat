@echo off
REM Installation script for Contractor Portal MCP Server
REM Run this on your local Windows machine

echo ========================================
echo Installing Contractor Portal MCP Server
echo ========================================
echo.

REM Install MCP package
echo [1/3] Installing MCP SDK...
pip install mcp
if errorlevel 1 (
    echo ERROR: Failed to install MCP SDK
    pause
    exit /b 1
)

REM Update requirements.txt
echo.
echo [2/3] Updating requirements.txt...
pip freeze > requirements.txt

REM Display configuration instructions
echo.
echo [3/3] Configuration Required
echo.
echo ========================================
echo Next Steps:
echo ========================================
echo.
echo 1. Open Claude Desktop configuration:
echo    %APPDATA%\Claude\claude_desktop_config.json
echo.
echo 2. Add this configuration:
echo.
echo {
echo   "mcpServers": {
echo     "contractor-portal": {
echo       "command": "python",
echo       "args": [
echo         "r:\\Contractor App\\app\\mcp\\server.py"
echo       ],
echo       "env": {
echo         "DB_HOST": "127.0.0.1",
echo         "DB_USER": "root",
echo         "DB_PASSWORD": "Bimmer325!",
echo         "DB_NAME": "contractor_portal",
echo         "APP_BASE_URL": "http://localhost:8080"
echo       }
echo     }
echo   }
echo }
echo.
echo 3. Restart Claude Desktop completely
echo.
echo 4. Look for the plug icon in Claude Desktop to verify MCP is connected
echo.
echo ========================================
echo Installation complete!
echo ========================================
pause
