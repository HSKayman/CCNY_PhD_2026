#!/bin/bash
# Script to run new feature migrations (activity tracking and robot status)

set -e

# Configuration from app.yaml
PROJECT_ID="csci0220-472715"
SQL_INSTANCE="robo"
SQL_PASSWORD="-6uB+6(7_bHPGmGupolivoliv67"
CONNECTION_NAME="csci0220-472715:us-central1:robo"
DB_NAME="ROBOPETY"
PROXY_PORT=3310

echo "🚀 Running new feature migrations..."
echo ""

# Check if cloud-sql-proxy exists
if [ ! -f "./cloud-sql-proxy" ]; then
    echo "❌ cloud-sql-proxy not found. Downloading..."
    ARCH=$(uname -m)
    if [[ "$ARCH" == "x86_64" || "$ARCH" == "amd64" ]]; then
        PROXY_URL="https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.linux.amd64"
    elif [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
        PROXY_URL="https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.linux.arm64"
    else
        # Windows or other - try Windows version
        if [[ "$ARCH" == *"x86"* ]]; then
            PROXY_URL="https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.x64.exe"
        else
            echo "❌ Unsupported architecture: $ARCH"
            exit 1
        fi
    fi
    curl -fsSL -o cloud-sql-proxy "$PROXY_URL"
    chmod +x cloud-sql-proxy
    echo "✓ cloud-sql-proxy downloaded"
fi

# Stop any existing proxy on this port
pkill -f "cloud-sql-proxy.*--port ${PROXY_PORT}" 2>/dev/null || true
sleep 1

# Start proxy
echo "Starting Cloud SQL Proxy on port ${PROXY_PORT}..."
./cloud-sql-proxy "${CONNECTION_NAME}" --port ${PROXY_PORT} > /tmp/cloud-sql-proxy.log 2>&1 &
PROXY_PID=$!
echo "Proxy PID: $PROXY_PID"

# Wait for proxy to be ready
echo "Waiting for proxy to connect..."
for i in {1..30}; do
    if mysql -h 127.0.0.1 -P ${PROXY_PORT} -u root -p"$SQL_PASSWORD" -e "SELECT 1" &>/dev/null 2>&1; then
        echo "✓ Connected to Cloud SQL"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Failed to connect. Check /tmp/cloud-sql-proxy.log"
        kill $PROXY_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# Function to check if column exists
check_column_exists() {
    local table=$1
    local column=$2
    mysql -h 127.0.0.1 -P ${PROXY_PORT} -u root -p"$SQL_PASSWORD" -N -e \
        "USE \`${DB_NAME}\`; SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='${DB_NAME}' AND TABLE_NAME='${table}' AND COLUMN_NAME='${column}';" \
        2>/dev/null | grep -v "Using a password" || echo "0"
}

# Function to check if table exists
check_table_exists() {
    local table=$1
    mysql -h 127.0.0.1 -P ${PROXY_PORT} -u root -p"$SQL_PASSWORD" -N -e \
        "USE \`${DB_NAME}\`; SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='${DB_NAME}' AND TABLE_NAME='${table}';" \
        2>/dev/null | grep -v "Using a password" || echo "0"
}

echo ""
echo "=== Migration 1: Activity Tracking ==="
echo ""

# Check if last_login column exists
LAST_LOGIN_EXISTS=$(check_column_exists "users" "last_login")
LOGIN_COUNT_EXISTS=$(check_column_exists "users" "login_count")
ACTIVITY_TABLE_EXISTS=$(check_table_exists "user_activity_log")

if [ "$LAST_LOGIN_EXISTS" -eq "1" ] && [ "$LOGIN_COUNT_EXISTS" -eq "1" ] && [ "$ACTIVITY_TABLE_EXISTS" -eq "1" ]; then
    echo "✓ Activity tracking migration already applied"
else
    echo "Running activity tracking migration..."
    
    # Add columns if they don't exist
    if [ "$LAST_LOGIN_EXISTS" -ne "1" ]; then
        echo "  Adding last_login column..."
        mysql -h 127.0.0.1 -P ${PROXY_PORT} -u root -p"$SQL_PASSWORD" "$DB_NAME" -e \
            "ALTER TABLE users ADD COLUMN last_login DATETIME DEFAULT NULL;" \
            2>&1 | grep -v "Using a password" || echo "  (Column may already exist)"
    fi
    
    if [ "$LOGIN_COUNT_EXISTS" -ne "1" ]; then
        echo "  Adding login_count column..."
        mysql -h 127.0.0.1 -P ${PROXY_PORT} -u root -p"$SQL_PASSWORD" "$DB_NAME" -e \
            "ALTER TABLE users ADD COLUMN login_count INT DEFAULT 0;" \
            2>&1 | grep -v "Using a password" || echo "  (Column may already exist)"
    fi
    
    # Create activity log table
    if [ "$ACTIVITY_TABLE_EXISTS" -ne "1" ]; then
        echo "  Creating user_activity_log table..."
        mysql -h 127.0.0.1 -P ${PROXY_PORT} -u root -p"$SQL_PASSWORD" "$DB_NAME" -e "
            CREATE TABLE IF NOT EXISTS user_activity_log (
                id INT NOT NULL AUTO_INCREMENT,
                user_id INT NOT NULL,
                activity_type VARCHAR(50) NOT NULL,
                description VARCHAR(500),
                ip_address VARCHAR(45),
                user_agent VARCHAR(500),
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_created_at (created_at),
                INDEX idx_activity_type (activity_type)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        " 2>&1 | grep -v "Using a password" || true
    fi
    
    echo "✓ Activity tracking migration completed"
fi

echo ""
echo "=== Migration 2: Robot Status ==="
echo ""

# Check if robot status columns exist
STATUS_EXISTS=$(check_column_exists "robots" "status")
DESCRIPTION_EXISTS=$(check_column_exists "robots" "description")
CATEGORY_EXISTS=$(check_column_exists "robots" "category")
IS_ACTIVE_EXISTS=$(check_column_exists "robots" "is_active")
CREATED_AT_EXISTS=$(check_column_exists "robots" "created_at")
UPDATED_AT_EXISTS=$(check_column_exists "robots" "updated_at")

if [ "$STATUS_EXISTS" -eq "1" ] && [ "$DESCRIPTION_EXISTS" -eq "1" ] && [ "$CATEGORY_EXISTS" -eq "1" ] && [ "$IS_ACTIVE_EXISTS" -eq "1" ] && [ "$CREATED_AT_EXISTS" -eq "1" ] && [ "$UPDATED_AT_EXISTS" -eq "1" ]; then
    echo "✓ Robot status migration already applied"
else
    echo "Running robot status migration..."
    
    # Add columns if they don't exist
    if [ "$STATUS_EXISTS" -ne "1" ]; then
        echo "  Adding status column..."
        mysql -h 127.0.0.1 -P ${PROXY_PORT} -u root -p"$SQL_PASSWORD" "$DB_NAME" -e \
            "ALTER TABLE robots ADD COLUMN status VARCHAR(20) DEFAULT 'available';" \
            2>&1 | grep -v "Using a password" || echo "  (Column may already exist)"
    fi
    
    if [ "$DESCRIPTION_EXISTS" -ne "1" ]; then
        echo "  Adding description column..."
        mysql -h 127.0.0.1 -P ${PROXY_PORT} -u root -p"$SQL_PASSWORD" "$DB_NAME" -e \
            "ALTER TABLE robots ADD COLUMN description TEXT;" \
            2>&1 | grep -v "Using a password" || echo "  (Column may already exist)"
    fi
    
    if [ "$CATEGORY_EXISTS" -ne "1" ]; then
        echo "  Adding category column..."
        mysql -h 127.0.0.1 -P ${PROXY_PORT} -u root -p"$SQL_PASSWORD" "$DB_NAME" -e \
            "ALTER TABLE robots ADD COLUMN category VARCHAR(100);" \
            2>&1 | grep -v "Using a password" || echo "  (Column may already exist)"
    fi
    
    if [ "$IS_ACTIVE_EXISTS" -ne "1" ]; then
        echo "  Adding is_active column..."
        mysql -h 127.0.0.1 -P ${PROXY_PORT} -u root -p"$SQL_PASSWORD" "$DB_NAME" -e \
            "ALTER TABLE robots ADD COLUMN is_active BOOLEAN DEFAULT TRUE;" \
            2>&1 | grep -v "Using a password" || echo "  (Column may already exist)"
    fi
    
    if [ "$CREATED_AT_EXISTS" -ne "1" ]; then
        echo "  Adding created_at column..."
        mysql -h 127.0.0.1 -P ${PROXY_PORT} -u root -p"$SQL_PASSWORD" "$DB_NAME" -e \
            "ALTER TABLE robots ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP;" \
            2>&1 | grep -v "Using a password" || echo "  (Column may already exist)"
    fi
    
    if [ "$UPDATED_AT_EXISTS" -ne "1" ]; then
        echo "  Adding updated_at column..."
        mysql -h 127.0.0.1 -P ${PROXY_PORT} -u root -p"$SQL_PASSWORD" "$DB_NAME" -e \
            "ALTER TABLE robots ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;" \
            2>&1 | grep -v "Using a password" || echo "  (Column may already exist)"
    fi
    
    # Update existing robots
    echo "  Updating existing robots..."
    mysql -h 127.0.0.1 -P ${PROXY_PORT} -u root -p"$SQL_PASSWORD" "$DB_NAME" -e \
        "UPDATE robots SET status = 'available', is_active = TRUE WHERE status IS NULL OR is_active IS NULL;" \
        2>&1 | grep -v "Using a password" || true
    
    # Create indexes (check if they exist first)
    echo "  Creating indexes..."
    INDEX_STATUS_EXISTS=$(mysql -h 127.0.0.1 -P ${PROXY_PORT} -u root -p"$SQL_PASSWORD" -N -e \
        "USE \`${DB_NAME}\`; SELECT COUNT(*) FROM information_schema.STATISTICS WHERE TABLE_SCHEMA='${DB_NAME}' AND TABLE_NAME='robots' AND INDEX_NAME='idx_robot_status';" \
        2>/dev/null | grep -v "Using a password" || echo "0")
    INDEX_ACTIVE_EXISTS=$(mysql -h 127.0.0.1 -P ${PROXY_PORT} -u root -p"$SQL_PASSWORD" -N -e \
        "USE \`${DB_NAME}\`; SELECT COUNT(*) FROM information_schema.STATISTICS WHERE TABLE_SCHEMA='${DB_NAME}' AND TABLE_NAME='robots' AND INDEX_NAME='idx_robot_active';" \
        2>/dev/null | grep -v "Using a password" || echo "0")
    
    if [ "$INDEX_STATUS_EXISTS" -ne "1" ]; then
        mysql -h 127.0.0.1 -P ${PROXY_PORT} -u root -p"$SQL_PASSWORD" "$DB_NAME" -e \
            "CREATE INDEX idx_robot_status ON robots(status);" \
            2>&1 | grep -v "Using a password" || true
    fi
    
    if [ "$INDEX_ACTIVE_EXISTS" -ne "1" ]; then
        mysql -h 127.0.0.1 -P ${PROXY_PORT} -u root -p"$SQL_PASSWORD" "$DB_NAME" -e \
            "CREATE INDEX idx_robot_active ON robots(is_active);" \
            2>&1 | grep -v "Using a password" || true
    fi
    
    echo "✓ Robot status migration completed"
fi

# Verify migrations
echo ""
echo "=== Verification ==="
echo ""

LAST_LOGIN_CHECK=$(check_column_exists "users" "last_login")
LOGIN_COUNT_CHECK=$(check_column_exists "users" "login_count")
ACTIVITY_TABLE_CHECK=$(check_table_exists "user_activity_log")
STATUS_CHECK=$(check_column_exists "robots" "status")
IS_ACTIVE_CHECK=$(check_column_exists "robots" "is_active")

echo "Activity Tracking:"
echo "  users.last_login: $([ "$LAST_LOGIN_CHECK" -eq "1" ] && echo "✓" || echo "❌")"
echo "  users.login_count: $([ "$LOGIN_COUNT_CHECK" -eq "1" ] && echo "✓" || echo "❌")"
echo "  user_activity_log table: $([ "$ACTIVITY_TABLE_CHECK" -eq "1" ] && echo "✓" || echo "❌")"
echo ""
echo "Robot Status:"
echo "  robots.status: $([ "$STATUS_CHECK" -eq "1" ] && echo "✓" || echo "❌")"
echo "  robots.is_active: $([ "$IS_ACTIVE_CHECK" -eq "1" ] && echo "✓" || echo "❌")"

# Stop proxy
echo ""
echo "Stopping proxy..."
kill $PROXY_PID 2>/dev/null || true
sleep 1

echo ""
echo "✅ Migrations complete!"
echo ""

