# Operations Manual
**Project:** IoT Data Integration Platform  
**Developer:** Andrew Mathers  
**Version:** 1.0  
**Date:** November 2024  

---

## Table of Contents
1. [Deployment Guide](#deployment-guide)
2. [Configuration Management](#configuration-management)
3. [Running the Pipeline](#running-the-pipeline)
4. [Monitoring and Alerting](#monitoring-and-alerting)
5. [Troubleshooting](#troubleshooting)
6. [Backup and Recovery](#backup-and-recovery)
7. [Performance Tuning](#performance-tuning)
8. [Security Operations](#security-operations)

---

## Deployment Guide

### Prerequisites Checklist

#### System Requirements
- [ ] Operating System: Linux (Ubuntu 20.04+), macOS (10.15+), or Windows Server 2019+
- [ ] Python 3.8 or higher installed
- [ ] Python pip and virtualenv installed
- [ ] Microsoft SQL Server 2016+ or Azure SQL Database
- [ ] ODBC Driver 17 or 18 for SQL Server
- [ ] Network connectivity to api.thingspeak.com (HTTPS outbound)
- [ ] Network connectivity to SQL Server (port 1433 or custom)

#### Account Requirements
- [ ] ThingSpeak account (optional, for private channels)
- [ ] SQL Server database with admin access
- [ ] Server or VM with at least 2 GB RAM, 10 GB disk

### Step-by-Step Deployment

#### 1. Install ODBC Driver

**macOS:**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Microsoft ODBC driver
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
brew install msodbcsql18

# Verify installation
odbcinst -q -d | grep "ODBC Driver"
```

**Linux (Ubuntu/Debian):**
```bash
# Add Microsoft package repository
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | \
    sudo tee /etc/apt/sources.list.d/mssql-release.list

# Install ODBC driver
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql18

# Install unixODBC development headers
sudo apt-get install -y unixodbc-dev

# Verify installation
odbcinst -q -d | grep "ODBC Driver"
```

**Windows:**
1. Download ODBC Driver 18 from: https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
2. Run the installer (msodbcsql.msi)
3. Verify in ODBC Data Source Administrator (odbcad32.exe)

#### 2. Clone Repository and Setup

```bash
# Clone the repository
cd /opt  # or your preferred installation directory
git clone <repository-url> iot-api-mssql-integration
cd iot-api-mssql-integration

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Verify installations
python -c "import pyodbc; print('pyodbc:', pyodbc.version)"
python -c "import requests; print('requests:', requests.__version__)"
python -c "import dotenv; print('python-dotenv installed')"
```

#### 3. Database Setup

```bash
# Option A: Using sqlcmd (if available)
sqlcmd -S your_server -U sa -P 'YourPassword' -i sql/01_create_schema.sql
sqlcmd -S your_server -U sa -P 'YourPassword' -i sql/02_create_stored_procedures.sql

# Option B: Using Azure Data Studio or SSMS
# 1. Open Azure Data Studio or SQL Server Management Studio
# 2. Connect to your SQL Server instance
# 3. Open sql/01_create_schema.sql
# 4. Execute the script
# 5. Open sql/02_create_stored_procedures.sql
# 6. Execute the script

# Verify database setup
sqlcmd -S your_server -U sa -P 'YourPassword' -d IoTSensorDB -Q \
  "SELECT name FROM sys.tables WHERE schema_id = SCHEMA_ID('iot')"
# Expected output: Channels, SensorReadings, AggregatedData, DataQuality

# Verify stored procedures
sqlcmd -S your_server -U sa -P 'YourPassword' -d IoTSensorDB -Q \
  "SELECT name FROM sys.procedures WHERE schema_id = SCHEMA_ID('iot')"
# Expected output: usp_ProcessSensorReadings, usp_DetectAnomalies, 
#                  usp_CalculateDataQuality, usp_GetTrendAnalysis
```

#### 4. Configuration

```bash
# Create .env file from template
cp .env.example .env

# Edit .env file with your configuration
nano .env  # or vim, emacs, etc.
```

**Example .env configuration:**
```env
# ThingSpeak Configuration
THINGSPEAK_CHANNEL_ID=9
THINGSPEAK_API_KEY=

# Database Configuration (SQL Authentication)
DB_SERVER=localhost
DB_NAME=IoTSensorDB
DB_USERNAME=iot_pipeline_user
DB_PASSWORD=SecurePassword123!
DB_TRUSTED_CONNECTION=False

# OR for Windows Authentication:
# DB_SERVER=localhost
# DB_NAME=IoTSensorDB
# DB_TRUSTED_CONNECTION=True
# (DB_USERNAME and DB_PASSWORD not needed)
```

**Secure the .env file:**
```bash
chmod 600 .env  # Linux/macOS: Read/write for owner only
```

#### 5. Test Installation

```bash
# Test database connectivity
python -c "
from src.database import DatabaseConnection
import os
from dotenv import load_dotenv

load_dotenv()
db = DatabaseConnection(
    server=os.getenv('DB_SERVER'),
    database=os.getenv('DB_NAME'),
    username=os.getenv('DB_USERNAME'),
    password=os.getenv('DB_PASSWORD'),
    trusted_connection=os.getenv('DB_TRUSTED_CONNECTION', 'False').lower() == 'true'
)
if db.connect():
    print('✓ Database connection successful')
    db.disconnect()
else:
    print('✗ Database connection failed')
"

# Test ThingSpeak API connectivity
python -c "
from src.thingspeak_client import ThingSpeakClient
import os
from dotenv import load_dotenv

load_dotenv()
client = ThingSpeakClient(channel_id=os.getenv('THINGSPEAK_CHANNEL_ID'))
info = client.get_channel_info()
if info:
    print(f\"✓ ThingSpeak API working: Channel '{info.get('name')}'\" )
else:
    print('✗ ThingSpeak API failed')
"

# Run a test pipeline execution
python src/pipeline.py
# Expected output: Logs showing successful execution
```

---

## Configuration Management

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `THINGSPEAK_CHANNEL_ID` | ✓ | - | ThingSpeak channel ID to fetch data from |
| `THINGSPEAK_API_KEY` | ✗ | Empty | API key for private channels |
| `DB_SERVER` | ✓ | - | SQL Server hostname or IP |
| `DB_NAME` | ✓ | IoTSensorDB | Database name |
| `DB_USERNAME` | ✓* | - | SQL authentication username (*if not using trusted connection) |
| `DB_PASSWORD` | ✓* | - | SQL authentication password (*if not using trusted connection) |
| `DB_TRUSTED_CONNECTION` | ✗ | False | Use Windows authentication (True/False) |

### Configuration Validation

Create a validation script `/opt/iot-api-mssql-integration/scripts/validate_config.py`:

```python
#!/usr/bin/env python3
"""Configuration validation script"""
import os
import sys
from dotenv import load_dotenv

def validate_config():
    load_dotenv()
    
    errors = []
    warnings = []
    
    # Required for all configurations
    if not os.getenv('THINGSPEAK_CHANNEL_ID'):
        errors.append('THINGSPEAK_CHANNEL_ID is required')
    
    if not os.getenv('DB_SERVER'):
        errors.append('DB_SERVER is required')
    
    if not os.getenv('DB_NAME'):
        errors.append('DB_NAME is required')
    
    # Check authentication method
    trusted_conn = os.getenv('DB_TRUSTED_CONNECTION', 'False').lower() == 'true'
    
    if not trusted_conn:
        if not os.getenv('DB_USERNAME'):
            errors.append('DB_USERNAME is required (or set DB_TRUSTED_CONNECTION=True)')
        if not os.getenv('DB_PASSWORD'):
            errors.append('DB_PASSWORD is required (or set DB_TRUSTED_CONNECTION=True)')
    
    # Warnings
    if not os.getenv('THINGSPEAK_API_KEY'):
        warnings.append('THINGSPEAK_API_KEY not set (only works with public channels)')
    
    # Print results
    if errors:
        print('❌ Configuration Errors:')
        for error in errors:
            print(f'  - {error}')
    
    if warnings:
        print('⚠️  Configuration Warnings:')
        for warning in warnings:
            print(f'  - {warning}')
    
    if not errors and not warnings:
        print('✅ Configuration is valid')
    
    return len(errors) == 0

if __name__ == '__main__':
    sys.exit(0 if validate_config() else 1)
```

Run validation:
```bash
chmod +x scripts/validate_config.py
python scripts/validate_config.py
```

### Managing Multiple Environments

**Development, Staging, Production:**

```bash
# Create environment-specific config files
cp .env .env.development
cp .env .env.staging
cp .env .env.production

# Edit each file with environment-specific values

# Use with environment variable
export ENV=production
python -c "from dotenv import load_dotenv; load_dotenv('.env.${ENV}')"
```

---

## Running the Pipeline

### Manual Execution

**Basic run (fetch 100 records):**
```bash
cd /opt/iot-api-mssql-integration
source venv/bin/activate
python src/pipeline.py
```

**With custom record count:**
```bash
python -c "from src.pipeline import IoTDataPipeline; IoTDataPipeline().run_full_pipeline(fetch_results=500)"
```

### Scheduled Execution

#### Cron (Linux/macOS)

**Edit crontab:**
```bash
crontab -e
```

**Hourly execution:**
```cron
# Run IoT pipeline every hour at minute 5
5 * * * * cd /opt/iot-api-mssql-integration && /opt/iot-api-mssql-integration/venv/bin/python src/pipeline.py >> /var/log/iot-pipeline.log 2>&1
```

**Every 15 minutes:**
```cron
# Run IoT pipeline every 15 minutes
*/15 * * * * cd /opt/iot-api-mssql-integration && /opt/iot-api-mssql-integration/venv/bin/python src/pipeline.py >> /var/log/iot-pipeline.log 2>&1
```

**Daily at 3 AM:**
```cron
# Run IoT pipeline daily at 3:00 AM
0 3 * * * cd /opt/iot-api-mssql-integration && /opt/iot-api-mssql-integration/venv/bin/python src/pipeline.py >> /var/log/iot-pipeline.log 2>&1
```

**Setup log rotation:**
```bash
sudo nano /etc/logrotate.d/iot-pipeline
```

```
/var/log/iot-pipeline.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 ubuntu ubuntu
}
```

#### Systemd Service (Linux)

**Create service file:**
```bash
sudo nano /etc/systemd/system/iot-pipeline.service
```

```ini
[Unit]
Description=IoT Data Integration Pipeline
After=network.target mssql-server.service

[Service]
Type=oneshot
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/iot-api-mssql-integration
Environment="PATH=/opt/iot-api-mssql-integration/venv/bin"
ExecStart=/opt/iot-api-mssql-integration/venv/bin/python src/pipeline.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Create timer:**
```bash
sudo nano /etc/systemd/system/iot-pipeline.timer
```

```ini
[Unit]
Description=Run IoT Pipeline Hourly
Requires=iot-pipeline.service

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable iot-pipeline.timer
sudo systemctl start iot-pipeline.timer

# Check status
sudo systemctl status iot-pipeline.timer
sudo systemctl list-timers iot-pipeline.timer

# View logs
sudo journalctl -u iot-pipeline.service -f
```

#### Windows Task Scheduler

**Create batch script `run_pipeline.bat`:**
```batch
@echo off
cd /d C:\iot-api-mssql-integration
call venv\Scripts\activate
python src\pipeline.py >> logs\pipeline.log 2>&1
```

**PowerShell command to create scheduled task:**
```powershell
$action = New-ScheduledTaskAction -Execute "C:\iot-api-mssql-integration\run_pipeline.bat"
$trigger = New-ScheduledTaskTrigger -Daily -At "3:00AM"
$principal = New-ScheduledTaskPrincipal -UserId "NT AUTHORITY\SYSTEM" -LogonType ServiceAccount
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable

Register-ScheduledTask -TaskName "IoT Data Pipeline" `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Description "Hourly execution of IoT data integration pipeline"
```

---

## Monitoring and Alerting

### Log Monitoring

**View real-time logs:**
```bash
# Cron logs
tail -f /var/log/iot-pipeline.log

# Systemd logs
sudo journalctl -u iot-pipeline.service -f

# Filter by log level
grep ERROR /var/log/iot-pipeline.log
grep WARNING /var/log/iot-pipeline.log
```

**Log Analysis Script:**
```bash
#!/bin/bash
# analyze_logs.sh - Analyze pipeline logs

LOG_FILE="/var/log/iot-pipeline.log"
HOURS=${1:-24}  # Default: last 24 hours

echo "=== Pipeline Log Analysis (Last $HOURS hours) ==="
echo ""

# Count successful runs
echo "Successful runs:"
grep -c "Pipeline completed successfully" "$LOG_FILE"

# Count errors
echo "Total errors:"
grep -c "ERROR" "$LOG_FILE"

# Recent errors
echo ""
echo "Recent errors:"
grep "ERROR" "$LOG_FILE" | tail -n 10

# Records inserted
echo ""
echo "Records inserted (last 10 runs):"
grep "Inserted.*sensor readings" "$LOG_FILE" | tail -n 10

# Data quality scores
echo ""
echo "Data quality scores (last 10 runs):"
grep "QualityScore" "$LOG_FILE" | tail -n 10
```

### Health Checks

**Create health check script `/opt/iot-api-mssql-integration/scripts/health_check.py`:**
```python
#!/usr/bin/env python3
"""Health check script for monitoring systems"""
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from src.database import DatabaseConnection

def check_last_data_import():
    """Check if data was imported in the last 2 hours"""
    load_dotenv()
    
    db = DatabaseConnection(
        server=os.getenv('DB_SERVER'),
        database=os.getenv('DB_NAME'),
        username=os.getenv('DB_USERNAME'),
        password=os.getenv('DB_PASSWORD'),
        trusted_connection=os.getenv('DB_TRUSTED_CONNECTION', 'False').lower() == 'true'
    )
    
    if not db.connect():
        print('CRITICAL: Cannot connect to database')
        return False
    
    try:
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT TOP 1 ImportedAt 
            FROM iot.SensorReadings 
            ORDER BY ImportedAt DESC
        """)
        row = cursor.fetchone()
        
        if not row:
            print('WARNING: No data found in database')
            return False
        
        last_import = row[0]
        age = datetime.utcnow() - last_import
        
        if age > timedelta(hours=2):
            print(f'WARNING: Last import was {age.total_seconds()/3600:.1f} hours ago')
            return False
        else:
            print(f'OK: Last import was {age.total_seconds()/60:.0f} minutes ago')
            return True
    finally:
        db.disconnect()

if __name__ == '__main__':
    sys.exit(0 if check_last_data_import() else 1)
```

**Integrate with monitoring systems:**
```bash
# Nagios/Icinga check
*/5 * * * * /opt/iot-api-mssql-integration/scripts/health_check.py

# Or with alerting
*/5 * * * * /opt/iot-api-mssql-integration/scripts/health_check.py || \
    mail -s "IoT Pipeline Health Check Failed" admin@example.com
```

### Database Monitoring Queries

**Check recent data imports:**
```sql
-- Records imported in last 24 hours
SELECT 
    CAST(ImportedAt AS DATE) AS ImportDate,
    COUNT(*) AS RecordCount
FROM iot.SensorReadings
WHERE ImportedAt >= DATEADD(HOUR, -24, GETUTCDATE())
GROUP BY CAST(ImportedAt AS DATE)
ORDER BY ImportDate DESC;
```

**Check data quality trends:**
```sql
-- Data quality over last 7 days
SELECT 
    CheckDate,
    TotalReadings,
    MissingReadings,
    QualityScore
FROM iot.DataQuality
WHERE CheckDate >= DATEADD(DAY, -7, GETUTCDATE())
ORDER BY CheckDate DESC;
```

**Check aggregation status:**
```sql
-- Latest aggregations by type
SELECT 
    AggregationType,
    MAX(PeriodStart) AS LatestPeriod,
    MAX(CreatedAt) AS LastAggregated
FROM iot.AggregatedData
WHERE ChannelID = 9
GROUP BY AggregationType;
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: ODBC Driver Not Found

**Symptoms:**
```
pyodbc.Error: ('01000', "[01000] [unixODBC][Driver Manager]Can't open lib 'ODBC Driver 18 for SQL Server'")
```

**Solution:**
```bash
# List installed drivers
odbcinst -q -d

# If driver not found, install it (see Deployment Guide)

# If driver has different name, update .env or database.py
# Common driver names:
# - ODBC Driver 18 for SQL Server
# - ODBC Driver 17 for SQL Server
# - SQL Server
```

#### Issue 2: Database Connection Timeout

**Symptoms:**
```
ERROR - Database connection error: ('08001', '[08001] [Microsoft][ODBC Driver 18]...')
```

**Solution:**
```bash
# Test network connectivity
ping your-sql-server

# Test SQL Server port
telnet your-sql-server 1433
# or
nc -zv your-sql-server 1433

# Check firewall rules
sudo ufw status
sudo firewall-cmd --list-all

# Check SQL Server is listening
sqlcmd -S your-sql-server -U sa -Q "SELECT @@VERSION"

# Try with IP address instead of hostname
# Update DB_SERVER in .env
```

#### Issue 3: ThingSpeak Rate Limit Exceeded

**Symptoms:**
```
ERROR - Error fetching channel feed: 429 Client Error: Too Many Requests
```

**Solution:**
```python
# Increase rate_limit_delay in thingspeak_client.py
# or when instantiating ThingSpeakClient:
client = ThingSpeakClient(
    channel_id="9",
    rate_limit_delay=2.0  # Increase from 1.0 to 2.0 seconds
)

# Or upgrade to ThingSpeak paid tier for higher limits
```

#### Issue 4: Duplicate Key Errors

**Symptoms:**
```
ERROR - Error inserting sensor readings: Violation of UNIQUE KEY constraint 'UQ_ChannelEntry'
```

**This is expected behavior.** The code handles duplicates gracefully:
```python
try:
    cursor.execute(sql, params)
    inserted_count += 1
except pyodbc.IntegrityError:
    # Skip duplicate - this is normal
    continue
```

**If you see this in logs, it means:**
- Pipeline is running multiple times on same data (expected with scheduled runs)
- Duplicate prevention is working correctly

#### Issue 5: Stored Procedure Fails

**Symptoms:**
```
ERROR - Error executing stored procedure iot.usp_ProcessSensorReadings: ...
```

**Solution:**
```sql
-- Check if procedure exists
SELECT name FROM sys.procedures 
WHERE schema_id = SCHEMA_ID('iot') 
AND name = 'usp_ProcessSensorReadings';

-- If not found, run:
sqlcmd -S your_server -U sa -P 'password' -i sql/02_create_stored_procedures.sql

-- Check for data
SELECT COUNT(*) FROM iot.SensorReadings WHERE ChannelID = 9;

-- Test procedure manually
EXEC iot.usp_ProcessSensorReadings 
    @ChannelID = 9, 
    @AggregationType = 'DAILY',
    @StartDate = NULL,
    @EndDate = NULL;
```

### Diagnostic Commands

**System diagnostics:**
```bash
# Check Python version
python --version  # Should be 3.8+

# Check installed packages
pip list | grep -E '(pyodbc|requests|python-dotenv)'

# Check disk space
df -h

# Check memory
free -m

# Check running processes
ps aux | grep python
```

**Database diagnostics:**
```bash
# Test connection
sqlcmd -S your_server -U your_user -P 'your_password' -Q "SELECT @@VERSION"

# Check database exists
sqlcmd -S your_server -U your_user -P 'your_password' -Q "SELECT name FROM sys.databases WHERE name = 'IoTSensorDB'"

# Check schema objects
sqlcmd -S your_server -U your_user -P 'your_password' -d IoTSensorDB -Q \
  "SELECT SCHEMA_NAME(schema_id) + '.' + name AS ObjectName, type_desc 
   FROM sys.objects 
   WHERE schema_id = SCHEMA_ID('iot')"
```

---

## Backup and Recovery

### Database Backup

**Full backup:**
```sql
-- Manual backup
BACKUP DATABASE IoTSensorDB
TO DISK = '/var/opt/mssql/backup/IoTSensorDB_Full.bak'
WITH FORMAT, COMPRESSION;

-- Automated daily backup (SQL Server Agent)
USE msdb;
GO

EXEC sp_add_schedule
    @schedule_name = 'Daily Midnight',
    @freq_type = 4,  -- Daily
    @freq_interval = 1,
    @active_start_time = 000000;  -- Midnight

EXEC sp_add_job
    @job_name = 'Backup IoT Database',
    @enabled = 1;

EXEC sp_add_jobstep
    @job_name = 'Backup IoT Database',
    @step_name = 'Full Backup',
    @subsystem = 'TSQL',
    @command = '
        BACKUP DATABASE IoTSensorDB
        TO DISK = ''/var/opt/mssql/backup/IoTSensorDB_'' + 
                  CONVERT(NVARCHAR, GETDATE(), 112) + ''.bak''
        WITH COMPRESSION;',
    @retry_attempts = 3,
    @retry_interval = 5;

EXEC sp_attach_schedule
    @job_name = 'Backup IoT Database',
    @schedule_name = 'Daily Midnight';
```

**Differential backup:**
```sql
-- Hourly differential backup
BACKUP DATABASE IoTSensorDB
TO DISK = '/var/opt/mssql/backup/IoTSensorDB_Diff.bak'
WITH DIFFERENTIAL, COMPRESSION;
```

### Restore Procedures

**Full restore:**
```sql
-- Restore from full backup
USE master;
GO

ALTER DATABASE IoTSensorDB SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
GO

RESTORE DATABASE IoTSensorDB
FROM DISK = '/var/opt/mssql/backup/IoTSensorDB_Full.bak'
WITH REPLACE, RECOVERY;
GO

ALTER DATABASE IoTSensorDB SET MULTI_USER;
GO
```

**Point-in-time restore:**
```sql
-- Requires transaction log backups
RESTORE DATABASE IoTSensorDB
FROM DISK = '/var/opt/mssql/backup/IoTSensorDB_Full.bak'
WITH NORECOVERY;

RESTORE LOG IoTSensorDB
FROM DISK = '/var/opt/mssql/backup/IoTSensorDB_Log.bak'
WITH RECOVERY, STOPAT = '2024-11-24 12:00:00';
```

### Application Backup

**Backup configuration:**
```bash
#!/bin/bash
# backup_app.sh - Backup application files

BACKUP_DIR="/backup/iot-pipeline"
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/opt/iot-api-mssql-integration"

mkdir -p "$BACKUP_DIR"

# Backup .env file (encrypted)
openssl enc -aes-256-cbc -salt \
    -in "$APP_DIR/.env" \
    -out "$BACKUP_DIR/env_$DATE.enc" \
    -pass pass:YourEncryptionKey

# Backup custom scripts and configs
tar -czf "$BACKUP_DIR/app_$DATE.tar.gz" \
    -C "$APP_DIR" \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    .

# Keep only last 30 days of backups
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.enc" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR"
```

---

## Performance Tuning

### Database Performance

**Update statistics:**
```sql
-- Update statistics for better query plans
USE IoTSensorDB;
GO

UPDATE STATISTICS iot.SensorReadings WITH FULLSCAN;
UPDATE STATISTICS iot.AggregatedData WITH FULLSCAN;
```

**Rebuild indexes:**
```sql
-- Rebuild fragmented indexes (monthly maintenance)
ALTER INDEX IX_SensorReadings_ChannelID_CreatedAt 
ON iot.SensorReadings REBUILD;

ALTER INDEX IX_SensorReadings_CreatedAt 
ON iot.SensorReadings REBUILD;

ALTER INDEX IX_AggregatedData_ChannelID_Type_Period 
ON iot.AggregatedData REBUILD;
```

**Partition old data:**
```sql
-- Archive data older than 1 year
INSERT INTO iot.SensorReadings_Archive
SELECT * FROM iot.SensorReadings
WHERE CreatedAt < DATEADD(YEAR, -1, GETUTCDATE());

DELETE FROM iot.SensorReadings
WHERE CreatedAt < DATEADD(YEAR, -1, GETUTCDATE());

-- Shrink database after large delete
DBCC SHRINKDATABASE(IoTSensorDB, 10);
```

### Application Performance

**Optimize batch size:**
```python
# In pipeline.py, adjust fetch_results
pipeline.run_full_pipeline(fetch_results=500)  # Increase if network is fast
```

**Enable fast_executemany (future enhancement):**
```python
# In database.py, insert_sensor_readings method
cursor.fast_executemany = True
cursor.executemany(sql, params_list)
```

---

## Security Operations

### Credential Rotation

**Rotate database password:**
```sql
-- Change SQL Server password
ALTER LOGIN iot_pipeline_user WITH PASSWORD = 'NewSecurePassword123!';
```

```bash
# Update .env file
nano .env
# Change DB_PASSWORD value

# Restart pipeline service
sudo systemctl restart iot-pipeline.timer
```

**Rotate API key:**
```bash
# Update .env file
nano .env
# Change THINGSPEAK_API_KEY value

# No restart needed (reloaded on each run)
```

### Access Audit

**Review database logins:**
```sql
-- Check recent logins
SELECT 
    login_name,
    MAX(login_time) AS LastLogin
FROM sys.dm_exec_sessions
WHERE is_user_process = 1
GROUP BY login_name
ORDER BY LastLogin DESC;
```

**Review database permissions:**
```sql
-- Check user permissions
SELECT 
    USER_NAME(grantee_principal_id) AS UserName,
    permission_name,
    state_desc
FROM sys.database_permissions
WHERE grantee_principal_id = USER_ID('iot_pipeline_user');
```

### Security Hardening

**Principle of Least Privilege:**
```sql
-- Create dedicated user with minimal permissions
CREATE LOGIN iot_pipeline_user WITH PASSWORD = 'SecurePassword123!';
USE IoTSensorDB;
CREATE USER iot_pipeline_user FOR LOGIN iot_pipeline_user;

-- Grant only required permissions
GRANT SELECT, INSERT, UPDATE ON SCHEMA::iot TO iot_pipeline_user;
GRANT EXECUTE ON SCHEMA::iot TO iot_pipeline_user;

-- Remove default permissions
REVOKE CREATE TABLE TO iot_pipeline_user;
REVOKE CREATE VIEW TO iot_pipeline_user;
```

---

## Appendix: Runbook Summary

### Quick Reference

**Start pipeline manually:**
```bash
cd /opt/iot-api-mssql-integration && source venv/bin/activate && python src/pipeline.py
```

**Check pipeline status:**
```bash
sudo systemctl status iot-pipeline.timer
tail -f /var/log/iot-pipeline.log
```

**Emergency stop:**
```bash
sudo systemctl stop iot-pipeline.timer
ps aux | grep pipeline.py | awk '{print $2}' | xargs kill
```

**Check data freshness:**
```sql
SELECT TOP 1 ImportedAt, DATEDIFF(MINUTE, ImportedAt, GETUTCDATE()) AS MinutesAgo
FROM iot.SensorReadings
ORDER BY ImportedAt DESC;
```

**Contact Information:**
- Developer: Andrew Mathers
- Email: [your-email@example.com]
- On-call: [on-call-number]

---

**Related Documents:**
- [EXECUTIVE_SUMMARY.md](EXECUTIVE_SUMMARY.md) - Business overview
- [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) - Architecture deep dive
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Development guide
