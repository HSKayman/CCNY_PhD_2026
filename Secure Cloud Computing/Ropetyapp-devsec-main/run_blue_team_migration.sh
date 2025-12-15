#!/bin/bash

# Blue Team Migration Script
# This script adds the blue_team role and creates the security_events table

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "╔══════════════════════════════════════════════════════════╗"
echo "║        Run Blue Team Migration Script                   ║"
echo "╚══════════════════════════════════════════════════════════╝"

# Configuration
DB_CONNECTION_NAME="${CLOUD_SQL_CONNECTION_NAME:-csci0220-472715:us-central1:robo}"
DB_USER="${CLOUD_SQL_USERNAME:-root}"
DB_PASSWORD="${CLOUD_SQL_PASSWORD}"
DB_NAME="${CLOUD_SQL_DATABASE_NAME:-ROBOPETY}"
PROXY_PORT="${CLOUD_SQL_PROXY_PORT:-3310}"

echo ""
echo "Configuration:"
echo "  Connection: $DB_CONNECTION_NAME"
echo "  Port: $PROXY_PORT"
echo "  Database: $DB_NAME"
echo ""

# Check if Cloud SQL Proxy is running
if ! lsof -Pi :$PROXY_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠ Cloud SQL Proxy is not running on port $PROXY_PORT${NC}"
    echo "Starting Cloud SQL Proxy..."
    
    # Try to start the proxy in the background
    if command -v cloud-sql-proxy >/dev/null 2>&1; then
        cloud-sql-proxy $DB_CONNECTION_NAME --port=$PROXY_PORT > /dev/null 2>&1 &
        PROXY_PID=$!
        echo "Cloud SQL Proxy started (PID: $PROXY_PID)"
        sleep 3
        
        # Cleanup function
        cleanup() {
            if [ ! -z "$PROXY_PID" ]; then
                kill $PROXY_PID 2>/dev/null || true
            fi
        }
        trap cleanup EXIT
    else
        echo -e "${RED}✗ cloud-sql-proxy not found. Please start it manually:${NC}"
        echo "  cloud-sql-proxy $DB_CONNECTION_NAME --port=$PROXY_PORT"
        echo ""
        echo "Then run this script again."
        exit 1
    fi
else
    echo -e "${GREEN}✓ Cloud SQL Proxy is already running on port $PROXY_PORT${NC}"
fi

# Test database connection
echo ""
echo "Testing database connection..."
if mysql -h 127.0.0.1 -P $PROXY_PORT -u "$DB_USER" -p"$DB_PASSWORD" -e "USE $DB_NAME;" 2>/dev/null; then
    echo -e "${GREEN}✓ Database connection successful${NC}"
else
    echo -e "${RED}✗ Database connection failed${NC}"
    echo "Please check your credentials and ensure Cloud SQL Proxy is running."
    exit 1
fi

# Run migration
echo ""
echo "Running Blue Team migration..."
echo ""

# Run the migration SQL file
mysql -h 127.0.0.1 -P $PROXY_PORT -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < migration_add_blue_team_role.sql 2>&1 | grep -v "Using a password" || {
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✓ Migration completed successfully${NC}"
    else
        # Check if it's just a "column already exists" error (idempotent)
        if mysql -h 127.0.0.1 -P $PROXY_PORT -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "SHOW COLUMNS FROM users LIKE 'role';" 2>/dev/null | grep -q "role"; then
            echo -e "${YELLOW}⚠ Migration may have already been run (role column exists)${NC}"
            echo "Checking if blue_team role is available..."
            if mysql -h 127.0.0.1 -P $PROXY_PORT -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "SHOW COLUMNS FROM users WHERE Field='role' AND Type LIKE '%blue_team%';" 2>/dev/null | grep -q "blue_team"; then
                echo -e "${GREEN}✓ Blue team role already exists${NC}"
            else
                echo -e "${YELLOW}⚠ Role column exists but may need to be updated to include blue_team${NC}"
                echo "Attempting to modify role column..."
                mysql -h 127.0.0.1 -P $PROXY_PORT -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" <<EOF 2>&1 | grep -v "Using a password" || true
USE $DB_NAME;
ALTER TABLE users MODIFY COLUMN role ENUM('user', 'admin', 'blue_team') NOT NULL DEFAULT 'user';
EOF
                echo -e "${GREEN}✓ Role column updated${NC}"
            fi
        else
            echo -e "${RED}✗ Migration failed${NC}"
            exit 1
        fi
    fi
}

# Verify migration
echo ""
echo "Verifying migration..."
if mysql -h 127.0.0.1 -P $PROXY_PORT -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "SHOW TABLES LIKE 'security_events';" 2>/dev/null | grep -q "security_events"; then
    echo -e "${GREEN}✓ security_events table created${NC}"
else
    echo -e "${YELLOW}⚠ security_events table may already exist or creation failed${NC}"
fi

if mysql -h 127.0.0.1 -P $PROXY_PORT -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "SHOW COLUMNS FROM users WHERE Field='role' AND Type LIKE '%blue_team%';" 2>/dev/null | grep -q "blue_team"; then
    echo -e "${GREEN}✓ blue_team role added to users table${NC}"
else
    echo -e "${RED}✗ blue_team role not found in users table${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Blue Team Migration Completed Successfully!            ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Next steps:"
echo "  1. Deploy your application with the new Blue Team code"
echo "  2. As admin, go to Users tab and click 'Grant Blue Team' on any user"
echo "  3. That user will now have access to /blue-team dashboard"
echo ""

