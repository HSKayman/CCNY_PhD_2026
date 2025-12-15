#!/bin/bash
# Script to verify 2FA migration was successful
# Usage: ./verify_2fa_migration.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Verifying 2FA migration...${NC}"
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

# Check if columns exist
echo -e "${BLUE}Checking for 2FA columns in users table...${NC}"

COLUMNS=$(mysql -h 127.0.0.1 -P ${PROXY_PORT} -u ${DB_USER} -p"${DB_PASSWORD}" ${DB_NAME} -sN -e "
SELECT COLUMN_NAME 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = '${DB_NAME}' 
  AND TABLE_NAME = 'users' 
  AND COLUMN_NAME IN ('two_factor_enabled', 'two_factor_secret', 'two_factor_backup_codes')
ORDER BY COLUMN_NAME;
" 2>/dev/null)

if [ -z "$COLUMNS" ]; then
    echo -e "${RED}✗ 2FA columns not found! Migration may have failed.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found 2FA columns:${NC}"
echo "$COLUMNS" | while read col; do
    echo -e "  ${GREEN}✓${NC} $col"
done

# Check if index exists
echo ""
echo -e "${BLUE}Checking for 2FA index...${NC}"
INDEX_EXISTS=$(mysql -h 127.0.0.1 -P ${PROXY_PORT} -u ${DB_USER} -p"${DB_PASSWORD}" ${DB_NAME} -sN -e "
SELECT COUNT(*) 
FROM INFORMATION_SCHEMA.STATISTICS 
WHERE TABLE_SCHEMA = '${DB_NAME}' 
  AND TABLE_NAME = 'users' 
  AND INDEX_NAME = 'idx_users_two_factor_enabled';
" 2>/dev/null)

if [ "$INDEX_EXISTS" = "1" ]; then
    echo -e "${GREEN}✓ Index 'idx_users_two_factor_enabled' exists${NC}"
else
    echo -e "${YELLOW}⚠ Index 'idx_users_two_factor_enabled' not found (optional)${NC}"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ 2FA Migration Verified Successfully!                ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "  1. Install dependencies: ${YELLOW}pip install -r requirements.txt${NC}"
echo -e "  2. Restart your Flask application"
echo -e "  3. Test 2FA by enabling it for a user account"

