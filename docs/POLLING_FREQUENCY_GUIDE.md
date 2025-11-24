# Polling Frequency Guide

## Quick Answer

**Recommended polling frequency: Every 5-15 minutes**

| Frequency | Use Case | Pros | Cons |
|-----------|----------|------|------|
| **Every 15 seconds** | ❌ Not recommended | Near real-time | Rate limits, wasted calls |
| **Every 1 minute** | ❌ Too frequent | Recent data | Rate limits, minimal benefit |
| **Every 5 minutes** | ✅ Real-time monitoring | Good balance | Higher API usage |
| **Every 15 minutes** | ✅ **RECOMMENDED** | Efficient, reliable | 15-min delay acceptable |
| **Every hour** | ✅ Standard monitoring | Very efficient | 1-hour delay |
| **Every day** | ✅ Historical/batch | Most efficient | 24-hour delay |

## Why Not More Frequent?

### 1. ThingSpeak Update Rates

Most ThingSpeak channels update **every 15-60 seconds**:

```
Checked Channel 9:
- Entry 16785517: 2025-11-24T21:56:17Z
- Entry 16785518: 2025-11-24T22:04:18Z
- Entry 16785519: 2025-11-24T22:12:18Z
Gap: ~8 minutes between readings
```

**Reality check:** If the sensor only posts every 8 minutes, polling every 15 seconds is wasteful!

### 2. ThingSpeak Free Tier Limits

**Rate limit: ~1 request per second**

Polling 10 channels every 15 seconds:
- 10 channels × 2 API calls = 20 calls
- 20 calls in 15 seconds = **1.33 calls/second**
- **EXCEEDS free tier limit!** ❌

Polling 10 channels every 5 minutes:
- 10 channels × 2 API calls = 20 calls
- 20 calls in 300 seconds = **0.067 calls/second**
- **Within limits** ✅

### 3. Data Value vs. Cost

**Diminishing returns:**
```
Update every 15 seconds × 24 hours = 5,760 API calls/day/channel
Update every 15 minutes × 24 hours = 96 API calls/day/channel
Reduction: 98.3% fewer calls, <1% data loss
```

## Optimal Polling by Sensor Type

### High-Frequency Sensors (Fast-changing data)

**Examples:** Motion detectors, door sensors, vibration monitors

**Sensor update rate:** Every 15-60 seconds  
**Recommended polling:** **Every 5 minutes**

**Rationale:**
- Captures most events (5 min = 300 sec window)
- Reasonable for alerting
- Doesn't overwhelm API

**Alternative:** Use ThingSpeak TalkBack API for alerts instead of polling

### Medium-Frequency Sensors (Moderate changes)

**Examples:** Temperature, humidity, air quality, pressure

**Sensor update rate:** Every 1-15 minutes  
**Recommended polling:** **Every 15 minutes** ⭐ **RECOMMENDED DEFAULT**

**Rationale:**
- Matches sensor update rates
- 96 readings/day/channel
- Plenty for trend analysis
- Very API-efficient

### Low-Frequency Sensors (Slow changes)

**Examples:** Daily rainfall, soil moisture, battery levels

**Sensor update rate:** Every 30-60 minutes  
**Recommended polling:** **Every 1 hour**

**Rationale:**
- Sensor doesn't change much
- 24 readings/day sufficient
- Maximum API efficiency

### Historical/Reporting Only

**Examples:** Archived data, compliance reporting, long-term trends

**Sensor update rate:** Irrelevant  
**Recommended polling:** **Once daily**

**Rationale:**
- Not time-sensitive
- Aggregated data is sufficient
- Minimal API usage

## ThingSpeak Channel Update Rates

Let me check actual update rates for real channels:

### Channel 9 (Home Weather Station)
```
Recent entries:
16785517: 2025-11-24T21:56:17Z
16785518: 2025-11-24T22:04:18Z  (+8 min)
16785519: 2025-11-24T22:12:18Z  (+8 min)
16785520: 2025-11-24T22:36:18Z  (+24 min)
16785521: 2025-11-24T22:44:18Z  (+8 min)

Average update rate: ~8-10 minutes
```

**Conclusion:** Polling this channel more than every 5-10 minutes gets duplicate data!

### Channel 12397 (MathWorks Weather Station)
```
Last entry: 2025-09-29T15:49:01Z
Status: Inactive for 2+ months
```

**Conclusion:** Polling inactive channels wastes API calls. Need detection!

## API Usage Calculations

### Scenario: 10 Channels, Different Frequencies

| Frequency | Calls/Day/Channel | Total Calls/Day | Annual Calls | Free Tier Impact |
|-----------|-------------------|-----------------|--------------|------------------|
| Every 15 sec | 5,760 | 57,600 | 21M | ❌ Exceeds limits |
| Every 1 min | 1,440 | 14,400 | 5.3M | ❌ Risky |
| Every 5 min | 288 | 2,880 | 1.05M | ⚠️ Acceptable |
| Every 15 min | 96 | 960 | 350K | ✅ Safe |
| Every hour | 24 | 240 | 87.6K | ✅ Very safe |
| Daily | 1 | 10 | 3,650 | ✅ Minimal |

### Scenario: 50 Channels

| Frequency | Total Calls/Day | Free Tier Status |
|-----------|-----------------|------------------|
| Every 15 min | 4,800 | ✅ Safe (0.056 req/sec avg) |
| Every 5 min | 14,400 | ⚠️ Borderline (0.167 req/sec avg) |
| Every 1 min | 72,000 | ❌ Too high (0.83 req/sec avg) |

