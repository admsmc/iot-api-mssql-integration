#!/bin/bash
# Setup cron job for 15-minute polling
# Run this script to install the cron job

PROJECT_DIR="/Users/andrewmathers/projects/iot-api-mssql-integration"
PYTHON_PATH="python3"  # or /path/to/venv/bin/python3 if using venv
LOG_DIR="$PROJECT_DIR/logs"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Create the cron command
CRON_CMD="*/15 * * * * cd $PROJECT_DIR && $PYTHON_PATH src/multi_channel_pipeline.py >> $LOG_DIR/pipeline.log 2>&1"

echo "======================================================================="
echo "IoT Pipeline Cron Job Setup"
echo "======================================================================="
echo ""
echo "This will add the following cron job:"
echo ""
echo "$CRON_CMD"
echo ""
echo "Schedule: Every 15 minutes"
echo "Channels: As configured in .env (currently 5 channels)"
echo "Logs: $LOG_DIR/pipeline.log"
echo ""
echo "======================================================================="
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "multi_channel_pipeline.py"; then
    echo "⚠️  A cron job for this pipeline already exists!"
    echo ""
    echo "Current cron jobs:"
    crontab -l | grep "multi_channel_pipeline.py"
    echo ""
    read -p "Do you want to replace it? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 1
    fi
    # Remove existing job
    crontab -l | grep -v "multi_channel_pipeline.py" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo ""
echo "✅ Cron job installed successfully!"
echo ""
echo "Verify with:"
echo "  crontab -l | grep multi_channel"
echo ""
echo "View logs with:"
echo "  tail -f $LOG_DIR/pipeline.log"
echo ""
echo "Remove cron job with:"
echo "  crontab -l | grep -v multi_channel_pipeline.py | crontab -"
echo ""
echo "======================================================================="
