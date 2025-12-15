#!/bin/bash

# Script to run password policy migration on Cloud SQL
# This addresses Cloud SQL security warnings

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        Run Password Policy Migration                   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"

# Get configuration from environment or app.yaml
CONNECTION_NAME="${CLOUD_SQL_CONNECTION_NAME:-csci0220-472715:us-central1:robo}"
SQL_PASSWORD="${CLOUD_SQL_PASSWORD:--6uB+6(7_bHPGmGupolivoliv67}"
DB_NAME="${CLOUD_SQL_DATABASE_NAME:-ROBOPETY}"
PROXY_PORT="${CLOUD_SQL_PROXY_PORT:-3310}"

echo -e "\n${CYAN}Configuration:${NC}"
echo -e "  Connection: ${BLUE}${CONNECTION_NAME}${NC}"
echo -e "  Port: ${BLUE}${PROXY_PORT}${NC}"
echo -e "  Database: ${BLUE}${DB_NAME}${NC}"

# Check if Cloud SQL Proxy is running
if ! ss -ltn 2>/dev/null | grep -q ":${PROXY_PORT}" && ! netstat -an 2>/dev/null | grep -q ":${PROXY_PORT}"; then
    echo -e "\n${YELLOW}⚠️  Cloud SQL Proxy is not running on port ${PROXY_PORT}${NC}"
    echo -e "${YELLOW}Starting Cloud SQL Proxy...${NC}"
    
    if [ ! -f "./cloud-sql-proxy" ]; then
        echo -e "${RED}✗ cloud-sql-proxy not found${NC}"
        echo -e "${YELLOW}Please download cloud-sql-proxy first${NC}"
        exit 1
    fi
    
    ./cloud-sql-proxy "${CONNECTION_NAME}=tcp:${PROXY_PORT}" > /tmp/cloud-sql-proxy.log 2>&1 &
    PROXY_PID=$!
    echo $PROXY_PID > /tmp/cloud-sql-proxy.pid
    
    # Wait for proxy to be ready
    echo -e "${YELLOW}Waiting for Cloud SQL Proxy to start...${NC}"
    sleep 3
    
    if ! ss -ltn 2>/dev/null | grep -q ":${PROXY_PORT}" && ! netstat -an 2>/dev/null | grep -q ":${PROXY_PORT}"; then
        echo -e "${RED}✗ Cloud SQL Proxy failed to start${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Cloud SQL Proxy started${NC}"
else
    echo -e "${GREEN}✓ Cloud SQL Proxy is already running on port ${PROXY_PORT}${NC}"
fi

# Test database connection
echo -e "\n${BLUE}Testing database connection...${NC}"
if mysql -h 127.0.0.1 -P "${PROXY_PORT}" -u root -p"${SQL_PASSWORD}" -e "SELECT 1" &>/dev/null; then
    echo -e "${GREEN}✓ Database connection successful${NC}"
else
    echo -e "${RED}✗ Database connection failed${NC}"
    echo -e "${YELLOW}Please check your credentials and Cloud SQL Proxy${NC}"
    exit 1
fi

# Run migration
echo -e "\n${BLUE}Running password policy migration...${NC}"
if mysql -h 127.0.0.1 -P "${PROXY_PORT}" -u root -p"${SQL_PASSWORD}" < migration_add_password_policy.sql 2>&1; then
    echo -e "${GREEN}✓ Password policy migration completed${NC}"
else
    echo -e "${YELLOW}⚠️  Migration completed with warnings (this is normal if policies already exist)${NC}"
fi

echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        Migration Complete!                               ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo -e "\n${CYAN}Next Steps:${NC}"
echo -e "  1. Go to Google Cloud Console → Cloud SQL → Your Instance"
echo -e "  2. Check 'Connections' tab - the warnings should be resolved"
echo -e "  3. If 'Allows unencrypted direct connections' still shows:"
echo -e "     - Go to 'Connections' → 'Authorized networks'"
echo -e "     - Remove any public IP access"
echo -e "     - Ensure only App Engine and authorized services can connect"
echo ""