**The more channels you have, the less frequently you should poll each!**

## Recommended Strategy: Tiered Polling

Different channels can have different frequencies:

```python
# config/polling_tiers.yaml
high_priority:
  channels: [9, 12397]
  frequency: "5 minutes"
  description: "Critical sensors needing near real-time data"

standard:
  channels: [301051, 50123, ...]
  frequency: "15 minutes"
  description: "Normal monitoring"

low_priority:
  channels: [999, 1234, ...]
  frequency: "1 hour"
  description: "Slow-changing or historical"

batch:
  channels: [5555, 6666, ...]
  frequency: "daily"
  description: "Reporting only"
```

**Benefit:** Optimize API usage while maintaining responsiveness where needed.

## Smart Polling Strategies

### 1. Adaptive Polling
Check if data has changed before deep poll:

```python
# Quick check: get last entry ID
last_entry = client.get_last_entry()
if last_entry['entry_id'] != previous_entry_id:
    # New data! Fetch full feed
    feed_data = client.get_channel_feed(results=100)
else:
    # No change, skip this cycle
    pass
```

**Saves API calls when sensors are inactive!**

### 2. Detect Inactive Channels
Skip channels that haven't updated in 24+ hours:

```sql
-- Query to find inactive channels
SELECT ChannelID, MAX(CreatedAt) as LastUpdate
FROM iot.SensorReadings
GROUP BY ChannelID
HAVING MAX(CreatedAt) < DATEADD(DAY, -1, GETUTCDATE());
```

### 3. Time-Based Scheduling
Adjust frequency by time of day:

```
Business hours (9 AM - 5 PM): Every 15 minutes
Off hours (5 PM - 9 AM): Every hour
Weekends: Every 2 hours
```

**Saves 60-70% of API calls if monitoring business facilities!**

## Real-Time Alternatives

If you need **true real-time** (< 1 minute latency), consider:

### 1. ThingSpeak TalkBack API
- Push notifications for threshold breaches
- No polling needed
- Requires sensor-side configuration

### 2. ThingSpeak MQTT
- Real-time streaming protocol
- Subscribe to channel updates
- Requires MQTT broker setup

### 3. ThingSpeak React API
- Automated actions on data conditions
- Triggers external webhooks
- No custom polling needed

### 4. Webhooks (if ThingSpeak supports)
- Push updates to your server
- Instant notifications
- Best for critical alerts

## Cron Schedule Examples

### Every 5 Minutes
```bash
*/5 * * * * /path/to/venv/bin/python3 /path/to/pipeline.py >> /var/log/iot.log 2>&1
```

### Every 15 Minutes (Recommended)
```bash
*/15 * * * * /path/to/venv/bin/python3 /path/to/pipeline.py >> /var/log/iot.log 2>&1
```

### Every Hour
```bash
0 * * * * /path/to/venv/bin/python3 /path/to/pipeline.py >> /var/log/iot.log 2>&1
```

### Daily at 2 AM
```bash
0 2 * * * /path/to/venv/bin/python3 /path/to/pipeline.py >> /var/log/iot.log 2>&1
```

## Monitoring Polling Efficiency

Track these metrics to optimize:

```python
# 1. Data freshness
latest_reading_age = now - last_reading_timestamp
# Target: < 2x polling frequency

# 2. Duplicate rate
duplicate_entries = readings_fetched - new_readings_inserted
duplicate_rate = duplicate_entries / readings_fetched
# Target: < 20%

# 3. API efficiency
useful_calls = calls_with_new_data / total_api_calls
# Target: > 80%

# 4. Channel activity rate
active_channels = channels_with_updates / total_channels
# Target: > 90% (or adjust frequency)
```

## Decision Tree

```
How time-sensitive is your monitoring?
├─ Critical (safety/security) → Every 5 minutes + alerts
├─ Important (operations) → Every 15 minutes ⭐ RECOMMENDED
├─ Standard (monitoring) → Every hour
└─ Historical (reporting) → Daily

How many channels?
├─ 1-10 channels → Every 5-15 minutes OK
├─ 10-50 channels → Every 15 minutes recommended
├─ 50-100 channels → Every hour recommended
└─ 100+ channels → Daily batch + tiered strategy

What's your API tier?
├─ Free tier (1 req/sec) → 15 minutes or longer
└─ Paid tier (3-4 req/sec) → 5 minutes OK for < 50 channels
```

## Summary

**Best Practice: Poll every 15 minutes**

✅ **Pros:**
- Matches typical sensor update rates (8-15 min)
- 96 data points per day (excellent for analysis)
- API-efficient (0.001 req/sec per channel)
- Scales to 50+ channels easily
- Good balance of freshness and efficiency

❌ **Don't:**
- Poll every second/15 seconds (rate limits, wasted calls)
- Poll faster than sensor update rate (duplicates)
- Use same frequency for all channels (inefficient)

🎯 **Optimal Setup:**
```bash
# .env
POLLING_FREQUENCY=15  # minutes

# crontab
*/15 * * * * python3 /path/to/multi_channel_pipeline.py
```

---

**Bottom line:** Start with **every 15 minutes**. If you need faster, try 5 minutes but watch your rate limits. If data isn't time-sensitive, hourly or daily is much more efficient.
