-- Optional Multi-Channel Convenience Views
-- These views make it easier to query and compare data across channels
-- Run this file AFTER 01_create_schema.sql and 02_create_stored_procedures.sql

USE IoTSensorDB;
GO

-- =============================================
-- View: vw_LatestReadings
-- Description: Latest reading from each channel with channel info
-- =============================================
CREATE OR ALTER VIEW iot.vw_LatestReadings AS
SELECT 
    c.ChannelID,
    c.ChannelName,
    c.Description,
    sr.EntryID,
    sr.CreatedAt,
    sr.Field1,
    sr.Field2,
    sr.Field3,
    sr.Field4,
    sr.Latitude,
    sr.Longitude,
    DATEDIFF(MINUTE, sr.CreatedAt, GETUTCDATE()) as MinutesSinceUpdate
FROM iot.Channels c
LEFT JOIN iot.SensorReadings sr ON c.ChannelID = sr.ChannelID
    AND sr.CreatedAt = (
        SELECT MAX(CreatedAt) 
        FROM iot.SensorReadings 
        WHERE ChannelID = c.ChannelID
    )
WHERE c.IsActive = 1;
GO

-- =============================================
-- View: vw_ChannelSummary
-- Description: Summary statistics for all channels
-- =============================================
CREATE OR ALTER VIEW iot.vw_ChannelSummary AS
SELECT 
    c.ChannelID,
    c.ChannelName,
    c.Description,
    c.IsActive,
    COUNT(sr.ReadingID) as TotalReadings,
    MIN(sr.CreatedAt) as FirstReading,
    MAX(sr.CreatedAt) as LastReading,
    DATEDIFF(HOUR, MIN(sr.CreatedAt), MAX(sr.CreatedAt)) as DataSpanHours,
    COUNT(DISTINCT CAST(sr.CreatedAt AS DATE)) as DaysWithData
FROM iot.Channels c
LEFT JOIN iot.SensorReadings sr ON c.ChannelID = sr.ChannelID
GROUP BY c.ChannelID, c.ChannelName, c.Description, c.IsActive;
GO

-- =============================================
-- View: vw_DailyAggregations
-- Description: Daily aggregations with channel names
-- =============================================
CREATE OR ALTER VIEW iot.vw_DailyAggregations AS
SELECT 
    c.ChannelID,
    c.ChannelName,
    ad.PeriodStart,
    ad.PeriodEnd,
    ad.Field1Avg,
    ad.Field1Min,
    ad.Field1Max,
    ad.Field2Avg,
    ad.Field2Min,
    ad.Field2Max,
    ad.ReadingCount
FROM iot.AggregatedData ad
INNER JOIN iot.Channels c ON ad.ChannelID = c.ChannelID
WHERE ad.AggregationType = 'DAILY'
    AND c.IsActive = 1;
GO

-- =============================================
-- View: vw_ChannelHealth
-- Description: Health status of all channels
-- =============================================
CREATE OR ALTER VIEW iot.vw_ChannelHealth AS
SELECT 
    c.ChannelID,
    c.ChannelName,
    c.IsActive,
    lr.LastReading,
    DATEDIFF(MINUTE, lr.LastReading, GETUTCDATE()) as MinutesSinceUpdate,
    lr.ReadingsLast24Hours,
    dq.QualityScore,
    CASE 
        WHEN DATEDIFF(HOUR, lr.LastReading, GETUTCDATE()) > 24 THEN 'STALE'
        WHEN lr.ReadingsLast24Hours < 10 THEN 'LOW_VOLUME'
        WHEN dq.QualityScore < 50 THEN 'POOR_QUALITY'
        WHEN dq.QualityScore >= 80 THEN 'HEALTHY'
        ELSE 'FAIR'
    END as HealthStatus
FROM iot.Channels c
LEFT JOIN (
    SELECT 
        ChannelID,
        MAX(CreatedAt) as LastReading,
        COUNT(CASE WHEN CreatedAt >= DATEADD(HOUR, -24, GETUTCDATE()) THEN 1 END) as ReadingsLast24Hours
    FROM iot.SensorReadings
    GROUP BY ChannelID
) lr ON c.ChannelID = lr.ChannelID
LEFT JOIN (
    SELECT 
        ChannelID,
        AVG(QualityScore) as QualityScore
    FROM iot.DataQuality
    WHERE CheckDate >= DATEADD(DAY, -7, GETUTCDATE())
    GROUP BY ChannelID
) dq ON c.ChannelID = dq.ChannelID
WHERE c.IsActive = 1;
GO

-- =============================================
-- View: vw_CrossChannelComparison
-- Description: Compare field averages across channels
-- =============================================
CREATE OR ALTER VIEW iot.vw_CrossChannelComparison AS
SELECT 
    ad.PeriodStart,
    ad.AggregationType,
    MAX(CASE WHEN c.ChannelID = 3 THEN c.ChannelName END) as Channel3Name,
    MAX(CASE WHEN c.ChannelID = 3 THEN ad.Field1Avg END) as Channel3_Field1,
    MAX(CASE WHEN c.ChannelID = 4 THEN c.ChannelName END) as Channel4Name,
    MAX(CASE WHEN c.ChannelID = 4 THEN ad.Field1Avg END) as Channel4_Field1,
    MAX(CASE WHEN c.ChannelID = 9 THEN c.ChannelName END) as Channel9Name,
    MAX(CASE WHEN c.ChannelID = 9 THEN ad.Field1Avg END) as Channel9_Field1,
    MAX(CASE WHEN c.ChannelID = 38629 THEN c.ChannelName END) as Channel38629Name,
    MAX(CASE WHEN c.ChannelID = 38629 THEN ad.Field1Avg END) as Channel38629_Field1,
    MAX(CASE WHEN c.ChannelID = 1417 THEN c.ChannelName END) as Channel1417Name,
    MAX(CASE WHEN c.ChannelID = 1417 THEN ad.Field1Avg END) as Channel1417_Field1
FROM iot.AggregatedData ad
INNER JOIN iot.Channels c ON ad.ChannelID = c.ChannelID
WHERE ad.AggregationType = 'DAILY'
    AND c.IsActive = 1
GROUP BY ad.PeriodStart, ad.AggregationType;
GO

PRINT 'Multi-channel views created successfully!';
PRINT '';
PRINT 'Available views:';
PRINT '  - iot.vw_LatestReadings       : Latest reading from each channel';
PRINT '  - iot.vw_ChannelSummary       : Summary statistics per channel';
PRINT '  - iot.vw_DailyAggregations    : Daily aggregations with channel names';
PRINT '  - iot.vw_ChannelHealth        : Health status of all channels';
PRINT '  - iot.vw_CrossChannelComparison : Compare metrics across channels';
PRINT '';
PRINT 'Example queries:';
PRINT '  SELECT * FROM iot.vw_LatestReadings;';
PRINT '  SELECT * FROM iot.vw_ChannelHealth;';
PRINT '  SELECT * FROM iot.vw_ChannelSummary ORDER BY TotalReadings DESC;';
