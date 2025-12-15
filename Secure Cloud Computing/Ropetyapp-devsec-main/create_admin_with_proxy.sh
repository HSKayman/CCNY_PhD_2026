#!/bin/bash
# Script to create admin user - automatically starts Cloud SQL Proxy
# Usage: ./create_admin_with_proxy.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        Create Admin User Script                        ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Extract config from app.yaml
if [ ! -f "app.yaml" ]; then
    echo -e "${RED}✗ app.yaml not found${NC}"
    exit 1
fi

CONNECTION_NAME=$(grep -A 100 "^env_variables:" app.yaml | grep "CLOUD_SQL_CONNECTION_NAME:" | head -1 | sed -E "s/.*CLOUD_SQL_CONNECTION_NAME:\s*[\"']?([^\"']*)[\"']?\s*$/\1/" | sed 's/^ *//;s/ *$//')
PROXY_PORT=3310

if [ -z "$CONNECTION_NAME" ]; then
    echo -e "${RED}✗ Could not extract CONNECTION_NAME from app.yaml${NC}"
    exit 1
fi

echo -e "${BLUE}Configuration:${NC}"
echo -e "  Connection: ${CONNECTION_NAME}"
echo -e "  Port: ${PROXY_PORT}"
echo ""

# Check if proxy is already running
if ss -ltn 2>/dev/null | grep -q ":${PROXY_PORT}" || netstat -tln 2>/dev/null | grep -q ":${PROXY_PORT}"; then
    echo -e "${GREEN}✓ Cloud SQL Proxy is already running on port ${PROXY_PORT}${NC}"
    STARTED_PROXY=false
else
    echo -e "${YELLOW}Starting Cloud SQL Proxy...${NC}"
    
    if [ ! -x "./cloud-sql-proxy" ]; then
        echo -e "${RED}✗ cloud-sql-proxy not found in current directory${NC}"
        echo -e "${YELLOW}Please download it or run from the project root${NC}"
        exit 1
    fi
    
    # Start proxy in background
    ./cloud-sql-proxy "${CONNECTION_NAME}" --port ${PROXY_PORT} > /tmp/cloud-sql-proxy.log 2>&1 &
    PROXY_PID=$!
    
    # Wait for proxy to start
    echo -e "${YELLOW}Waiting for proxy to start...${NC}"
    for i in {1..15}; do
        if ss -ltn 2>/dev/null | grep -q ":${PROXY_PORT}" || netstat -tln 2>/dev/null | grep -q ":${PROXY_PORT}"; then
            echo -e "${GREEN}✓ Cloud SQL Proxy started (PID: $PROXY_PID)${NC}"
            STARTED_PROXY=true
            break
        fi
        sleep 1
    done
    
    if [ "${STARTED_PROXY:-false}" != "true" ]; then
        echo -e "${RED}✗ Failed to start Cloud SQL Proxy${NC}"
        cat /tmp/cloud-sql-proxy.log 2>/dev/null || true
        kill "$PROXY_PID" 2>/dev/null || true
        exit 1
    fi
fi

# Test connection
echo -e "${BLUE}Testing database connection...${NC}"
sleep 2  # Give it a moment to stabilize

# Run the Python script
echo -e "\n${BLUE}Creating admin user...${NC}"
if python3 create_admin_quick.py; then
    echo -e "\n${GREEN}✓ Admin user creation completed${NC}"
else
    echo -e "\n${RED}✗ Admin user creation failed${NC}"
    EXIT_CODE=$?
    if [ "$STARTED_PROXY" = "true" ]; then
        kill "$PROXY_PID" 2>/dev/null || true
    fi
    exit $EXIT_CODE
fi

# Clean up proxy if we started it
if [ "$STARTED_PROXY" = "true" ]; then
    echo -e "\n${YELLOW}Stopping Cloud SQL Proxy...${NC}"
    kill "$PROXY_PID" 2>/dev/null || true
    echo -e "${GREEN}✓ Proxy stopped${NC}"
fi

echo -e "\n${GREEN}Done!${NC}"








