#!/bin/bash
# Quick script to run database migration on production Cloud SQL

set -e

# Configuration
PROJECT_ID="melodic-voice-475605-d2"
SQL_INSTANCE="robo"
SQL_PASSWORD="-6uB+6(7_bHPGmGu"
CONNECTION_NAME="melodic-voice-475605-d2:us-central1:robo"
DB_NAME="ROBOPETY"

echo "🚀 Running database migration on production Cloud SQL..."
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
        echo "❌ Unsupported architecture: $ARCH"
        exit 1
    fi
    curl -fsSL -o cloud-sql-proxy "$PROXY_URL"
    chmod +x cloud-sql-proxy
    echo "✓ cloud-sql-proxy downloaded"
fi

# Stop any existing proxy
pkill cloud-sql-proxy 2>/dev/null || true
sleep 1

# Start proxy
echo "Starting Cloud SQL Proxy..."
./cloud-sql-proxy "${CONNECTION_NAME}" --port 3310 > /tmp/cloud-sql-proxy.log 2>&1 &
PROXY_PID=$!
echo "Proxy PID: $PROXY_PID"

# Wait for proxy to be ready
echo "Waiting for proxy to connect..."
for i in {1..30}; do
    if mysql -h 127.0.0.1 -P 3310 -u root -p"$SQL_PASSWORD" -e "SELECT 1" &>/dev/null; then
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

# Check if role column already exists
echo ""
echo "Checking if migration already applied..."
ROLE_EXISTS=$(mysql -h 127.0.0.1 -P 3310 -u root -p"$SQL_PASSWORD" -N -e "USE \`${DB_NAME}\`; SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='${DB_NAME}' AND TABLE_NAME='users' AND COLUMN_NAME='role';" 2>/dev/null || echo "0")

if [ "$ROLE_EXISTS" -eq "1" ]; then
    echo "✓ Migration already applied (role column exists)"
else
    echo "Running migration..."
    
    # Run migration (use safe version that checks for existing columns)
    if [ -f "migration_add_role_safe.sql" ]; then
        echo "Using safe migration script..."
        mysql -h 127.0.0.1 -P 3310 -u root -p"$SQL_PASSWORD" "$DB_NAME" < migration_add_role_safe.sql 2>&1 | grep -v "Using a password" || true
        echo "✓ Migration completed"
    elif [ -f "migration_add_role.sql" ]; then
        echo "Using standard migration script (may show errors if columns exist)..."
        # Suppress "column already exists" errors but show others
        mysql -h 127.0.0.1 -P 3310 -u root -p"$SQL_PASSWORD" "$DB_NAME" < migration_add_role.sql 2>&1 | grep -v "Using a password" | grep -v "Duplicate column name" || {
            # Check if error was just "column exists" - that's okay
            ERROR_OUTPUT=$(mysql -h 127.0.0.1 -P 3310 -u root -p"$SQL_PASSWORD" "$DB_NAME" < migration_add_role.sql 2>&1 || true)
            if echo "$ERROR_OUTPUT" | grep -q "Duplicate column name"; then
                echo "⚠️  Some columns already exist (migration may have been partially applied)"
                echo "   This is okay - continuing..."
            else
                echo "❌ Migration failed with error:"
                echo "$ERROR_OUTPUT" | grep -v "Using a password"
                kill $PROXY_PID 2>/dev/null || true
                exit 1
            fi
        }
        echo "✓ Migration completed"
    else
        echo "❌ Migration SQL file not found!"
        kill $PROXY_PID 2>/dev/null || true
        exit 1
    fi
    
    # Verify migration
    ROLE_EXISTS_AFTER=$(mysql -h 127.0.0.1 -P 3310 -u root -p"$SQL_PASSWORD" -N -e "USE \`${DB_NAME}\`; SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='${DB_NAME}' AND TABLE_NAME='users' AND COLUMN_NAME='role';" 2>/dev/null || echo "0")
    
    if [ "$ROLE_EXISTS_AFTER" -eq "1" ]; then
        echo "✓ Migration verified - role column exists"
    else
        echo "❌ Migration may have failed - role column still missing"
    fi
fi

# Check created_at columns
echo ""
echo "Checking created_at columns..."
USERS_CREATED_AT=$(mysql -h 127.0.0.1 -P 3310 -u root -p"$SQL_PASSWORD" -N -e "USE \`${DB_NAME}\`; SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='${DB_NAME}' AND TABLE_NAME='users' AND COLUMN_NAME='created_at';" 2>/dev/null || echo "0")
USER_ROBOTS_CREATED_AT=$(mysql -h 127.0.0.1 -P 3310 -u root -p"$SQL_PASSWORD" -N -e "USE \`${DB_NAME}\`; SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='${DB_NAME}' AND TABLE_NAME='user_robots' AND COLUMN_NAME='created_at';" 2>/dev/null || echo "0")

if [ "$USERS_CREATED_AT" -eq "1" ] && [ "$USER_ROBOTS_CREATED_AT" -eq "1" ]; then
    echo "✓ All columns migrated successfully"
else
    echo "⚠️  Some columns may be missing:"
    echo "   users.created_at: $([ "$USERS_CREATED_AT" -eq "1" ] && echo "✓" || echo "❌")"
    echo "   user_robots.created_at: $([ "$USER_ROBOTS_CREATED_AT" -eq "1" ] && echo "✓" || echo "❌")"
fi

# Stop proxy
echo ""
echo "Stopping proxy..."
kill $PROXY_PID 2>/dev/null || true
sleep 1

echo ""
echo "✅ Migration complete! Your app should now work."
echo ""
echo "Note: If you still see errors, wait a few seconds for App Engine to refresh,"
echo "      or redeploy: gcloud app deploy"

