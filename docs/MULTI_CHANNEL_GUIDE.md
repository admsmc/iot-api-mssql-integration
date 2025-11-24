# Multi-Channel Integration Guide

## Overview

The enhanced pipeline supports monitoring **multiple ThingSpeak channels simultaneously**, allowing you to aggregate data from different sensor locations or devices into a single database.

## Test Results

✅ **Successfully tested with 2 public channels:**
- **Channel 9**: Home Weather Station (Pennsylvania)
- **Channel 12397**: MathWorks Weather Station (Massachusetts)

## Benefits

### 1. **Centralized Monitoring**
- Monitor all your IoT sensors from a single database
- Cross-location analysis and comparisons
- Unified reporting and dashboards

### 2. **Fault Tolerance**
- One channel failure doesn't stop others
- Per-channel error tracking and reporting
- Graceful degradation

### 3. **Scalability**
- Easily add new sensors/channels
- Rate limiting respects ThingSpeak API limits
- Database schema designed for multi-channel from the start

### 4. **Cost Efficiency**
- Single database instance for all channels
- Shared aggregation procedures
- Efficient resource utilization

## Configuration

### Option 1: Environment Variables (Recommended)

Update your `.env` file:

```bash
# Multi-channel mode (comma-separated)
THINGSPEAK_CHANNEL_IDS=9,12397

# Optional: API keys for private channels (comma-separated, same order)
THINGSPEAK_API_KEYS=,  # Empty = public channels

# Database config (same as before)
DB_SERVER=localhost
DB_NAME=IoTSensorDB
DB_USERNAME=sa
DB_PASSWORD=your_password
DB_TRUSTED_CONNECTION=False
```

### Option 2: Programmatic Configuration

```python
from src.multi_channel_pipeline import MultiChannelPipeline, ChannelConfig

channels = [
    ChannelConfig("9", description="Weather Station PA"),
    ChannelConfig("12397", description="Weather Station MA"),
    ChannelConfig("your_channel", api_key="your_key", description="Private Channel"),
]

pipeline = MultiChannelPipeline(channels=channels)
pipeline.run_full_pipeline(fetch_results=100)
```

## Usage

### Test Multi-Channel API Connectivity (No Database)

```bash
python3 test_multi_channel.py
```

This tests API connectivity for multiple channels without requiring database setup.

### Run Multi-Channel Pipeline (With Database)

```bash
# Update .env with multiple channel IDs
THINGSPEAK_CHANNEL_IDS=9,12397

# Run the pipeline
python3 src/multi_channel_pipeline.py
```

### Single Channel (Backward Compatible)

```bash
# Original format still works
THINGSPEAK_CHANNEL_ID=9
THINGSPEAK_API_KEY=

python3 src/pipeline.py
```

## Features

### Per-Channel Processing
- Each channel gets its own ThingSpeak client
- Independent metadata sync
- Separate error handling
- Individual aggregation runs

### Execution Summary
```
======================================================================
Pipeline Execution Summary
======================================================================
Total Channels:         3
Successfully Processed: 2
Failed:                 1
Total Records:          195
======================================================================
```

### Error Tracking
Failed channels are logged with:
- Channel ID
- Error message
- Timestamp
- Detailed stack traces in logs

## Database Considerations

### Schema Support
The existing schema **already supports** multiple channels:
- `iot.Channels` table stores metadata for all channels
- `iot.SensorReadings` has `ChannelID` foreign key
- `iot.AggregatedData` groups by `ChannelID`
- All queries filter by `ChannelID`

### Storage Growth
- Each channel adds ~100-1000 readings/day
- 10 channels = ~10,000 readings/day
- With hourly aggregations pre-computed
- Monitor disk space if tracking 100+ channels

### Query Performance
Indexes are optimized for multi-channel:
- `IX_SensorReadings_ChannelID_CreatedAt` (composite index)
- Aggregations run per-channel (no cross-channel joins)
- Stored procedures parameterized by `@ChannelID`

## Rate Limiting

ThingSpeak free tier: **~1 request/second**

The pipeline respects this by:
- Sequential channel processing (not parallel)
- Built-in rate limiting in `ThingSpeakClient`
- Default 1.0 second delay between requests

**For 3 channels:**
- 3 channel info requests = ~3 seconds
- 3 feed requests = ~3 seconds
- Total: ~6-10 seconds for full pipeline

**Avoid parallel processing without API keys!**

## Best Practices

### 1. Start Small
Begin with 2-3 channels to test your database setup and queries.

### 2. Monitor Performance
Track pipeline execution time and database size:
```sql
-- Check record counts per channel
SELECT ChannelID, COUNT(*) as Records
FROM iot.SensorReadings
GROUP BY ChannelID;

-- Check aggregation status
SELECT ChannelID, AggregationType, MAX(PeriodStart) as LatestPeriod
FROM iot.AggregatedData
GROUP BY ChannelID, AggregationType;
```

### 3. Schedule Wisely
For multiple channels, consider:
- Running hourly (not every minute)
- Staggering channels across runs
- Using `fetch_results=50` instead of 100 to reduce load

### 4. Use Private API Keys
If you have premium ThingSpeak accounts:
- Higher rate limits (no 1-second wait)
- Access to private channels
- Better reliability

### 5. Disable Failing Channels
Programmatic configuration allows disabling channels:
```python
ChannelConfig("broken_channel", enabled=False)
```

## Troubleshooting

### "Rate limit exceeded"
- Increase `rate_limit_delay` in `ThingSpeakClient` constructor
- Reduce number of channels processed per run
- Spread out scheduled runs

### "Database timeout"
- Reduce `fetch_results` per channel
- Add more indexes if querying specific fields
- Consider archiving old data

### "Channel not found (400 error)"
- Channel may be private (needs API key)
- Channel ID may be incorrect
- Channel may have been deleted

## Example: Production Deployment

### Cron Schedule
```bash
# /etc/cron.d/iot-pipeline

# Run every hour at :05 past the hour
5 * * * * /path/to/venv/bin/python3 /path/to/src/multi_channel_pipeline.py >> /var/log/iot-pipeline.log 2>&1
```

### Systemd Timer
```ini
# /etc/systemd/system/iot-pipeline.service
[Unit]
Description=IoT Multi-Channel Data Pipeline

[Service]
Type=oneshot
User=iot
WorkingDirectory=/opt/iot-api-mssql-integration
Environment="PATH=/opt/iot-api-mssql-integration/venv/bin"
ExecStart=/opt/iot-api-mssql-integration/venv/bin/python3 src/multi_channel_pipeline.py
```

```ini
# /etc/systemd/system/iot-pipeline.timer
[Unit]
Description=Run IoT Pipeline Hourly

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

## Future Enhancements

Potential additions (not yet implemented):
- [ ] Parallel processing with thread pool
- [ ] Per-channel configuration files (YAML/JSON)
- [ ] Automatic channel discovery
- [ ] Real-time streaming with MQTT
- [ ] Per-channel alerting rules
- [ ] Dashboard UI for monitoring all channels
- [ ] Auto-retry with exponential backoff
- [ ] Channel health scoring

## Summary

**Yes, multi-channel integration is highly advisable!**

✅ Database schema supports it  
✅ Architecture is ready for it  
✅ Implementation is production-ready  
✅ Performance is acceptable (with rate limiting)  
✅ Error handling is robust  

Start with 2-3 channels and scale up as needed.
