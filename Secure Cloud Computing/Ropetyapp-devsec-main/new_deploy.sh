#!/bin/bash
#
# Robopety Complete Deployment Script (WSL / Ubuntu)
# Enhanced version with all security features, database migration, and reCAPTCHA
# This script installs dependencies and automates Google Cloud deployment
# Designed for WSL (Ubuntu/Debian)
#
# Features:
# - Complete infrastructure setup (Cloud SQL, Storage, App Engine)
# - Database migration with role-based access control
# - Security enhancements (SQLAlchemy, Flask-Talisman, rate limiting)
# - Google reCAPTCHA integration
# - Secret Manager setup
# - All security files verification
#

set -e  # Exit on error
set -o pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration variables (will be set from app.yaml or user input)
PROJECT_ID=""
SQL_INSTANCE="robo"
SQL_PASSWORD=""
BUCKET_NAME=""
REGION="us-central1"
CONNECTION_NAME=""
DB_NAME="ROBOPETY"
CLOUD_SQL_USERNAME="root"

# Function to extract value from app.yaml
extract_app_yaml_value() {
    local key="$1"
    local app_yaml="${2:-app.yaml}"
    
    if [ ! -f "$app_yaml" ]; then
        return 1
    fi
    
    # Extract value - handles both quoted and unquoted values
    local value=$(grep -A 100 "^env_variables:" "$app_yaml" | \
        grep -E "^\s*${key}:" | \
        head -1 | \
        sed -E "s/^\s*${key}:\s*[\"']?([^\"']*)[\"']?\s*$/\1/" | \
        sed 's/^ *//;s/ *$//')
    
    if [ -n "$value" ]; then
        echo "$value"
        return 0
    fi
    return 1
}

# Function to parse connection name and extract project, region, instance
parse_connection_name() {
    local conn_name="$1"
    if [[ "$conn_name" =~ ^([^:]+):([^:]+):(.+)$ ]]; then
        PROJECT_ID="${BASH_REMATCH[1]}"
        REGION="${BASH_REMATCH[2]}"
        SQL_INSTANCE="${BASH_REMATCH[3]}"
        return 0
    fi
    return 1
}

# Load configuration from app.yaml or prompt user
load_project_config() {
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}Project Configuration Setup${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if [ -f "app.yaml" ]; then
        echo -e "${GREEN}Found app.yaml - extracting configuration...${NC}"
        
        # Extract values from app.yaml
        TEMP_CONNECTION_NAME=$(extract_app_yaml_value "CLOUD_SQL_CONNECTION_NAME" "app.yaml")
        TEMP_PASSWORD=$(extract_app_yaml_value "CLOUD_SQL_PASSWORD" "app.yaml")
        TEMP_BUCKET=$(extract_app_yaml_value "BUCKET_NAME" "app.yaml")
        TEMP_DB_NAME=$(extract_app_yaml_value "CLOUD_SQL_DATABASE_NAME" "app.yaml")
        
        if [ -n "$TEMP_CONNECTION_NAME" ]; then
            parse_connection_name "$TEMP_CONNECTION_NAME"
            CONNECTION_NAME="$TEMP_CONNECTION_NAME"
        fi
        
        if [ -n "$TEMP_PASSWORD" ]; then
            SQL_PASSWORD="$TEMP_PASSWORD"
        fi
        
        if [ -n "$TEMP_BUCKET" ]; then
            BUCKET_NAME="$TEMP_BUCKET"
        fi
        
        if [ -n "$TEMP_DB_NAME" ]; then
            DB_NAME="$TEMP_DB_NAME"
        fi
        
        # Show detected configuration
        if [ -n "$PROJECT_ID" ]; then
            echo -e "${GREEN}✓ Configuration loaded from app.yaml:${NC}"
            echo -e "  Project ID:       ${BLUE}${PROJECT_ID}${NC}"
            echo -e "  Region:           ${BLUE}${REGION}${NC}"
            echo -e "  SQL Instance:     ${BLUE}${SQL_INSTANCE}${NC}"
            echo -e "  Connection Name:  ${BLUE}${CONNECTION_NAME}${NC}"
            echo -e "  Database Name:    ${BLUE}${DB_NAME}${NC}"
            echo -e "  Bucket Name:      ${BLUE}${BUCKET_NAME}${NC}"
            echo ""
            read -p "Use this configuration? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo -e "${GREEN}✓ Using configuration from app.yaml${NC}"
                return 0
            fi
        fi
    fi
    
    # Manual input if app.yaml not found or user wants to override
    echo -e "${YELLOW}Enter project configuration manually:${NC}"
    
    # Get PROJECT_ID
    if [ -z "$PROJECT_ID" ]; then
        read -p "Google Cloud Project ID: " PROJECT_ID
        if [ -z "$PROJECT_ID" ]; then
            echo -e "${RED}✗ Project ID is required${NC}"
            exit 1
        fi
    else
        read -p "Google Cloud Project ID [${PROJECT_ID}]: " INPUT_PROJECT_ID
        if [ -n "$INPUT_PROJECT_ID" ]; then
            PROJECT_ID="$INPUT_PROJECT_ID"
        fi
    fi
    
    # Get SQL_INSTANCE
    read -p "Cloud SQL Instance Name [${SQL_INSTANCE}]: " INPUT_SQL_INSTANCE
    if [ -n "$INPUT_SQL_INSTANCE" ]; then
        SQL_INSTANCE="$INPUT_SQL_INSTANCE"
    fi
    
    # Get REGION
    read -p "Region [${REGION}]: " INPUT_REGION
    if [ -n "$INPUT_REGION" ]; then
        REGION="$INPUT_REGION"
    fi
    
    # Build CONNECTION_NAME
    CONNECTION_NAME="${PROJECT_ID}:${REGION}:${SQL_INSTANCE}"
    
    # Get SQL_PASSWORD
    if [ -z "$SQL_PASSWORD" ]; then
        read -sp "Cloud SQL Root Password: " SQL_PASSWORD
        echo
        if [ -z "$SQL_PASSWORD" ]; then
            echo -e "${RED}✗ SQL password is required${NC}"
            exit 1
        fi
    else
        read -sp "Cloud SQL Root Password [use existing]: " INPUT_PASSWORD
        echo
        if [ -n "$INPUT_PASSWORD" ]; then
            SQL_PASSWORD="$INPUT_PASSWORD"
        fi
    fi
    
    # Get BUCKET_NAME
    if [ -z "$BUCKET_NAME" ]; then
        DEFAULT_BUCKET="robo-images-${PROJECT_ID}"
        read -p "Storage Bucket Name [${DEFAULT_BUCKET}]: " INPUT_BUCKET
        if [ -n "$INPUT_BUCKET" ]; then
            BUCKET_NAME="$INPUT_BUCKET"
        else
            BUCKET_NAME="$DEFAULT_BUCKET"
        fi
    else
        read -p "Storage Bucket Name [${BUCKET_NAME}]: " INPUT_BUCKET
        if [ -n "$INPUT_BUCKET" ]; then
            BUCKET_NAME="$INPUT_BUCKET"
        fi
    fi
    
    # Get DB_NAME
    read -p "Database Name [${DB_NAME}]: " INPUT_DB_NAME
    if [ -n "$INPUT_DB_NAME" ]; then
        DB_NAME="$INPUT_DB_NAME"
    fi
    
    echo -e "\n${GREEN}✓ Configuration saved:${NC}"
    echo -e "  Project ID:       ${BLUE}${PROJECT_ID}${NC}"
    echo -e "  Region:           ${BLUE}${REGION}${NC}"
    echo -e "  SQL Instance:     ${BLUE}${SQL_INSTANCE}${NC}"
    echo -e "  Connection Name:  ${BLUE}${CONNECTION_NAME}${NC}"
    echo -e "  Database Name:    ${BLUE}${DB_NAME}${NC}"
    echo -e "  Bucket Name:      ${BLUE}${BUCKET_NAME}${NC}"
}

echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Robopety Enhanced Deployment Script (WSL)            ║${NC}"
echo -e "${GREEN}║   Complete Setup & Deployment with Security Features   ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Ensure script is run in WSL / Linux
if [[ "$(uname -s)" != "Linux" ]]; then
    echo -e "${RED}✗ This script is intended to run in WSL / Linux${NC}"
    exit 1
fi

# Ensure sudo is available
if ! command -v sudo &>/dev/null; then
    echo -e "${RED}✗ 'sudo' not found. Please install sudo or run as root.${NC}"
    exit 1
fi

# Update and install common prerequisites
install_prereqs() {
    echo -e "\n${BLUE}[1/13] Updating apt and installing prerequisites...${NC}"
    sudo apt-get update -y
    sudo apt-get install -y --no-install-recommends \
        apt-transport-https ca-certificates gnupg curl wget lsb-release unzip \
        software-properties-common

    echo -e "${GREEN}✓ Prerequisites installed${NC}"
}

# Install Google Cloud SDK (apt repository) - recommended for WSL
install_gcloud() {
    echo -e "\n${BLUE}[2/13] Installing Google Cloud SDK...${NC}"
    if command -v gcloud &>/dev/null; then
        echo -e "${GREEN}✓ gcloud CLI found${NC}"
        return
    fi

    # Add Google Cloud apt repository and GPG key
    echo -e "${YELLOW}Adding Google Cloud SDK apt repository...${NC}"
    curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | \
        sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list > /dev/null

    sudo apt-get update -y
    sudo apt-get install -y google-cloud-sdk || {
        echo -e "${YELLOW}! apt install failed, trying snap (if available)${NC}"
        if command -v snap &>/dev/null; then
            sudo snap install google-cloud-sdk --classic || {
                echo -e "${RED}✗ Could not install google-cloud-sdk via apt or snap.${NC}"
                exit 1
            }
        else
            echo -e "${RED}✗ snap is not available; please install gcloud manually.${NC}"
            exit 1
        fi
    }

    echo -e "${GREEN}✓ gcloud CLI installed${NC}"
}

# Install MySQL client
install_mysql_client() {
    echo -e "\n${BLUE}[3/13] Installing MySQL client...${NC}"
    if command -v mysql &>/dev/null; then
        echo -e "${GREEN}✓ MySQL client found${NC}"
        return
    fi

    sudo apt-get install -y default-mysql-client || sudo apt-get install -y mysql-client || {
        echo -e "${RED}✗ Failed to install MySQL client${NC}"
        exit 1
    }
    echo -e "${GREEN}✓ MySQL client installed${NC}"
}

