# Demo Use Cases Based on Selected Channels

## Selected Channels Overview

| Channel | Name | Type | Update Frequency | Key Data |
|---------|------|------|------------------|----------|
| **3** | Uniontown Weather Data | Weather Station | Active (last: 2 hours ago) | Temperature, weather metrics |
| **4** | Lee's Test Channel | Test/Demo | Inactive (2017) | Unicode/character testing |
| **9** | my_house | Home IoT | Very Active (minutes ago) | Home sensors (temp, humidity) |
| **38629** | Traffic Monitor | Transportation | Very Active (minutes ago) | Traffic density, car counts |
| **1417** | CheerLights | IoT Community | Active (minutes ago) | Color values, IoT events |

## 🎯 Primary Use Cases

### 1. **Smart City Monitoring** ⭐ BEST DEMO

**Scenario:** A city monitors multiple data sources for urban planning and operations.

**Channels Used:**
- **Channel 3** (Uniontown Weather) - Weather conditions
- **Channel 38629** (Traffic Monitor) - Traffic flow
- **Channel 9** (my_house) - Local environmental sensors

**Demo Queries:**

```sql
-- Weather-Traffic Correlation
-- Show how weather affects traffic patterns
SELECT 
    w.CreatedAt as Timestamp,
    w.Field1 as Temperature,
    w.Field2 as Humidity,
    t.Field1 as TrafficDensity,
    CASE 
        WHEN w.Field1 < 32 THEN 'Freezing'
        WHEN w.Field1 < 50 THEN 'Cold'
        ELSE 'Normal'
    END as WeatherCondition
FROM iot.SensorReadings w
INNER JOIN iot.SensorReadings t 
    ON DATEADD(MINUTE, -5, w.CreatedAt) <= t.CreatedAt 
    AND t.CreatedAt <= DATEADD(MINUTE, 5, w.CreatedAt)
WHERE w.ChannelID = 3  -- Weather
    AND t.ChannelID = 38629  -- Traffic
    AND w.CreatedAt >= DATEADD(DAY, -7, GETUTCDATE())
ORDER BY w.CreatedAt DESC;

-- Urban Dashboard Query
SELECT 
    c.ChannelName,
    sr.Field1 as PrimaryMetric,
    sr.Field2 as SecondaryMetric,
    sr.CreatedAt,
    DATEDIFF(MINUTE, sr.CreatedAt, GETUTCDATE()) as MinutesAgo
FROM iot.vw_LatestReadings c
WHERE c.ChannelID IN (3, 38629, 9);
```

**Business Value:**
- Optimize traffic light timing based on weather
- Predict rush hour congestion
- Air quality monitoring correlated with traffic
- Emergency response planning

---

### 2. **Multi-Location Environmental Monitoring**

**Scenario:** Monitor environmental conditions across different geographic locations.

**Channels Used:**
- **Channel 3** (Uniontown, PA) - Weather data
- **Channel 9** (Home sensors) - Indoor environmental
- **Channel 38629** (Traffic area) - Urban environment

**Demo Queries:**

```sql
-- Compare Environmental Conditions Across Locations
SELECT 
    PeriodStart,
    MAX(CASE WHEN ChannelID = 3 THEN Field1Avg END) as Uniontown_Temp,
    MAX(CASE WHEN ChannelID = 9 THEN Field1Avg END) as Indoor_Temp,
    MAX(CASE WHEN ChannelID = 38629 THEN Field1Avg END) as Urban_Metric
FROM iot.AggregatedData
WHERE AggregationType = 'HOURLY'
    AND PeriodStart >= DATEADD(DAY, -1, GETUTCDATE())
GROUP BY PeriodStart
ORDER BY PeriodStart DESC;

-- Temperature Variance Analysis
SELECT 
    ChannelID,
    ChannelName,
    AVG(Field1) as AvgValue,
    MIN(Field1) as MinValue,
    MAX(Field1) as MaxValue,
    STDEV(Field1) as StdDeviation,
    COUNT(*) as ReadingCount
FROM iot.SensorReadings sr
INNER JOIN iot.Channels c ON sr.ChannelID = c.ChannelID
WHERE sr.CreatedAt >= DATEADD(DAY, -7, GETUTCDATE())
    AND sr.ChannelID IN (3, 9)
    AND sr.Field1 IS NOT NULL
GROUP BY ChannelID, ChannelName;
```

**Business Value:**
- Cross-location environmental comparison
- Indoor vs. outdoor conditions
- HVAC optimization
- Energy management

---

### 3. **IoT Community Platform** (Using CheerLights)

**Scenario:** Community-driven IoT demonstration showing real-time global synchronization.

**Channels Used:**
- **Channel 1417** (CheerLights) - IoT community events

**Demo Queries:**

