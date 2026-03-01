#!/bin/bash
# Helper script to run WebSocket client

set -e

echo "=== WebSocket Chat Client ==="
echo

if [ -z "$1" ]; then
    echo "Creating new conversation..."
    # Login to get token
    echo "Login with your credentials (or press Enter for default: admin@example.com / password)"
    read -p "Email [admin@example.com]: " email
    email=${email:-admin@example.com}
    read -sp "Password [password]: " password
    echo
    password=${password:-password}
    # Get token
    TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/login/access-token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=${email}&password=${password}" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
    
    if [ -z "$TOKEN" ]; then
        echo "Error: Failed to get token. Check credentials and server is running."
        exit 1
    fi
    # Start new conversation
    CONVERSATION_ID=$(curl -s -X POST "http://localhost:8000/api/v1/chat/start" \
        -H "Authorization: Bearer ${TOKEN}" | python3 -c "import sys, json; print(json.load(sys.stdin)['conversation']['id'])" 2>/dev/null)
    if [ -z "$CONVERSATION_ID" ]; then
        echo "Error: Failed to create conversation"
        exit 1
    fi
    echo "Created conversation: ${CONVERSATION_ID}"
else
    CONVERSATION_ID=$1
    # Login to get token
    read -p "Email: " email
    read -sp "Password: " password
    echo
    TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/login/access-token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=${email}&password=${password}" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)
    
    if [ -z "$TOKEN" ]; then
        echo "Error: Failed to get token"
        exit 1
    fi
fi

echo
echo "Connecting to WebSocket..."
echo

# Check if websockets is installed
if ! python3 -c "import websockets" 2>/dev/null; then
    echo "Installing websockets..."
    uv add websockets
fi

# Run the client
python3 websocket_client.py "${CONVERSATION_ID}" "${TOKEN}"
