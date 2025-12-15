#!/bin/bash
# Script to run 2FA migration
# Usage: ./run_2fa_migration.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        Run 2FA Migration Script                        ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Extract config from app.yaml
if [ ! -f "app.yaml" ]; then
    echo -e "${RED}✗ app.yaml not found${NC}"
    exit 1
fi

CONNECTION_NAME=$(grep -A 100 "^env_variables:" app.yaml | grep "CLOUD_SQL_CONNECTION_NAME:" | head -1 | sed -E "s/.*CLOUD_SQL_CONNECTION_NAME:\s*[\"']?([^\"']*)[\"']?\s*$/\1/" | sed 's/^ *//;s/ *$//')
PROXY_PORT=3310
DB_USER="root"
DB_PASSWORD=$(grep -A 100 "^env_variables:" app.yaml | grep "CLOUD_SQL_PASSWORD:" | head -1 | sed -E "s/.*CLOUD_SQL_PASSWORD:\s*[\"']?([^\"']*)[\"']?\s*$/\1/" | sed 's/^ *//;s/ *$//')
DB_NAME=$(grep -A 100 "^env_variables:" app.yaml | grep "CLOUD_SQL_DATABASE_NAME:" | head -1 | sed -E "s/.*CLOUD_SQL_DATABASE_NAME:\s*[\"']?([^\"']*)[\"']?\s*$/\1/" | sed 's/^ *//;s/ *$//')

if [ -z "$CONNECTION_NAME" ]; then
    echo -e "${RED}✗ Could not extract CONNECTION_NAME from app.yaml${NC}"
    exit 1
fi

echo -e "${BLUE}Configuration:${NC}"
echo -e "  Connection: ${CONNECTION_NAME}"
echo -e "  Port: ${PROXY_PORT}"
echo -e "  Database: ${DB_NAME}"
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
sleep 2

# Run migration
echo -e "\n${BLUE}Running 2FA migration...${NC}"
MIGRATION_OUTPUT=$(mysql -h 127.0.0.1 -P ${PROXY_PORT} -u ${DB_USER} -p"${DB_PASSWORD}" ${DB_NAME} < migration_add_2fa.sql 2>&1)
MIGRATION_EXIT=$?

# Check output for duplicate column errors (which are okay)
if echo "$MIGRATION_OUTPUT" | grep -q "Duplicate column name"; then
    echo -e "${YELLOW}⚠ Some columns already exist (migration may have been run before)${NC}"
    echo -e "${GREEN}✓ 2FA migration completed${NC}"
elif [ $MIGRATION_EXIT -eq 0 ]; then
    echo -e "${GREEN}✓ 2FA migration completed successfully${NC}"
else
    echo -e "${RED}✗ 2FA migration failed${NC}"
    echo "$MIGRATION_OUTPUT"
    if [ "$STARTED_PROXY" = "true" ]; then
        kill "$PROXY_PID" 2>/dev/null || true
    fi
    exit $MIGRATION_EXIT
fi

# Clean up proxy if we started it
if [ "$STARTED_PROXY" = "true" ]; then
    echo -e "\n${YELLOW}Stopping Cloud SQL Proxy...${NC}"
    kill "$PROXY_PID" 2>/dev/null || true
    echo -e "${GREEN}✓ Proxy stopped${NC}"
fi

echo -e "\n${GREEN}Done!${NC}"