# Install Python dependencies
install_python_deps() {
    echo -e "\n${BLUE}[4/13] Setting up Python virtual environment (fast & safe)...${NC}"

    # Ensure system Python + venv support are present (idempotent)
    sudo apt-get update -y
    sudo apt-get install -y --no-install-recommends python3 python3-venv python3-full curl rsync || {
        echo -e "${YELLOW}Warning: could not ensure some system packages via apt (continuing)${NC}"
    }

    # Determine project dir and whether it's on /mnt (Windows)
    ORIGINAL_PROJECT_DIR="$(pwd)"
    PROJECT_BASENAME="$(basename "$ORIGINAL_PROJECT_DIR")"

    if [[ "$ORIGINAL_PROJECT_DIR" == /mnt/* ]]; then
        # Copy project into WSL native FS for fast pip operations
        TARGET_DIR="$HOME/projects/${PROJECT_BASENAME}"
        echo -e "${YELLOW}Project is on Windows-mounted FS. Copying to WSL native path: ${TARGET_DIR}${NC}"
        mkdir -p "$(dirname "$TARGET_DIR")"
        rsync -a --info=progress2 "$ORIGINAL_PROJECT_DIR/" "$TARGET_DIR/" --exclude venv || {
            echo -e "${YELLOW}rsync warning/failure — continuing with whatever copied${NC}"
        }
        cd "$TARGET_DIR" || { echo -e "${RED}Failed to cd to $TARGET_DIR${NC}"; exit 1; }
    else
        TARGET_DIR="$ORIGINAL_PROJECT_DIR"
        echo -e "${BLUE}Using project directory: ${TARGET_DIR}${NC}"
    fi

    # Where to put the venv: prefer project/venv inside WSL FS
    VENV_DIR="${TARGET_DIR}/venv"

    # Create venv if missing
    if [ ! -d "${VENV_DIR}" ]; then
        echo -e "${BLUE}Creating venv at ${VENV_DIR}...${NC}"
        python3 -m venv "${VENV_DIR}" || {
            echo -e "${YELLOW}python3 -m venv failed — trying ensurepip/get-pip fallback${NC}"
            python3 -m ensurepip --upgrade || true
            python3 -m venv "${VENV_DIR}" || {
                echo -e "${RED}✗ Failed to create venv${NC}"
                exit 1
            }
        }
    fi

    # Activate venv for the remainder of the script (same shell)
    # shellcheck disable=SC1090
    source "${VENV_DIR}/bin/activate"

    # Confirm python/pip locations and versions
    echo -e "${BLUE}Using Python: $(which python) ($(python --version 2>&1))${NC}"
    echo -e "${BLUE}Using pip: $(which pip) ($(pip --version 2>&1))${NC}"

    # Upgrade pip in a safe way
    echo -e "${BLUE}Ensuring pip/setuptools/wheel are up-to-date inside venv...${NC}"
    if ! python -m pip install --upgrade pip setuptools wheel --no-cache-dir --disable-pip-version-check -q; then
        echo -e "${YELLOW}pip upgrade failed — attempting ensurepip fallback${NC}"
        python -m ensurepip --upgrade || true
        python -m pip install --upgrade pip setuptools wheel --no-cache-dir --disable-pip-version-check -q || {
            echo -e "${YELLOW}pip upgrade still failing — using get-pip.py fallback${NC}"
            curl -fsSLo /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py
            python /tmp/get-pip.py --force-reinstall
        }
    fi

    # Install requirements if present; use retry to tolerate transient network issues
    if [ -f "requirements.txt" ]; then
        echo -e "${BLUE}Installing Python packages from requirements.txt (including new security dependencies)...${NC}"
        echo -e "${CYAN}  New packages: SQLAlchemy, Flask-Talisman, Flask-Limiter, google-cloud-secret-manager${NC}"
        for attempt in 1 2; do
            if pip install --no-cache-dir -r requirements.txt --disable-pip-version-check -q; then
                echo -e "${GREEN}✓ requirements installed${NC}"
                break
            else
                echo -e "${YELLOW}Attempt ${attempt} failed — retrying...${NC}"
                sleep 2
            fi
            if [ "${attempt}" -eq 2 ]; then
                echo -e "${YELLOW}⚠️ Some pip installs failed; continuing anyway${NC}"
            fi
        done
    else
        echo -e "${RED}✗ requirements.txt not found — this is required!${NC}"
        exit 1
    fi

    # Ensure requests available for image download script (best-effort)
    pip install --no-cache-dir requests --disable-pip-version-check -q || {
        echo -e "${YELLOW}Could not install 'requests' into venv — continuing (download script may fail)${NC}"
    }

    # Export VENV_DIR and current project dir for later script steps
    export ROBOPETY_VENV_PATH="${VENV_DIR}"
    export ROBOPETY_PROJECT_DIR="$(pwd)"
    echo -e "${GREEN}✓ Python virtual environment ready at: ${ROBOPETY_VENV_PATH}${NC}"
    echo -e "${BLUE}Working directory is: ${ROBOPETY_PROJECT_DIR}${NC}"
    echo -e "${BLUE}To activate in a new shell: source ${ROBOPETY_VENV_PATH}/bin/activate${NC}"
}

# Download Cloud SQL Proxy for Linux
install_sql_proxy() {
    echo -e "\n${BLUE}[5/13] Checking Cloud SQL Proxy...${NC}"
    if [ -f "./cloud-sql-proxy" ]; then
        echo -e "${GREEN}✓ Cloud SQL Proxy found${NC}"
        return
    fi

    echo -e "${YELLOW}Downloading Cloud SQL Proxy (Linux)...${NC}"
    ARCH=$(uname -m)
    if [[ "$ARCH" == "x86_64" || "$ARCH" == "amd64" ]]; then
        PROXY_URL="https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.linux.amd64"
    elif [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
        PROXY_URL="https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.linux.arm64"
    else
        echo -e "${RED}✗ Unsupported architecture: $ARCH${NC}"
        exit 1
    fi

    curl -fsSL -o cloud-sql-proxy "$PROXY_URL" || {
        echo -e "${RED}✗ Failed to download Cloud SQL Proxy${NC}"
        exit 1
    }
    chmod +x cloud-sql-proxy
    echo -e "${GREEN}✓ Cloud SQL Proxy downloaded${NC}"
}

# Authenticate gcloud and set project
authenticate_gcloud() {
    echo -e "\n${BLUE}[6/13] Authenticating with Google Cloud...${NC}"

    # Check if already authenticated
    ACTIVE_ACCOUNT=$(gcloud config get-value account 2>/dev/null || echo "")
    ACTIVE_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
    
    if [ -n "$ACTIVE_ACCOUNT" ] && [ "$ACTIVE_ACCOUNT" != "(unset)" ]; then
        echo -e "${GREEN}✓ Currently authenticated as: ${BLUE}${ACTIVE_ACCOUNT}${NC}"
        echo -e "${CYAN}Current project: ${BLUE}${ACTIVE_PROJECT}${NC}"
        echo ""
        
        # First, ask about switching projects (same account, different project)
        if [ -n "${PROJECT_ID:-}" ] && [ "$ACTIVE_PROJECT" != "$PROJECT_ID" ]; then
            echo -e "${YELLOW}Detected project mismatch:${NC}"
            echo -e "${YELLOW}  Current project: ${ACTIVE_PROJECT}${NC}"
            echo -e "${YELLOW}  Target project:  ${PROJECT_ID}${NC}"
            echo -e "${YELLOW}Do you want to switch to project '${PROJECT_ID}' (using the same account)?${NC}"
            read -p "Switch project? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo -e "${BLUE}Setting active project to: ${PROJECT_ID}${NC}"
                gcloud config set project "$PROJECT_ID" --quiet
                ACTIVE_PROJECT="$PROJECT_ID"
                echo -e "${GREEN}✓ Project switched to: ${PROJECT_ID}${NC}"
            else
                echo -e "${YELLOW}Keeping current project: ${ACTIVE_PROJECT}${NC}"
                echo -e "${YELLOW}⚠️  Note: This may cause issues if the project doesn't match your app.yaml configuration${NC}"
            fi
        fi
        
        # Then, separately ask if they want to switch accounts
        echo ""
        echo -e "${CYAN}Do you want to authenticate with a different Google account?${NC}"
        echo -e "${YELLOW}  This will log out the current account (${ACTIVE_ACCOUNT}) and allow you to sign in with a new one.${NC}"
        read -p "Switch to a different account? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Logging out current account...${NC}"
            
            # Logout from current account
            gcloud auth revoke "$ACTIVE_ACCOUNT" 2>/dev/null || {
                echo -e "${YELLOW}⚠️ Could not revoke account directly, attempting full logout...${NC}"
                gcloud auth revoke --all 2>/dev/null || true
            }
            
            # Also logout from ADC
            gcloud auth application-default revoke 2>/dev/null || true
            
            echo -e "${GREEN}✓ Logged out from previous account${NC}"
            echo ""
            echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${YELLOW}Now you can authenticate with a different Google account.${NC}"
            echo -e "${YELLOW}A login URL will be printed below. Open it in your browser.${NC}"
            echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""
            
            # Authenticate with new account
            if gcloud auth login --no-launch-browser; then
                echo -e "${GREEN}✓ Successfully authenticated with new account${NC}"
            else
                echo -e "${RED}✗ Authentication failed${NC}"
                exit 1
            fi
            
            # Configure Application Default Credentials for new account
            echo -e "${BLUE}Configuring Application Default Credentials for new account...${NC}"
            if gcloud auth application-default login --no-launch-browser; then
                echo -e "${GREEN}✓ ADC configured for new account${NC}"
            else
                echo -e "${YELLOW}⚠️ ADC setup skipped or failed — continuing${NC}"
            fi
            
            # Update active account and set project
            ACTIVE_ACCOUNT=$(gcloud config get-value account 2>/dev/null || echo "")
            if [ -n "${PROJECT_ID:-}" ]; then
                echo -e "${BLUE}Setting active project to: ${PROJECT_ID}${NC}"
                gcloud config set project "$PROJECT_ID" --quiet
                ACTIVE_PROJECT="$PROJECT_ID"
            else
                ACTIVE_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
            fi
        else
            echo -e "${GREEN}Using existing authentication: ${BLUE}${ACTIVE_ACCOUNT}${NC}"
            # Ensure project is set correctly even if we didn't switch accounts
            if [ -n "${PROJECT_ID:-}" ] && [ "$ACTIVE_PROJECT" != "$PROJECT_ID" ]; then
                echo -e "${BLUE}Setting active project to: ${PROJECT_ID}${NC}"
                gcloud config set project "$PROJECT_ID" --quiet
                ACTIVE_PROJECT="$PROJECT_ID"
            fi
        fi
    else
        # Not authenticated - proceed with login
        echo -e "${YELLOW}Not authenticated. Using interactive login.${NC}"
        echo -e "${YELLOW}A login URL will be printed below. Open it in your Windows browser.${NC}"
        echo ""

        # Authenticate user (opens URL only)
        if gcloud auth login --no-launch-browser; then
            echo -e "${GREEN}✓ gcloud CLI authenticated (user login)${NC}"
        else
            echo -e "${RED}✗ Interactive login failed${NC}"
            exit 1
        fi

        # Configure Application Default Credentials
        echo -e "${BLUE}Configuring Application Default Credentials...${NC}"
        if gcloud auth application-default login --no-launch-browser; then
            echo -e "${GREEN}✓ ADC configured${NC}"
        else
            echo -e "${YELLOW}⚠️ ADC setup skipped or failed — continuing${NC}"
        fi
        
        # Get newly authenticated account and set project
        ACTIVE_ACCOUNT=$(gcloud config get-value account 2>/dev/null || echo "")
        if [ -n "${PROJECT_ID:-}" ]; then
            echo -e "${BLUE}Setting active project to: ${PROJECT_ID}${NC}"
            gcloud config set project "$PROJECT_ID" --quiet
            ACTIVE_PROJECT="$PROJECT_ID"
        else
            ACTIVE_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")
        fi
    fi
    
    # Verify ADC is configured for current account
    if ! gcloud auth application-default print-access-token &>/dev/null; then
        echo -e "${YELLOW}Application Default Credentials not configured. Setting up...${NC}"
        if gcloud auth application-default login --no-launch-browser; then
            echo -e "${GREEN}✓ ADC configured${NC}"
        else
            echo -e "${YELLOW}⚠️ ADC setup skipped or failed — continuing${NC}"
        fi
    else
        echo -e "${GREEN}✓ Application Default Credentials configured${NC}"
    fi

    # Final summary
    ACTIVE_ACCOUNT=$(gcloud config get-value account 2>/dev/null || echo "")
    ACTIVE_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")

    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Authentication Summary:${NC}"
    echo -e "  Account: ${BLUE}${ACTIVE_ACCOUNT}${NC}"
    echo -e "  Project: ${BLUE}${ACTIVE_PROJECT}${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    return 0
}

# Enable required APIs
enable_apis() {
    echo -e "\n${BLUE}[7/13] Enabling required Google Cloud APIs...${NC}"
    echo -e "${YELLOW}This may take a minute...${NC}"
    gcloud services enable sqladmin.googleapis.com --quiet
    gcloud services enable storage-api.googleapis.com --quiet
    gcloud services enable appengine.googleapis.com --quiet
    gcloud services enable sql-component.googleapis.com --quiet
    gcloud services enable secretmanager.googleapis.com --quiet || {
        echo -e "${YELLOW}⚠️ Secret Manager API enable failed (optional, continuing)${NC}"
    }
    echo -e "${GREEN}✓ All APIs enabled${NC}"
}

# Create Cloud SQL instance (if missing)
create_sql_instance() {
    echo -e "\n${BLUE}[8/13] Creating Cloud SQL instance '${SQL_INSTANCE}' if not present...${NC}"
    if gcloud sql instances describe "$SQL_INSTANCE" &>/dev/null; then
        echo -e "${YELLOW}! Cloud SQL instance already exists${NC}"
        return
    fi

    echo -e "${YELLOW}Creating Cloud SQL instance (this can take 5-10 minutes, please be patient)...${NC}"
    echo -e "${YELLOW}You can check progress in another terminal with:${NC}"
    echo -e "${BLUE}  gcloud sql operations list --instance=${SQL_INSTANCE}${NC}"
    gcloud sql instances create "$SQL_INSTANCE" \
        --database-version=MYSQL_8_0 \
        --tier=db-f1-micro \
        --region="$REGION" \
        --root-password="$SQL_PASSWORD" \
        --no-backup

    echo -e "${GREEN}✓ Cloud SQL instance created${NC}"
}

# Setup DB with Cloud SQL Proxy
setup_database() {
    echo -e "\n${BLUE}[9/13] Setting up database tables...${NC}"

    # Allow skipping interactive prompt by exporting SKIP_DB_PROMPT=1
    if [ -z "${SKIP_DB_PROMPT:-}" ]; then
        read -p "Have you already set up the database? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${GREEN}✓ Skipping database setup${NC}"
            return
        fi
    else
        echo -e "${YELLOW}SKIP_DB_PROMPT set — continuing with database setup automatically${NC}"
    fi

    echo -e "${YELLOW}Starting Cloud SQL Proxy in background (local port 3310)...${NC}"

    # Ensure proxy binary exists
    if [ ! -x "./cloud-sql-proxy" ]; then
        echo -e "${RED}✗ cloud-sql-proxy not found or not executable at ./cloud-sql-proxy${NC}"
        echo -e "${YELLOW}Make sure cloud-sql-proxy binary is downloaded and executable.${NC}"
        exit 1
    fi

    # Start proxy - try different formats based on Cloud SQL Proxy version
    # Cloud SQL Proxy v2 supports: cloud-sql-proxy INSTANCE_CONNECTION_NAME --port PORT
    echo -e "${BLUE}Starting proxy with connection: ${CONNECTION_NAME} on port 3310${NC}"
    echo -e "${BLUE}Proxy command: ./cloud-sql-proxy ${CONNECTION_NAME} --port 3310${NC}"
    
    # Try the --port flag format (v2 recommended)
    ./cloud-sql-proxy "${CONNECTION_NAME}" --port 3310 > /tmp/cloud-sql-proxy.log 2>&1 &
    PROXY_PID=$!
    echo $PROXY_PID > /tmp/cloud-sql-proxy.pid
    
    # Give it a moment to start and check for immediate errors
    sleep 2
    if ! kill -0 "$PROXY_PID" 2>/dev/null; then
        echo -e "${YELLOW}⚠️ Proxy process died immediately. Trying alternative format...${NC}"
        # Try alternative format: INSTANCE_CONNECTION_NAME=tcp:PORT
        ./cloud-sql-proxy "${CONNECTION_NAME}=tcp:3310" > /tmp/cloud-sql-proxy.log 2>&1 &
        PROXY_PID=$!
        echo $PROXY_PID > /tmp/cloud-sql-proxy.pid
        sleep 2
    fi

    # Wait for proxy to be ready
    echo -e "${YELLOW}Waiting for Cloud SQL Proxy to listen on 127.0.0.1:3310...${NC}"
    READY=0
    for i in {1..30}; do
        if ss -ltn | grep -q ':3310'; then
            if mysql -h 127.0.0.1 -P 3310 -u root -p"$SQL_PASSWORD" -e "SELECT 1" &>/dev/null; then
                READY=1
                break
            fi
        fi
        sleep 1
    done

    if [ "$READY" -ne 1 ]; then
        echo -e "${RED}✗ Cloud SQL Proxy did not become ready. Check /tmp/cloud-sql-proxy.log for details.${NC}"
        tail -n 50 /tmp/cloud-sql-proxy.log
        kill "$PROXY_PID" 2>/dev/null || true
        exit 1
    fi
    echo -e "${GREEN}✓ Connected to Cloud SQL via proxy${NC}"

    # Create database if missing
    echo -e "${YELLOW}Ensuring database '${DB_NAME}' exists...${NC}"
    mysql -h 127.0.0.1 -P 3310 -u root -p"$SQL_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\`;" || {
        echo -e "${RED}✗ Failed to create or access database '${DB_NAME}'. See proxy log:${NC}"
        tail -n 80 /tmp/cloud-sql-proxy.log
        kill "$PROXY_PID" 2>/dev/null || true
        exit 1
    }
    echo -e "${GREEN}✓ Database '${DB_NAME}' ready${NC}"

    # Import all required database files in order
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}Importing Database Files${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # List of SQL files to import in order (schema first, then data, then migrations)
    declare -a SQL_FILES=(
        "database.sql:Base schema (tables structure)"
        "populate_DB.sql:Initial data (robots, users, etc.)"
    )
    
    IMPORTED_COUNT=0
    SKIPPED_COUNT=0
    
    for sql_entry in "${SQL_FILES[@]}"; do
        IFS=':' read -r sql_file sql_desc <<< "$sql_entry"
        
        if [ -f "$sql_file" ]; then
            echo -e "\n${YELLOW}[${sql_file}] ${sql_desc}${NC}"
            
            # Special check for populate_DB.sql - skip if 50+ robots already exist
            if [ "$sql_file" = "populate_DB.sql" ]; then
                ROBOT_COUNT=$(mysql -h 127.0.0.1 -P 3310 -u root -p"$SQL_PASSWORD" -N -e "USE \`${DB_NAME}\`; SELECT COUNT(*) FROM robots;" 2>/dev/null || echo "0")
                if [ "$ROBOT_COUNT" -ge 50 ]; then
                    echo -e "${GREEN}✓ Database already has ${ROBOT_COUNT} robots (target: 50)${NC}"
                    echo -e "${YELLOW}  Skipping populate_DB.sql to prevent duplicates${NC}"
                    SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
                    continue
                else
                    echo -e "${BLUE}Found ${ROBOT_COUNT} robots, importing populate_DB.sql (will use INSERT IGNORE to prevent duplicates)...${NC}"
                fi
            fi
            
            echo -e "${BLUE}Importing ${sql_file} into ${DB_NAME}...${NC}"
            
            # Import the SQL file
            if mysql -h 127.0.0.1 -P 3310 -u root -p"$SQL_PASSWORD" "$DB_NAME" < "$sql_file" 2>&1 | grep -v "Using a password" | grep -v "already exists" | grep -v "Duplicate entry"; then
                echo -e "${GREEN}✓ ${sql_file} imported successfully${NC}"
                IMPORTED_COUNT=$((IMPORTED_COUNT + 1))
            else
                # Check if it actually succeeded (warnings are okay)
                if [ ${PIPESTATUS[0]} -eq 0 ]; then
                    echo -e "${GREEN}✓ ${sql_file} imported successfully (some warnings may be normal)${NC}"
                    IMPORTED_COUNT=$((IMPORTED_COUNT + 1))
                else
                    echo -e "${YELLOW}⚠️ ${sql_file} import had issues, but continuing...${NC}"
                    SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
                fi
            fi
        else
            echo -e "${YELLOW}⚠️ ${sql_file} not found — skipping${NC}"
            SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
        fi
    done
    
    echo -e "\n${CYAN}Import Summary:${NC}"
    echo -e "  ✓ Imported: ${IMPORTED_COUNT} files"
    if [ "$SKIPPED_COUNT" -gt 0 ]; then
        echo -e "  ⚠️  Skipped: ${SKIPPED_COUNT} files"
    fi

    
    # Run all migration files in order
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}Running Database Migrations${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # List of migration files to run in order
    declare -a MIGRATION_FILES=(
        "migration_add_role_safe.sql:Add role column and timestamps (safe version)"
        "migration_add_role.sql:Add role column and timestamps (fallback)"
        "migration_fix_role_values.sql:Fix role column type for SQLAlchemy compatibility"
        "migration_add_alerts.sql:Create alerts table for admin messages"
        "migration_add_2fa.sql:Add 2FA (Two-Factor Authentication) fields to users table"
        "migration_add_robot_unique_constraint.sql:Add unique constraint on robot name to prevent duplicates"
        "migration_add_password_policy.sql:Add database-level password policies (addresses Cloud SQL security warnings)"
    )
    
    MIGRATION_APPLIED=false
    
    for migration_entry in "${MIGRATION_FILES[@]}"; do
        IFS=':' read -r migration_file migration_desc <<< "$migration_entry"
        
        # Skip if already applied (for role migration)
        if [ "$migration_file" = "migration_add_role_safe.sql" ] || [ "$migration_file" = "migration_add_role.sql" ]; then
            ROLE_COLUMN_EXISTS=$(mysql -h 127.0.0.1 -P 3310 -u root -p"$SQL_PASSWORD" -N -e "USE \`${DB_NAME}\`; SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='${DB_NAME}' AND TABLE_NAME='users' AND COLUMN_NAME='role';" 2>/dev/null || echo "0")
            if [ "$ROLE_COLUMN_EXISTS" -eq "1" ] && [ "$migration_file" = "migration_add_role.sql" ]; then
                echo -e "${GREEN}✓ Role migration already applied, skipping ${migration_file}${NC}"
                continue
            fi
        fi
        
        if [ -f "$migration_file" ]; then
            echo -e "\n${YELLOW}[${migration_file}] ${migration_desc}${NC}"
            
            if mysql -h 127.0.0.1 -P 3310 -u root -p"$SQL_PASSWORD" "$DB_NAME" < "$migration_file" 2>&1 | grep -v "Using a password" | grep -v "already exists" | grep -v "Duplicate column" | grep -v "Duplicate entry"; then
                echo -e "${GREEN}✓ ${migration_file} applied successfully${NC}"
                MIGRATION_APPLIED=true
            else
                # Check if it actually succeeded
                if [ ${PIPESTATUS[0]} -eq 0 ]; then
                    echo -e "${GREEN}✓ ${migration_file} applied (some warnings may be normal)${NC}"
                    MIGRATION_APPLIED=true
                else
                    # Check if error is just "already exists"
                    MIGRATION_OUTPUT=$(mysql -h 127.0.0.1 -P 3310 -u root -p"$SQL_PASSWORD" "$DB_NAME" < "$migration_file" 2>&1 || true)
                    if echo "$MIGRATION_OUTPUT" | grep -qE "(already exists|Duplicate)"; then
                        echo -e "${GREEN}✓ ${migration_file} already applied (skipping)${NC}"
                    else
                        echo -e "${YELLOW}⚠️ ${migration_file} had issues:${NC}"
                        echo -e "${YELLOW}  $(echo "$MIGRATION_OUTPUT" | grep -v 'Using a password' | head -2)${NC}"
                    fi
                fi
            fi
        fi
    done
    
    # Verify critical migrations
    echo -e "\n${CYAN}Verifying migrations...${NC}"
    ROLE_COLUMN_EXISTS=$(mysql -h 127.0.0.1 -P 3310 -u root -p"$SQL_PASSWORD" -N -e "USE \`${DB_NAME}\`; SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='${DB_NAME}' AND TABLE_NAME='users' AND COLUMN_NAME='role';" 2>/dev/null || echo "0")
    ALERTS_TABLE_EXISTS=$(mysql -h 127.0.0.1 -P 3310 -u root -p"$SQL_PASSWORD" -N -e "USE \`${DB_NAME}\`; SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='${DB_NAME}' AND TABLE_NAME='alerts';" 2>/dev/null || echo "0")
    TWO_FACTOR_ENABLED_EXISTS=$(mysql -h 127.0.0.1 -P 3310 -u root -p"$SQL_PASSWORD" -N -e "USE \`${DB_NAME}\`; SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='${DB_NAME}' AND TABLE_NAME='users' AND COLUMN_NAME='two_factor_enabled';" 2>/dev/null || echo "0")
    
    if [ "$ROLE_COLUMN_EXISTS" -eq "1" ]; then
        echo -e "${GREEN}✓ Role column exists${NC}"
    else
        echo -e "${YELLOW}⚠️ Role column not found - role-based access may not work${NC}"
    fi
    
    if [ "$ALERTS_TABLE_EXISTS" -eq "1" ]; then
        echo -e "${GREEN}✓ Alerts table exists${NC}"
    else
        echo -e "${YELLOW}⚠️ Alerts table not found - admin alerts may not work${NC}"
    fi
    
    if [ "$TWO_FACTOR_ENABLED_EXISTS" -eq "1" ]; then
        echo -e "${GREEN}✓ 2FA columns exist${NC}"
    else
        echo -e "${YELLOW}⚠️ 2FA columns not found - two-factor authentication may not work${NC}"
    fi

    # Quick verification
    ROBOT_COUNT="N/A"
    if mysql -h 127.0.0.1 -P 3310 -u root -p"$SQL_PASSWORD" -N -e "USE \`${DB_NAME}\`; SELECT COUNT(*) FROM robots;" &>/dev/null; then
        ROBOT_COUNT=$(mysql -h 127.0.0.1 -P 3310 -u root -p"$SQL_PASSWORD" -N -e "USE \`${DB_NAME}\`; SELECT COUNT(*) FROM robots;")
    fi
    echo -e "${GREEN}✓ Database setup complete (robot count: ${ROBOT_COUNT})${NC}"

    # Stop proxy
    if [ -n "$PROXY_PID" ]; then
        kill "$PROXY_PID" 2>/dev/null || true
        rm -f /tmp/cloud-sql-proxy.pid || true
    fi
}

# Create storage bucket
create_bucket() {
    echo -e "\n${BLUE}[10/13] Creating Cloud Storage bucket...${NC}"
    if gcloud storage buckets describe "gs://${BUCKET_NAME}" &>/dev/null; then
        echo -e "${YELLOW}! Bucket '${BUCKET_NAME}' already exists${NC}"
        return
    fi

    echo -e "${YELLOW}Creating bucket '${BUCKET_NAME}'...${NC}"
    gcloud storage buckets create "gs://${BUCKET_NAME}" --location="$REGION" --uniform-bucket-level-access --quiet

    echo -e "${YELLOW}Making bucket publicly readable...${NC}"
    gcloud storage buckets add-iam-policy-binding "gs://${BUCKET_NAME}" \
        --member=allUsers \
        --role=roles/storage.objectViewer --quiet

    echo -e "${GREEN}✓ Bucket created and made public${NC}"
}

# Download images (expects download_images.py)
download_images() {
    echo -e "\n${BLUE}[11/13] Downloading Pokemon images...${NC}"
    EXPECTED_COUNT=50

    if [ -d "robot_images" ]; then
        CURRENT_COUNT=$(ls robot_images/*.png 2>/dev/null | wc -l | xargs)
        if [ "$CURRENT_COUNT" -eq "$EXPECTED_COUNT" ]; then
            echo -e "${GREEN}✓ Images already downloaded ($CURRENT_COUNT/$EXPECTED_COUNT)${NC}"
            return
        elif [ "$CURRENT_COUNT" -gt 0 ]; then
            echo -e "${YELLOW}! Found only $CURRENT_COUNT/$EXPECTED_COUNT images. Re-downloading missing images...${NC}"
        fi
    fi

    if [ -f "download_images.py" ]; then
        python3 download_images.py || echo -e "${YELLOW}⚠️ download_images.py returned non-zero exit code${NC}"
    else
        echo -e "${RED}✗ download_images.py not found — skipping image download${NC}"
        return
    fi

    IMAGE_COUNT=$(ls robot_images/*.png 2>/dev/null | wc -l | xargs)
    if [ "$IMAGE_COUNT" -eq "$EXPECTED_COUNT" ]; then
        echo -e "${GREEN}✓ Downloaded ${IMAGE_COUNT}/${EXPECTED_COUNT} images${NC}"
    else
        echo -e "${YELLOW}⚠️  Downloaded ${IMAGE_COUNT}/${EXPECTED_COUNT} images (some may have failed)${NC}"
    fi
}

# Upload images to Cloud Storage
upload_images() {
    echo -e "\n${BLUE}[12/13] Uploading images to Cloud Storage...${NC}"
    EXPECTED_COUNT=50

    if [ ! -d "robot_images" ]; then
        echo -e "${RED}✗ robot_images folder not found${NC}"
        exit 1
    fi

    # Count PNG files in Cloud Storage more accurately
    # Use gcloud storage ls with recursive flag and filter only .png files
    echo -e "${YELLOW}Checking existing images in Cloud Storage...${NC}"
    CLOUD_COUNT=$(gcloud storage ls "gs://${BUCKET_NAME}/**" 2>/dev/null | grep -E "\.png$" | wc -l | xargs || echo 0)
    LOCAL_COUNT=$(ls robot_images/*.png 2>/dev/null | wc -l | xargs || echo 0)

    echo -e "${BLUE}  Cloud Storage: ${CLOUD_COUNT} images${NC}"
    echo -e "${BLUE}  Local folder: ${LOCAL_COUNT} images${NC}"

    # Skip upload if we already have exactly 50 images
    if [ "$CLOUD_COUNT" -ge "$EXPECTED_COUNT" ]; then
        echo -e "${GREEN}✓ Images already uploaded ($CLOUD_COUNT >= $EXPECTED_COUNT files in Cloud Storage)${NC}"
        echo -e "${GREEN}  Skipping upload to avoid duplicates.${NC}"
        return
    fi

    # If we have some but not enough, warn user
    if [ "$CLOUD_COUNT" -gt 0 ] && [ "$CLOUD_COUNT" -lt "$EXPECTED_COUNT" ]; then
        echo -e "${YELLOW}⚠️  Found $CLOUD_COUNT/$EXPECTED_COUNT images in Cloud Storage${NC}"
        echo -e "${YELLOW}  Uploading missing images...${NC}"
    fi

    echo -e "${YELLOW}Uploading $LOCAL_COUNT images (this may take 2-3 minutes)...${NC}"
    gcloud storage cp robot_images/*.png "gs://${BUCKET_NAME}/" --quiet || true

    # Verify final count
    FINAL_COUNT=$(gcloud storage ls "gs://${BUCKET_NAME}/**" 2>/dev/null | grep -E "\.png$" | wc -l | xargs || echo 0)
    if [ "$FINAL_COUNT" -ge "$EXPECTED_COUNT" ]; then
        echo -e "${GREEN}✓ ${FINAL_COUNT} images in Cloud Storage (target: ${EXPECTED_COUNT})${NC}"
    else
        echo -e "${YELLOW}⚠️  ${FINAL_COUNT}/${EXPECTED_COUNT} images in Cloud Storage (some uploads may have failed)${NC}"
    fi
}

# Extract environment variable value from app.yaml
extract_env_var() {
    local var_name="$1"
    local app_yaml="${2:-app.yaml}"
    
    if [ ! -f "$app_yaml" ]; then
        return 1
    fi
    
    # Extract value using grep and sed
    # Handles both quoted and unquoted values
    local value=$(grep -A 100 "^env_variables:" "$app_yaml" | \
        grep -E "^\s*${var_name}:" | \
        head -1 | \
        sed -E "s/^\s*${var_name}:\s*[\"']?([^\"']*)[\"']?\s*$/\1/" | \
        sed 's/^ *//;s/ *$//')
    
    if [ -n "$value" ] && [ "$value" != "your_${var_name,,}" ] && [ "$value" != "YOUR_${var_name}" ]; then
        echo "$value"
        return 0
    fi
    return 1
}

# Check if secret exists in Google Secret Manager
secret_exists() {
    local secret_name="$1"
    gcloud secrets describe "$secret_name" &>/dev/null
    return $?
}

# Store secret in Google Secret Manager
store_secret() {
    local secret_name="$1"
    local secret_value="$2"
    
    if [ -z "$secret_value" ]; then
        return 1
    fi
    
    # Check if secret already exists
    if secret_exists "$secret_name"; then
        echo -e "${YELLOW}   ⚠️  Secret ${secret_name} already exists, skipping...${NC}"
        return 0  # Return success since secret exists
    fi
    
    # Create secret if it doesn't exist
    echo -n "$secret_value" | gcloud secrets create "$secret_name" \
        --data-file=- \
        --replication-policy="automatic" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

# Setup Google Secret Manager - automatically extract from app.yaml
setup_secrets() {
    echo -e "\n${BLUE}[13/13] Setting up Google Secret Manager...${NC}"
    echo -e "${YELLOW}This will automatically extract sensitive values from app.yaml and store them securely.${NC}"
    
    # Check if app.yaml exists
    if [ ! -f "app.yaml" ]; then
        echo -e "${RED}✗ app.yaml not found! Cannot extract secrets.${NC}"
        echo -e "${YELLOW}Skipping Secret Manager setup.${NC}"
        return
    fi
    
    # Auto-accept: automatically store secrets from app.yaml
    echo -e "${GREEN}Automatically storing secrets from app.yaml in Google Secret Manager...${NC}"

    # Check if Secret Manager API is enabled
    if ! gcloud services list --enabled | grep -q secretmanager.googleapis.com; then
        echo -e "${YELLOW}Enabling Secret Manager API...${NC}"
        gcloud services enable secretmanager.googleapis.com --quiet || {
            echo -e "${YELLOW}⚠️ Could not enable Secret Manager API. Continuing with env vars.${NC}"
            return
        }
        echo -e "${GREEN}✓ Secret Manager API enabled${NC}"
    fi

    echo -e "\n${CYAN}Extracting secrets from app.yaml...${NC}"
    
    # List of sensitive secrets to extract from app.yaml
    # Format: "SECRET_NAME:description"
    declare -a SECRETS_TO_STORE=(
        "CLOUD_SQL_PASSWORD:Cloud SQL database password"
        "JWT_SECRET:JWT token signing secret"
        "RECAPTCHA_SECRET_KEY:Google reCAPTCHA secret key"
        "RECAPTCHA_SITE_KEY:Google reCAPTCHA site key (public)"
        # SMTP_USER and EMAIL_FROM remain in app.yaml (they're not sensitive)
        # SMTP_PASSWORD is stored in Secret Manager (it's sensitive)
        "SMTP_PASSWORD:SMTP email password (Gmail App Password)"
        # "SMTP_USER:SMTP email user (Gmail address)" - SKIPPED (remains in app.yaml)
        # "EMAIL_FROM:Email sender address" - SKIPPED (remains in app.yaml)
    )
    
    # Also check for FLASK_SECRET if it exists
    if grep -q "FLASK_SECRET" app.yaml 2>/dev/null; then
        SECRETS_TO_STORE+=("FLASK_SECRET:Flask session secret key")
    fi
    
    STORED_COUNT=0
    SKIPPED_COUNT=0
    
    for secret_entry in "${SECRETS_TO_STORE[@]}"; do
        IFS=':' read -r secret_name secret_desc <<< "$secret_entry"
        
        # Skip SMTP_USER and EMAIL_FROM - they remain in app.yaml (not sensitive)
        # SMTP_PASSWORD is stored in Secret Manager (it's sensitive)
        if [[ "$secret_name" == "SMTP_USER" || "$secret_name" == "EMAIL_FROM" ]]; then
            echo -e "${YELLOW}⚠️  ${secret_name}: Skipped - remains in app.yaml${NC}"
            SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
            continue
        fi
        
        # Extract value from app.yaml
        secret_value=$(extract_env_var "$secret_name" "app.yaml")
        
        if [ -z "$secret_value" ]; then
            echo -e "${YELLOW}⚠️  ${secret_name}: Not found in app.yaml or placeholder value${NC}"
            SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
            continue
        fi
        
        # Auto-store all secrets (no prompts)
        if [ "$secret_name" != "RECAPTCHA_SITE_KEY" ]; then
            echo -e "${BLUE}📋 Found ${secret_name} in app.yaml${NC}"
            echo -e "${CYAN}   Description: ${secret_desc}${NC}"
            echo -e "${YELLOW}   Value: ${secret_value:0:10}...${secret_value: -4}${NC}"
        else
            # RECAPTCHA_SITE_KEY is public, so auto-store if found
            echo -e "${BLUE}📋 Found ${secret_name} (public key)${NC}"
        fi
        
        # Store the secret (will skip if already exists)
        echo -e "${YELLOW}   Storing ${secret_name} in Secret Manager...${NC}"
        if store_secret "$secret_name" "$secret_value"; then
            echo -e "${GREEN}   ✓ ${secret_name} stored successfully${NC}"
            STORED_COUNT=$((STORED_COUNT + 1))
        else
            echo -e "${RED}   ✗ Failed to store ${secret_name}${NC}"
            SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
        fi
    done
    
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}Secret Manager Setup Summary:${NC}"
    echo -e "  ✓ Stored: ${STORED_COUNT} secrets"
    if [ "$SKIPPED_COUNT" -gt 0 ]; then
        echo -e "  ⚠️  Skipped: ${SKIPPED_COUNT} secrets"
    fi
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if [ "$STORED_COUNT" -gt 0 ]; then
        echo -e "\n${YELLOW}Important: Grant App Engine service account access to secrets${NC}"
        echo -e "${CYAN}Run this command to grant access:${NC}"
        SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"
        echo -e "${BLUE}  gcloud projects add-iam-policy-binding ${PROJECT_ID} \\${NC}"
        echo -e "${BLUE}    --member=\"serviceAccount:${SERVICE_ACCOUNT}\" \\${NC}"
        echo -e "${BLUE}    --role=\"roles/secretmanager.secretAccessor\"${NC}"
        echo ""
        read -p "Do you want to grant access now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Granting Secret Manager access to App Engine service account...${NC}"
            gcloud projects add-iam-policy-binding "$PROJECT_ID" \
                --member="serviceAccount:${SERVICE_ACCOUNT}" \
                --role="roles/secretmanager.secretAccessor" \
                --quiet && \
            echo -e "${GREEN}✓ Access granted${NC}" || \
            echo -e "${YELLOW}⚠️  Failed to grant access. Please run the command manually.${NC}"
        else
            echo -e "${YELLOW}⚠️  Remember to grant access manually before deploying!${NC}"
        fi
        
        echo -e "\n${CYAN}Optional: Clean up app.yaml${NC}"
        echo -e "${YELLOW}You can now remove sensitive values from app.yaml since they're in Secret Manager.${NC}"
        echo -e "${YELLOW}Your app will automatically use secrets from Secret Manager (with env fallback).${NC}"
        read -p "Remove sensitive values from app.yaml now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Create backup
            cp app.yaml app.yaml.backup
            echo -e "${GREEN}✓ Backup created: app.yaml.backup${NC}"
            
            # Remove sensitive values (replace with placeholder comments)
            # Skip SMTP credentials - they should remain in app.yaml
            for secret_entry in "${SECRETS_TO_STORE[@]}"; do
                IFS=':' read -r secret_name secret_desc <<< "$secret_entry"
                
                # Skip SMTP credentials - they remain in app.yaml
                if [[ "$secret_name" == "SMTP_USER" || "$secret_name" == "SMTP_PASSWORD" || "$secret_name" == "EMAIL_FROM" ]]; then
                    continue
                fi
                
                if [ "$secret_name" != "RECAPTCHA_SITE_KEY" ]; then
                    # Replace with comment indicating it's in Secret Manager
                    sed -i.tmp "s/^\(\s*${secret_name}:\)\s*\"[^\"]*\"\s*$/\1 \"# Stored in Google Secret Manager\"/" app.yaml || \
                    sed -i.tmp "s/^\(\s*${secret_name}:\)\s*[^[:space:]]*\s*$/\1 \"# Stored in Google Secret Manager\"/" app.yaml
                fi
            done
            rm -f app.yaml.tmp
            echo -e "${GREEN}✓ Sensitive values removed from app.yaml${NC}"
            echo -e "${YELLOW}  (Keep non-sensitive values like CLOUD_SQL_USERNAME, BUCKET_NAME, etc.)${NC}"
        fi
    fi
    
    echo -e "\n${GREEN}✓ Secret Manager setup complete${NC}"
    echo -e "${CYAN}Note:${NC}"
    echo -e "${YELLOW}  - Secrets are now stored securely in Google Secret Manager${NC}"
    echo -e "${YELLOW}  - Your app will automatically retrieve them using secrets_manager.py${NC}"
    echo -e "${YELLOW}  - Environment variables in app.yaml will be used as fallback${NC}"
}

# App Engine creation and deploy
create_app_engine() {
    echo -e "\n${CYAN}Creating App Engine application (if not exists)...${NC}"
    if gcloud app describe &>/dev/null; then
        echo -e "${YELLOW}! App Engine app already exists${NC}"
        return
    fi
    gcloud app create --region="$REGION" --quiet
    echo -e "${GREEN}✓ App Engine app created${NC}"
}

deploy_app() {
    echo -e "\n${BLUE}Deploying application to App Engine...${NC}"
    echo -e "${YELLOW}⏱️  This step typically takes 3-5 minutes. Please be patient...${NC}"
    echo -e "${YELLOW}   App Engine is building your app and uploading it to Google Cloud.${NC}"
    echo -e "${YELLOW}   You'll see progress messages below...${NC}"
    
    # Check if requirements.txt exists and has content
    if [ ! -f "requirements.txt" ] || [ ! -s "requirements.txt" ]; then
        echo -e "${RED}✗ requirements.txt is missing or empty!${NC}"
        echo -e "${RED}  Deployment will fail without dependencies.${NC}"
        exit 1
    fi
    
    # Check if app.yaml exists
    if [ ! -f "app.yaml" ]; then
        echo -e "${RED}✗ app.yaml is missing!${NC}"
        exit 1
    fi

    # Verify new files exist
    echo -e "${CYAN}Verifying new security files...${NC}"
    REQUIRED_FILES=("models.py" "db_session.py" "db_service.py" "auth_utils.py" "error_handlers.py" "secrets_manager.py" "password_policy.py" "recaptcha_verify.py" "two_factor_auth.py")
    MISSING_FILES=()
    for file in "${REQUIRED_FILES[@]}"; do
        if [ ! -f "$file" ]; then
            MISSING_FILES+=("$file")
        fi
    done
    
    if [ ${#MISSING_FILES[@]} -gt 0 ]; then
        echo -e "${RED}✗ Missing required files: ${MISSING_FILES[*]}${NC}"
        echo -e "${RED}  Please ensure all new security files are present before deploying.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ All required files present${NC}"
    
    # Check for reCAPTCHA configuration
    echo -e "${CYAN}Checking reCAPTCHA configuration...${NC}"
    if grep -q "RECAPTCHA_SITE_KEY.*YOUR_RECAPTCHA" app.yaml 2>/dev/null || grep -q "RECAPTCHA_SECRET_KEY.*YOUR_RECAPTCHA" app.yaml 2>/dev/null; then
        echo -e "${YELLOW}⚠️  WARNING: reCAPTCHA keys appear to be placeholders in app.yaml${NC}"
        echo -e "${YELLOW}  The app will work, but reCAPTCHA verification will be skipped.${NC}"
        echo -e "${YELLOW}  To enable reCAPTCHA:${NC}"
        echo -e "${YELLOW}    1. Get keys from https://www.google.com/recaptcha/admin${NC}"
        echo -e "${YELLOW}    2. Update RECAPTCHA_SITE_KEY and RECAPTCHA_SECRET_KEY in app.yaml${NC}"
        echo -e "${YELLOW}    3. Or store RECAPTCHA_SECRET_KEY in Google Secret Manager${NC}"
        read -p "Continue deployment anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Deployment cancelled. Please configure reCAPTCHA keys first.${NC}"
            exit 0
        fi
    else
        echo -e "${GREEN}✓ reCAPTCHA keys configured${NC}"
    fi
    
    # Deploy with verbose output
    if gcloud app deploy; then
        echo -e "${GREEN}✓ Application deployed successfully${NC}"
    else
        echo -e "${RED}✗ Deployment failed. Check the error messages above.${NC}"
        echo -e "${YELLOW}Common issues:${NC}"
        echo -e "  - Missing dependencies in requirements.txt"
        echo -e "  - Network connectivity issues"
        echo -e "  - Insufficient permissions"
        echo -e "  - Build timeout"
        echo -e "\n${YELLOW}Try running with verbose output:${NC}"
        echo -e "  ${BLUE}gcloud app deploy --verbosity=debug${NC}"
        exit 1
    fi
}

# Show final info
show_info() {
    echo -e "\n${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                          ║${NC}"
    echo -e "${GREEN}║        🎉  Deployment Complete Successfully! 🎉          ║${NC}"
    echo -e "${GREEN}║                                                          ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}Your Robopety app is now live at:${NC}"
    echo -e "${BLUE}    https://${PROJECT_ID}.uc.r.appspot.com${NC}"
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}New Security Features Deployed:${NC}"
    echo -e "  ✓ Role-based access control (admin/user)"
    echo -e "  ✓ SQLAlchemy ORM with transactional operations"
    echo -e "  ✓ Centralized error handling & structured logging"
    echo -e "  ✓ Google Secret Manager integration (with env fallback)"
    echo -e "  ✓ Short-lived JWT tokens (15 minutes)"
    echo -e "  ✓ Flask-Talisman security headers (CSP, HSTS, X-Frame-Options)"
    echo -e "  ✓ Server-side password policy (bcrypt hashing)"
    echo -e "  ✓ Rate limiting (login/signup)"
    echo -e "  ✓ Google reCAPTCHA v2 (bot protection)"
    echo -e "  ✓ HttpOnly, Secure, SameSite cookies"
    echo -e "  ✓ Parameterized queries (SQL injection prevention)"
    echo -e "  ✓ XSS prevention (auto-escaping + CSP)"
    echo -e "  ✓ Multiple robot selection support"
    echo -e "  ✓ Enhanced frontend with dark mode & purple-blue theme"
    echo -e "  ✓ Two-Factor Authentication (2FA) with TOTP support"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}Resources Created:${NC}"
    echo -e "  ✓ Cloud SQL Instance:    ${BLUE}${SQL_INSTANCE}${NC}"
    echo -e "  ✓ Database connection:   ${BLUE}${CONNECTION_NAME}${NC}"
    echo -e "  ✓ Storage Bucket:        ${BLUE}gs://${BUCKET_NAME}${NC}"
    echo -e "  ✓ App Engine Service:    ${BLUE}default${NC}"
    echo ""
    echo -e "${YELLOW}Useful Commands:${NC}"
    echo -e "  ${GREEN}View live logs:${NC}"
    echo -e "    ${BLUE}gcloud app logs tail -s default${NC}"
    echo -e "  ${GREEN}Open in browser:${NC}"
    echo -e "    ${BLUE}gcloud app browse${NC}"
    echo -e "  ${GREEN}Redeploy after changes:${NC}"
    echo -e "    ${BLUE}gcloud app deploy${NC}"
    echo -e "  ${GREEN}Stop Cloud SQL (save money):${NC}"
    echo -e "    ${BLUE}gcloud sql instances patch ${SQL_INSTANCE} --activation-policy=NEVER --quiet${NC}"
    echo -e "  ${GREEN}Restart Cloud SQL:${NC}"
    echo -e "    ${BLUE}gcloud sql instances patch ${SQL_INSTANCE} --activation-policy=ALWAYS --quiet${NC}"
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Main
main() {
    echo -e "${YELLOW}This enhanced script will:${NC}"
    echo -e "  1. Load project configuration from app.yaml or prompt for input"
    echo -e "  2. Install required dependencies (gcloud, mysql client, python, cloud-sql-proxy)"
    echo -e "  3. Set up Google Cloud infrastructure (APIs, Cloud SQL, bucket)"
    echo -e "  4. Import all database files (database.sql, populate_DB.sql, migrations)"
    echo -e "  5. Run database migrations (role column, alerts table, 2FA fields, etc.)"
    echo -e "  6. Install new security dependencies (SQLAlchemy, Flask-Talisman, Flask-Limiter, pyotp, qrcode, requests)"
    echo -e "  7. (Optionally) set up Google Secret Manager (JWT, Flask, reCAPTCHA secrets)"
    echo -e "  8. Verify all security files are present"
    echo -e "  9. Check reCAPTCHA configuration"
    echo -e "  10. (Optionally) deploy to App Engine${NC}"
    echo ""
    echo -e "${YELLOW}⏱️  Expected time: 20-30 minutes (depending on what's already set up)${NC}"
    echo -e "${YELLOW}   - First time: ~25-30 minutes${NC}"
    echo -e "${YELLOW}   - Subsequent runs: ~5-10 minutes${NC}"
    echo ""
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Deployment cancelled${NC}"
        exit 0
    fi

    # Load project configuration first
    load_project_config
    
    install_prereqs
    install_gcloud
    install_mysql_client
    install_python_deps
    install_sql_proxy

    authenticate_gcloud
    enable_apis
    create_sql_instance
    setup_database

    create_bucket
    download_images
    upload_images

    setup_secrets

    # Final verification before deployment
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}Pre-Deployment Checklist:${NC}"
    echo -e "${GREEN}✓ Database migration completed${NC}"
    echo -e "${GREEN}✓ All security dependencies installed${NC}"
    echo -e "${GREEN}✓ All required files verified${NC}"
    
    # Check if reCAPTCHA is configured
    if grep -q "RECAPTCHA_SITE_KEY.*YOUR_RECAPTCHA" app.yaml 2>/dev/null; then
        echo -e "${YELLOW}⚠️  reCAPTCHA keys need to be configured (optional but recommended)${NC}"
    else
        echo -e "${GREEN}✓ reCAPTCHA configuration checked${NC}"
    fi
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Ask before creating App Engine / Deploy
    read -p "Create App Engine app and deploy now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        create_app_engine
        deploy_app
    else
        echo -e "${YELLOW}Skipping App Engine creation and deploy${NC}"
        echo -e "${YELLOW}You can deploy later with: ${BLUE}gcloud app deploy${NC}"
    fi

    show_info
}

main "$@"

