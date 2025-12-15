#!/bin/bash
# Script to setup admin user (delete all users and create admin)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}=== Admin Setup Script ===${NC}\n"
echo -e "${YELLOW}This will DELETE ALL existing users and create an admin user.${NC}"
echo -e "${YELLOW}Username: Admin${NC}"
echo -e "${YELLOW}Email: theoneandonly@gmail.com${NC}"
echo -e "${YELLOW}Password: theoneandonly${NC}\n"

read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${RED}Cancelled.${NC}"
    exit 0
fi

# Check if we're in WSL
if [ -f /proc/version ] && grep -qi microsoft /proc/version; then
    PROJECT_DIR="/mnt/c/Users/anshu/OneDrive/Desktop/ropetyapp-devsec-main"
    cd "$PROJECT_DIR" || exit 1
else
    PROJECT_DIR="$(pwd)"
fi

# Check if Cloud SQL Proxy is running
if ! pgrep -f "cloud-sql-proxy" > /dev/null; then
    echo -e "${YELLOW}Starting Cloud SQL Proxy...${NC}"
    CONNECTION_NAME=$(gcloud sql instances describe robo --format='value(connectionName)')
    ./cloud-sql-proxy "$CONNECTION_NAME" --port 3310 > /tmp/cloud-sql-proxy.log 2>&1 &
    sleep 5
fi

# Set environment variables
export CLOUD_SQL_USERNAME="root"
export CLOUD_SQL_PASSWORD="-6uB+6(7_bHPGmGu"
export CLOUD_SQL_DATABASE_NAME="ROBOPETY"
export CLOUD_SQL_CONNECTION_NAME="melodic-voice-475605-d2:us-central1:robo"
export JWT_SECRET="s3yPp7rV1iQe9kJw4ZxTnA2uB8LmF0cGhYdR5qKsO3vWbEtU"
export BUCKET_NAME="robo-images-melodic-voice-475605-d2"

echo -e "${CYAN}Running admin setup script...${NC}"

# Activate virtual environment if it exists, otherwise use system python
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}Using virtual environment${NC}"
fi

# Run the Python script
python3 setup_admin.py

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}✓ Admin setup completed successfully!${NC}"
    echo -e "\n${YELLOW}You can now login with:${NC}"
    echo -e "  Email: theoneandonly@gmail.com"
    echo -e "  Password: theoneandonly"
else
    echo -e "\n${RED}✗ Admin setup failed. Check the error messages above.${NC}"
    exit 1
fi