```sql
-- CheerLights Activity Pattern
-- Show how global IoT community interacts
SELECT 
    CAST(CreatedAt AS DATE) as Date,
    COUNT(*) as ColorChanges,
    COUNT(DISTINCT Field1) as UniqueColors
FROM iot.SensorReadings
WHERE ChannelID = 1417
    AND CreatedAt >= DATEADD(DAY, -30, GETUTCDATE())
GROUP BY CAST(CreatedAt AS DATE)
ORDER BY Date DESC;

-- Most Active Times
SELECT 
    DATEPART(HOUR, CreatedAt) as HourOfDay,
    COUNT(*) as ActivityCount,
    AVG(Field1) as AvgValue
FROM iot.SensorReadings
WHERE ChannelID = 1417
    AND CreatedAt >= DATEADD(DAY, -7, GETUTCDATE())
GROUP BY DATEPART(HOUR, CreatedAt)
ORDER BY HourOfDay;
```

**Business Value:**
- IoT platform engagement metrics
- Global community activity patterns
- Real-time event synchronization
- Social IoT applications

---

### 4. **Traffic Analytics & Prediction**

**Scenario:** Analyze traffic patterns for urban planning and optimization.

**Channels Used:**
- **Channel 38629** (Traffic Monitor) - Primary data source

**Demo Queries:**

```sql
-- Traffic Pattern Analysis by Hour
SELECT 
    DATEPART(HOUR, CreatedAt) as HourOfDay,
    DATEPART(WEEKDAY, CreatedAt) as DayOfWeek,
    AVG(Field1) as AvgTrafficDensity,
    MAX(Field1) as PeakDensity,
    COUNT(*) as Observations
FROM iot.SensorReadings
WHERE ChannelID = 38629
    AND CreatedAt >= DATEADD(DAY, -30, GETUTCDATE())
    AND Field1 IS NOT NULL
GROUP BY DATEPART(HOUR, CreatedAt), DATEPART(WEEKDAY, CreatedAt)
ORDER BY DayOfWeek, HourOfDay;

-- Detect Traffic Anomalies (using stored procedure)
EXEC iot.usp_DetectAnomalies 
    @ChannelID = 38629,
    @FieldNumber = 1,
    @ThresholdStdDev = 2.5,
    @LookbackDays = 14;

-- Traffic Trend Analysis
EXEC iot.usp_GetTrendAnalysis
    @ChannelID = 38629,
    @FieldNumber = 1,
    @Days = 30;
```

**Business Value:**
- Rush hour identification
- Anomaly detection (accidents, events)
- Predictive traffic modeling
- Infrastructure planning

---

### 5. **Data Quality Monitoring Dashboard**

**Scenario:** Monitor the health and quality of multiple IoT data streams.

**Channels Used:** All 5 channels

**Demo Queries:**

```sql
-- Overall Channel Health Dashboard
SELECT * FROM iot.vw_ChannelHealth
ORDER BY 
    CASE HealthStatus
        WHEN 'HEALTHY' THEN 1
        WHEN 'FAIR' THEN 2
        WHEN 'LOW_VOLUME' THEN 3
        WHEN 'POOR_QUALITY' THEN 4
        WHEN 'STALE' THEN 5
    END;

-- Data Quality Comparison
SELECT 
    c.ChannelID,
    c.ChannelName,
    COUNT(sr.ReadingID) as TotalReadings,
    COUNT(CASE WHEN sr.Field1 IS NOT NULL THEN 1 END) as ValidField1,
    COUNT(CASE WHEN sr.Field2 IS NOT NULL THEN 1 END) as ValidField2,
    100.0 * COUNT(CASE WHEN sr.Field1 IS NOT NULL THEN 1 END) / COUNT(*) as Field1Completeness
FROM iot.Channels c
LEFT JOIN iot.SensorReadings sr ON c.ChannelID = sr.ChannelID
    AND sr.CreatedAt >= DATEADD(DAY, -7, GETUTCDATE())
WHERE c.IsActive = 1
GROUP BY c.ChannelID, c.ChannelName;

-- Calculate Quality Scores for All Channels
EXEC iot.usp_CalculateDataQuality @ChannelID = 3, @CheckDate = NULL;
EXEC iot.usp_CalculateDataQuality @ChannelID = 9, @CheckDate = NULL;
EXEC iot.usp_CalculateDataQuality @ChannelID = 38629, @CheckDate = NULL;
EXEC iot.usp_CalculateDataQuality @ChannelID = 1417, @CheckDate = NULL;
```

**Business Value:**
- Proactive monitoring
- SLA compliance
- Sensor maintenance scheduling
- Data pipeline health

---

### 6. **Time-Series Aggregation & Reporting**

**Scenario:** Generate reports showing trends over time across multiple sources.

**Channels Used:** All active channels (3, 9, 38629, 1417)

**Demo Queries:**

