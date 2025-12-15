# Blue Team Migration Script for Windows PowerShell

Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║        Run Blue Team Migration Script                   ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

# Configuration
$DB_CONNECTION_NAME = "csci0220-472715:us-central1:robo"
$DB_USER = "root"
$DB_PASSWORD = "your_password_here"  # Update this with your password from app.yaml
$DB_NAME = "ROBOPETY"
$PROXY_PORT = 3310

Write-Host "Configuration:"
Write-Host "  Connection: $DB_CONNECTION_NAME"
Write-Host "  Port: $PROXY_PORT"
Write-Host "  Database: $DB_NAME"
Write-Host ""

# Check if Cloud SQL Proxy is running
$proxyRunning = Get-NetTCPConnection -LocalPort $PROXY_PORT -ErrorAction SilentlyContinue

if (-not $proxyRunning) {
    Write-Host "⚠ Cloud SQL Proxy is not running on port $PROXY_PORT" -ForegroundColor Yellow
    Write-Host "Please start it manually:" -ForegroundColor Yellow
    Write-Host "  cloud-sql-proxy $DB_CONNECTION_NAME --port=$PROXY_PORT" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Then run this script again." -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "✓ Cloud SQL Proxy is already running on port $PROXY_PORT" -ForegroundColor Green
}

# Test database connection
Write-Host ""
Write-Host "Testing database connection..."

# Read the SQL file
$sqlFile = "migration_add_blue_team_role.sql"
if (-not (Test-Path $sqlFile)) {
    Write-Host "✗ Migration file not found: $sqlFile" -ForegroundColor Red
    exit 1
}

$sqlContent = Get-Content $sqlFile -Raw

# Run the migration using mysql command
Write-Host ""
Write-Host "Running Blue Team migration..."
Write-Host ""

# Note: You'll need mysql client installed or use WSL
# For Windows, you can use WSL to run mysql
Write-Host "To run the migration, use one of these methods:" -ForegroundColor Yellow
Write-Host ""
Write-Host "Method 1: Using WSL (Recommended)" -ForegroundColor Cyan
Write-Host "  wsl bash -c 'mysql -h 127.0.0.1 -P $PROXY_PORT -u $DB_USER -p`"$DB_PASSWORD`" $DB_NAME < migration_add_blue_team_role.sql'" -ForegroundColor White
Write-Host ""
Write-Host "Method 2: Using MySQL Workbench or other GUI tool" -ForegroundColor Cyan
Write-Host "  Connect to: 127.0.0.1:$PROXY_PORT" -ForegroundColor White
Write-Host "  Database: $DB_NAME" -ForegroundColor White
Write-Host "  Then run the SQL from: migration_add_blue_team_role.sql" -ForegroundColor White
Write-Host ""

# Verify migration
Write-Host "After running the migration, verify it worked:" -ForegroundColor Yellow
Write-Host "  Check if security_events table exists" -ForegroundColor White
Write-Host "  Check if blue_team is in the role enum" -ForegroundColor White
Write-Host ""

Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  Next Steps:                                            ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host "  1. Run the SQL migration (see methods above)" -ForegroundColor White
Write-Host "  2. Deploy your application" -ForegroundColor White
Write-Host "  3. As admin, grant Blue Team access to users" -ForegroundColor White
Write-Host ""

