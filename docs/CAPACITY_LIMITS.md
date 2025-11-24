# Channel Capacity Limits

## Quick Answer

**Maximum channels you can connect to depends on your setup:**

| Scenario | Recommended Max | Notes |
|----------|----------------|-------|
| **Free API, Hourly** | **50-100 channels** | Safe for production |
| **Free API, Daily** | **500-1000 channels** | Best for batch processing |
| **Paid API, Hourly** | **200-300 channels** | Faster processing |
| **Paid API, Daily** | **2000+ channels** | Only limited by storage |

## Detailed Analysis

### Primary Constraint: API Rate Limits

**ThingSpeak Free Tier:**
- ~1 request per second
- 2 API calls per channel (metadata + feed)
- **4 seconds total per channel** (2s API + 2s processing)

**ThingSpeak Paid Tier:**
- ~3-4 requests per second
- 2 API calls per channel
- **~2.7 seconds per channel** (0.7s API + 2s processing)

### Secondary Constraint: Database Storage

**Storage Requirements:**
- ~17.8 MB per channel per year (at 100 readings/day)
- 10 GB database = ~574 channels (1 year data)
- 100 GB database = ~5,745 channels (1 year data)

### Execution Time Calculations

#### Free Tier, Hourly Pipeline
```
Available: 60 minutes = 3,600 seconds
Per channel: 4 seconds
Theoretical max: 900 channels
Recommended: 720 channels (with safety margin)
Storage limit (10 GB): 574 channels ← ACTUAL LIMIT
```

**Recommended: 50-100 channels for production safety**

#### Free Tier, Daily Batch
```
Available: 24 hours = 86,400 seconds
Per channel: 4 seconds
Theoretical max: 21,600 channels
Storage limit (100 GB): 5,745 channels ← ACTUAL LIMIT
```

**Recommended: 500-1000 channels**

#### Paid API, 15-Minute Pipeline
```
Available: 15 minutes = 900 seconds
Per channel: 2.7 seconds
Theoretical max: 337 channels
Recommended: 269 channels (with safety margin)
```

**Recommended: 200-300 channels**

## Scaling Strategies

### Strategy 1: Increase Schedule Interval
Run less frequently to process more channels:

| Interval | Free Tier Max | Paid API Max |
|----------|---------------|--------------|
| Every 5 min | 60 channels | 89 channels |
| Every 15 min | 180 channels | 269 channels |
| Every hour | 720 channels | 1,080 channels |
| Daily | 17,280 channels | 25,920 channels |

### Strategy 2: Batch Processing
Split channels across multiple pipeline runs:

```python
# Run 1: Channels 1-100
THINGSPEAK_CHANNEL_IDS=9,12397,...  # 100 channels

# Run 2: Channels 101-200 (5 minutes later)
THINGSPEAK_CHANNEL_IDS=50123,...    # next 100 channels
```

### Strategy 3: Upgrade to Paid API
- 3-4x faster processing
- Higher rate limits
- More reliable access

### Strategy 4: Multiple Database Instances
For 1000+ channels:
- Split across geographic regions
- One database per customer/group
- Parallel processing with multiple instances

## Real-World Scenarios

### Scenario 1: Small Business (5-10 Locations)
**Channels:** 10  
**Schedule:** Every 15 minutes  
**Database:** 10 GB  
**API:** Free tier  
**Status:** ✅ Plenty of capacity

### Scenario 2: Medium Enterprise (50-100 Locations)
**Channels:** 100  
**Schedule:** Hourly  
**Database:** 50 GB  
**API:** Free tier (consider paid)  
**Status:** ✅ At capacity, consider optimizations

### Scenario 3: Large Enterprise (500+ Locations)
**Channels:** 500  
**Schedule:** Daily batch  
**Database:** 100 GB  
**API:** Paid tier recommended  
**Status:** ⚠️ Need paid API + daily processing

### Scenario 4: IoT Platform (1000+ Devices)
**Channels:** 1000+  
**Schedule:** Daily batch + batching strategy  
**Database:** Multiple instances  
**API:** Paid tier required  
**Status:** ⚠️ Requires architecture redesign

## Performance Optimization

### 1. Reduce Records Per Fetch
Instead of fetching 100 records per channel:
```python
pipeline.run_full_pipeline(fetch_results=50)  # Half the data
```

### 2. Selective Field Processing
Only fetch specific fields:
```python
client.get_field_data(field_number=1, results=50)
```

### 3. Smart Scheduling
Process high-priority channels more frequently:
```
High priority (critical sensors): Every 15 minutes
Low priority (historical data): Daily
```

### 4. Database Archiving
Move old data to archive tables:
```sql
-- Keep only last 90 days in hot storage
-- Move older data to archive tables
```

## Using the Calculator

Run the capacity calculator to see limits for your specific setup:

```bash
python3 tools/capacity_calculator.py
```

Or customize for your scenario:

```python
from tools.capacity_calculator import calculate_capacity

calculate_capacity(
    api_requests_per_second=1.0,    # Your API tier
    schedule_interval_minutes=60,    # How often you run
    processing_overhead_seconds=2.0, # Database speed
    storage_limit_gb=50              # Your DB size
)
```

## Bottleneck Identification

**If processing is slow, identify the bottleneck:**

1. **API Rate Limit** (most common)
   - Symptom: Long pauses between channels
   - Solution: Upgrade to paid API or schedule less frequently

2. **Database Performance**
   - Symptom: Fast API calls, slow writes
   - Solution: Add indexes, optimize stored procedures

3. **Network Latency**
   - Symptom: Slow API responses
   - Solution: Run closer to ThingSpeak servers, use CDN

4. **Storage Space**
   - Symptom: Database fills up quickly
   - Solution: Archive old data, add storage

## Monitoring Recommendations

Track these metrics to stay within capacity:

```python
# Pipeline execution time
# Target: < 80% of schedule interval

# Database growth rate
# Target: < storage limit / expected lifetime

# API error rate
# Target: < 1% (rate limit errors)

# Channel success rate
# Target: > 95%
```

## Hard Limits Summary

| Constraint | Limit | Type |
|------------|-------|------|
| ThingSpeak Free API | ~1 req/sec | Soft limit |
| ThingSpeak Paid API | ~3-4 req/sec | Soft limit |
| SQL Server Channels | 2.1 billion | Hard limit (INT) |
| Database Storage | Hardware dependent | Hard limit |
| Pipeline Execution | Schedule interval | Configuration limit |

## Recommendations by Use Case

**Development/Testing:** 2-5 channels  
**Small Deployment:** 10-20 channels  
**Medium Deployment:** 50-100 channels  
**Large Deployment:** 100-500 channels  
**Enterprise/Platform:** 500+ channels (needs architectural review)

---

**Bottom Line:** Start with **10-20 channels** to validate your setup, then scale up to **50-100 channels** for production. Beyond 100 channels, plan for paid API access and daily batch processing.