```sql
-- Weekly Aggregation Summary
SELECT 
    c.ChannelName,
    ad.PeriodStart,
    ad.AggregationType,
    ad.Field1Avg,
    ad.Field1Min,
    ad.Field1Max,
    ad.ReadingCount
FROM iot.AggregatedData ad
INNER JOIN iot.Channels c ON ad.ChannelID = c.ChannelID
WHERE ad.AggregationType = 'WEEKLY'
    AND ad.PeriodStart >= DATEADD(MONTH, -1, GETUTCDATE())
ORDER BY ad.PeriodStart DESC, c.ChannelName;

-- Cross-Channel Daily Comparison
SELECT * FROM iot.vw_CrossChannelComparison
WHERE PeriodStart >= DATEADD(DAY, -7, GETUTCDATE())
ORDER BY PeriodStart DESC;

-- Process Aggregations for All Channels
EXEC iot.usp_ProcessSensorReadings @ChannelID = 3, @AggregationType = 'DAILY', @StartDate = NULL, @EndDate = NULL;
EXEC iot.usp_ProcessSensorReadings @ChannelID = 9, @AggregationType = 'DAILY', @StartDate = NULL, @EndDate = NULL;
EXEC iot.usp_ProcessSensorReadings @ChannelID = 38629, @AggregationType = 'DAILY', @StartDate = NULL, @EndDate = NULL;
EXEC iot.usp_ProcessSensorReadings @ChannelID = 1417, @AggregationType = 'DAILY', @StartDate = NULL, @EndDate = NULL;
```

**Business Value:**
- Historical trend analysis
- Comparative reporting
- Performance benchmarking
- Executive dashboards

---

## 🎬 Recommended Demo Flow

### Phase 1: Setup & Data Collection (5 minutes)
1. Show cron job configuration
2. Display real-time log monitoring (`tail -f logs/pipeline.log`)
3. Explain 15-minute polling schedule

### Phase 2: Basic Queries (10 minutes)
1. **Latest readings from all channels**
   ```sql
   SELECT * FROM iot.vw_LatestReadings;
   ```

2. **Channel summary statistics**
   ```sql
   SELECT * FROM iot.vw_ChannelSummary ORDER BY TotalReadings DESC;
   ```

3. **Channel health dashboard**
   ```sql
   SELECT * FROM iot.vw_ChannelHealth;
   ```

### Phase 3: Advanced Use Cases (15 minutes)

**A. Smart City Monitoring**
- Weather-Traffic correlation query
- Show how urban planning uses this data

**B. Traffic Analytics**
- Rush hour identification
- Anomaly detection demo
- Show trend analysis

**C. Multi-Location Comparison**
- Cross-location environmental data
- Indoor vs outdoor comparison

### Phase 4: Stored Procedures (10 minutes)

1. **Aggregation Demo**
   ```sql
   EXEC iot.usp_ProcessSensorReadings 
       @ChannelID = 38629, 
       @AggregationType = 'HOURLY';
   ```

2. **Anomaly Detection**
   ```sql
   EXEC iot.usp_DetectAnomalies 
       @ChannelID = 38629, 
       @FieldNumber = 1;
   ```

3. **Data Quality**
   ```sql
   EXEC iot.usp_CalculateDataQuality 
       @ChannelID = 9;
   ```

### Phase 5: Scalability Discussion (5 minutes)
- Show capacity calculator results
- Discuss scaling to 10-100 channels
- Explain polling frequency optimization

---

## 💡 Key Demo Talking Points

### Technical Excellence
✅ Multi-channel architecture handles diverse data sources  
✅ Rate limiting respects API constraints  
✅ Duplicate prevention via unique constraints  
✅ Automated aggregations for performance  
✅ Real-time monitoring with 15-minute freshness  

### Business Value
✅ Smart city operations  
✅ Predictive analytics  
✅ Cross-location insights  
✅ Data quality assurance  
✅ Cost-effective (free tier compatible)  

### Scalability
✅ 5 channels → 50 channels (same architecture)  
✅ Hourly → Daily aggregations (pre-computed)  
✅ Per-channel error handling (fault tolerant)  
✅ Easy to add new channels (just update .env)  

---

## 📊 Demo Data Expectations

Based on 15-minute polling over 24 hours:

| Metric | Expected Value |
|--------|---------------|
| **Channels monitored** | 5 |
| **Readings per channel** | ~96 per day |
| **Total readings** | ~480 per day |
| **API calls** | 960 per day |
| **Data freshness** | < 15 minutes |
| **Success rate** | > 95% |

---

## 🎯 Best Demo Use Case: Smart City Monitoring

**Why it's the best:**
1. ✅ **Uses 3 channels together** (weather + traffic + environment)
2. ✅ **Real-world business value** (urban planning, operations)
3. ✅ **Shows data correlation** (weather affects traffic)
4. ✅ **Demonstrates aggregations** (hourly/daily patterns)
5. ✅ **Actionable insights** (optimize city operations)

**Demo Script:**
> "Imagine you're running a Smart City operations center. You need to monitor weather conditions, traffic flow, and environmental sensors across the city. Our system automatically polls 5 different IoT data sources every 15 minutes, stores everything in SQL Server, and provides real-time dashboards. Watch as we correlate weather patterns with traffic density to predict when road conditions will deteriorate..."

---

## 📁 Next Steps

1. ✅ Set up SQL Server database
2. ✅ Run initial data collection (wait 15 min × 4 = 1 hour for good dataset)
3. ✅ Execute demo queries
4. ✅ Show stored procedure capabilities
5. ✅ Discuss scalability options

**Ready to demo in:** ~1 hour after database setup
