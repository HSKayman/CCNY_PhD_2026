#!/bin/bash

# Script to run the admin response migration for security events
# This adds admin_response and admin_responded_at columns to the security_events table

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Admin Response Migration for Security Events         ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Extract config from app.yaml (like run_2fa_migration.sh)
if [ ! -f "app.yaml" ]; then
    echo -e "${RED}✗ app.yaml not found${NC}"
    exit 1
fi

CONNECTION_NAME=$(grep -A 100 "^env_variables:" app.yaml | grep "CLOUD_SQL_CONNECTION_NAME:" | head -1 | sed -E "s/.*CLOUD_SQL_CONNECTION_NAME:\s*[\"']?([^\"']*)[\"']?\s*$/\1/" | sed 's/^ *//;s/ *$//')
PORT="${CLOUD_SQL_PORT:-3310}"
DB_NAME=$(grep -A 100 "^env_variables:" app.yaml | grep "CLOUD_SQL_DATABASE_NAME:" | head -1 | sed -E "s/.*CLOUD_SQL_DATABASE_NAME:\s*[\"']?([^\"']*)[\"']?\s*$/\1/" | sed 's/^ *//;s/ *$//')
DB_USER="${DB_USER:-root}"
DB_PASSWORD=$(grep -A 100 "^env_variables:" app.yaml | grep "CLOUD_SQL_PASSWORD:" | head -1 | sed -E "s/.*CLOUD_SQL_PASSWORD:\s*[\"']?([^\"']*)[\"']?\s*$/\1/" | sed 's/^ *//;s/ *$//')

if [ -z "$CONNECTION_NAME" ]; then
    echo -e "${RED}✗ Could not extract CONNECTION_NAME from app.yaml${NC}"
    exit 1
fi

if [ -z "$DB_PASSWORD" ]; then
    echo -e "${RED}✗ Could not extract CLOUD_SQL_PASSWORD from app.yaml${NC}"
    exit 1
fi

echo "Configuration:"
echo "  Connection: $CONNECTION_NAME"
echo "  Port: $PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""

# Check if Cloud SQL Proxy is running
if ss -ltn 2>/dev/null | grep -q ":${PORT}" || netstat -tln 2>/dev/null | grep -q ":${PORT}"; then
    echo -e "${GREEN}✓ Cloud SQL Proxy is already running on port $PORT${NC}"
    STARTED_PROXY=false
    TRAP_PID=""
else
    echo -e "${YELLOW}⚠ Cloud SQL Proxy is not running on port $PORT${NC}"
    echo "Starting Cloud SQL Proxy..."
    
    if [ ! -x "./cloud-sql-proxy" ]; then
        echo -e "${YELLOW}cloud-sql-proxy not found in current directory, trying system command...${NC}"
        # Try to start the proxy in the background
        cloud-sql-proxy "${CONNECTION_NAME}" --port=$PORT > /tmp/cloud-sql-proxy.log 2>&1 &
        PROXY_PID=$!
    else
        ./cloud-sql-proxy "${CONNECTION_NAME}" --port=$PORT > /tmp/cloud-sql-proxy.log 2>&1 &
        PROXY_PID=$!
    fi
    
    # Wait for proxy to start
    echo -e "${YELLOW}Waiting for proxy to start...${NC}"
    for i in {1..15}; do
        if ss -ltn 2>/dev/null | grep -q ":${PORT}" || netstat -tln 2>/dev/null | grep -q ":${PORT}"; then
            echo -e "${GREEN}✓ Cloud SQL Proxy started (PID: $PROXY_PID)${NC}"
            STARTED_PROXY=true
            TRAP_PID=$PROXY_PID
            break
        fi
        sleep 1
    done
    
    if [ "$STARTED_PROXY" != "true" ]; then
        echo -e "${RED}Error: Could not start Cloud SQL Proxy${NC}"
        echo "Please start it manually:"
        echo "  cloud-sql-proxy ${CONNECTION_NAME} --port=$PORT"
        exit 1
    fi
fi

# Test database connection
echo "Testing database connection..."
if mysql -h 127.0.0.1 -P $PORT -u "$DB_USER" -p"$DB_PASSWORD" -e "USE $DB_NAME;" 2>/dev/null; then
    echo -e "${GREEN}✓ Database connection successful${NC}"
else
    echo -e "${RED}Error: Database connection failed${NC}"
    if [ -n "$TRAP_PID" ]; then
        kill $TRAP_PID 2>/dev/null || true
    fi
    exit 1
fi

# Run migration
echo ""
echo "Running migration..."
mysql -h 127.0.0.1 -P $PORT -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < migration_add_admin_response_to_security_events.sql 2>&1 | grep -v "Using a password"
EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Migration completed successfully${NC}"
else
    echo -e "${YELLOW}⚠ Migration script exited with code $EXIT_CODE, checking if columns exist...${NC}"
    # Check if columns already exist (which is fine)
    if mysql -h 127.0.0.1 -P $PORT -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "DESCRIBE security_events;" 2>/dev/null | grep -q "admin_response"; then
        echo -e "${GREEN}✓ Columns already exist (migration was successful)${NC}"
    else
        echo -e "${RED}Error: Migration failed and columns do not exist${NC}"
        if [ "$STARTED_PROXY" = "true" ] && [ -n "$TRAP_PID" ]; then
            kill $TRAP_PID 2>/dev/null || true
        fi
        exit 1
    fi
fi

# Verify migration
echo ""
echo "Verifying migration..."
if mysql -h 127.0.0.1 -P $PORT -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "DESCRIBE security_events;" 2>/dev/null | grep -q "admin_response"; then
    echo -e "${GREEN}✓ admin_response column exists${NC}"
else
    echo -e "${RED}Error: admin_response column not found${NC}"
    if [ -n "$TRAP_PID" ]; then
        kill $TRAP_PID 2>/dev/null || true
    fi
    exit 1
fi

if mysql -h 127.0.0.1 -P $PORT -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "DESCRIBE security_events;" 2>/dev/null | grep -q "admin_responded_at"; then
    echo -e "${GREEN}✓ admin_responded_at column exists${NC}"
else
    echo -e "${RED}Error: admin_responded_at column not found${NC}"
    if [ -n "$TRAP_PID" ]; then
        kill $TRAP_PID 2>/dev/null || true
    fi
    exit 1
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Migration completed successfully!                     ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"

# Cleanup: Kill proxy if we started it
if [ "$STARTED_PROXY" = "true" ] && [ -n "$TRAP_PID" ]; then
    echo ""
    echo "Stopping Cloud SQL Proxy..."
    kill $TRAP_PID 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✓ Done${NC}"
fi

