# PowerShell script to run role enum case fix migration
# This ensures all role values in the database are lowercase

$PROXY_PORT = 3310
$SQL_PASSWORD = "-6uB+6(7_bHPGmGupolivoliv67"
$DB_NAME = "ROBOPETY"
$CONNECTION_NAME = "csci0220-472715:us-central1:robo"

Write-Host "Running role enum case fix migration..." -ForegroundColor Blue
Write-Host ""

# Check if cloud-sql-proxy.exe exists
if (-not (Test-Path "cloud-sql-proxy.exe")) {
    Write-Host "cloud-sql-proxy.exe not found!" -ForegroundColor Red
    Write-Host "Please download it from: https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.x64.exe" -ForegroundColor Yellow
    exit 1
}

# Stop any existing proxy on this port
$existingProxy = Get-Process | Where-Object { $_.ProcessName -like "*cloud-sql-proxy*" }
if ($existingProxy) {
    Write-Host "Stopping existing cloud-sql-proxy processes..." -ForegroundColor Yellow
    $existingProxy | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Start proxy
Write-Host "Starting Cloud SQL Proxy on port ${PROXY_PORT}..." -ForegroundColor Yellow
$proxyJob = Start-Process -FilePath ".\cloud-sql-proxy.exe" -ArgumentList "${CONNECTION_NAME}", "--port", "${PROXY_PORT}" -PassThru -NoNewWindow -RedirectStandardOutput "proxy.log" -RedirectStandardError "proxy-error.log"
Start-Sleep -Seconds 3

Write-Host "Waiting for proxy to connect..." -ForegroundColor Yellow
$connected = $false
for ($i = 1; $i -le 30; $i++) {
    try {
        $result = mysql -h 127.0.0.1 -P $PROXY_PORT -u root -p"$SQL_PASSWORD" -e "SELECT 1" 2>&1 | Out-String
        if ($LASTEXITCODE -eq 0) {
            $connected = $true
            Write-Host "Connected to Cloud SQL" -ForegroundColor Green
            break
        }
    } catch {
        # Continue waiting
    }
    Start-Sleep -Seconds 1
}

if (-not $connected) {
    Write-Host "Failed to connect. Check proxy logs." -ForegroundColor Red
    Stop-Process -Id $proxyJob.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# Run migration
Write-Host ""
Write-Host "Running migration..." -ForegroundColor Yellow
$migrationFile = "migration_fix_role_enum_case.sql"
if (-not (Test-Path $migrationFile)) {
    Write-Host "Migration file not found: $migrationFile" -ForegroundColor Red
    Stop-Process -Id $proxyJob.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# Read and execute migration
Get-Content $migrationFile | mysql -h 127.0.0.1 -P $PROXY_PORT -u root -p"$SQL_PASSWORD" $DB_NAME

Write-Host ""
Write-Host "Verifying roles..." -ForegroundColor Yellow
mysql -h 127.0.0.1 -P $PROXY_PORT -u root -p"$SQL_PASSWORD" $DB_NAME -e "SELECT DISTINCT role FROM users;"

# Stop proxy
Write-Host ""
Write-Host "Stopping proxy..." -ForegroundColor Yellow
Stop-Process -Id $proxyJob.Id -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

Write-Host ""
Write-Host "Migration complete!" -ForegroundColor Green
Write-Host ""
