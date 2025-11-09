#!/bin/bash
# Installation script for Contractor Portal MCP Server (Linux/macOS)

echo "========================================"
echo "Installing Contractor Portal MCP Server"
echo "========================================"
echo ""

# Install MCP package
echo "[1/3] Installing MCP SDK..."
pip3 install mcp
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install MCP SDK"
    exit 1
fi

# Update requirements.txt
echo ""
echo "[2/3] Updating requirements.txt..."
pip3 freeze > requirements.txt

# Display configuration instructions
echo ""
echo "[3/3] Configuration Required"
echo ""
echo "========================================"
echo "Next Steps:"
echo "========================================"
echo ""
echo "1. Open Claude Desktop configuration:"
echo "   ~/Library/Application Support/Claude/claude_desktop_config.json"
echo ""
echo "2. Add this configuration:"
echo ""
cat <<'EOF'
{
  "mcpServers": {
    "contractor-portal": {
      "command": "python3",
      "args": [
        "/opt/contractor-portal/mcp/server.py"
      ],
      "env": {
        "DB_HOST": "127.0.0.1",
        "DB_USER": "contractor",
        "DB_PASSWORD": "Bimmer325!",
        "DB_NAME": "contractor_portal",
        "APP_BASE_URL": "http://localhost:8080"
      }
    }
  }
}
EOF
echo ""
echo "3. Restart Claude Desktop completely"
echo ""
echo "4. Look for the plug icon in Claude Desktop to verify MCP is connected"
echo ""
echo "========================================"
echo "Installation complete!"
echo "========================================"
