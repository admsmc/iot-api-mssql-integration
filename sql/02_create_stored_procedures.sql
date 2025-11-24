-- Stored Procedures for IoT Data Processing
-- Complex procedures for aggregation, analysis, and data quality monitoring

USE master;
GO

-- =============================================
-- Stored Procedure: usp_ProcessSensorReadings
-- Description: Main procedure to aggregate sensor data and compute statistics
-- =============================================
CREATE OR ALTER PROCEDURE iot.usp_ProcessSensorReadings
    @ChannelID INT,
    @AggregationType NVARCHAR(20), -- 'HOURLY', 'DAILY', 'WEEKLY'
    @StartDate DATETIME2 = NULL,
    @EndDate DATETIME2 = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Set defaults if not provided
    IF @StartDate IS NULL
        SET @StartDate = DATEADD(DAY, -7, GETUTCDATE());
    IF @EndDate IS NULL
        SET @EndDate = GETUTCDATE();
    
    DECLARE @PeriodInterval INT;
    DECLARE @PeriodUnit NVARCHAR(10);
    
    -- Determine aggregation period
    IF @AggregationType = 'HOURLY'
    BEGIN
        SET @PeriodInterval = 1;
        SET @PeriodUnit = 'HOUR';
    END
    ELSE IF @AggregationType = 'DAILY'
    BEGIN
        SET @PeriodInterval = 1;
        SET @PeriodUnit = 'DAY';
    END
    ELSE IF @AggregationType = 'WEEKLY'
    BEGIN
        SET @PeriodInterval = 7;
        SET @PeriodUnit = 'DAY';
    END
    
    -- Temporary table to hold period boundaries
    CREATE TABLE #Periods (
        PeriodStart DATETIME2,
        PeriodEnd DATETIME2
    );
    
    -- Generate time periods
    DECLARE @CurrentStart DATETIME2 = @StartDate;
    WHILE @CurrentStart < @EndDate
    BEGIN
        DECLARE @CurrentEnd DATETIME2;
        
        IF @PeriodUnit = 'HOUR'
            SET @CurrentEnd = DATEADD(HOUR, @PeriodInterval, @CurrentStart);
        ELSE
            SET @CurrentEnd = DATEADD(DAY, @PeriodInterval, @CurrentStart);
            
        INSERT INTO #Periods (PeriodStart, PeriodEnd)
        VALUES (@CurrentStart, @CurrentEnd);
        
        SET @CurrentStart = @CurrentEnd;
    END
    
    -- Process aggregations for each period
    DECLARE @PStart DATETIME2, @PEnd DATETIME2;
    
    DECLARE period_cursor CURSOR FOR
    SELECT PeriodStart, PeriodEnd FROM #Periods;
    
    OPEN period_cursor;
    FETCH NEXT FROM period_cursor INTO @PStart, @PEnd;
    
    WHILE @@FETCH_STATUS = 0
    BEGIN
        -- Merge aggregated data (insert or update)
        MERGE iot.AggregatedData AS target
        USING (
            SELECT
                @ChannelID AS ChannelID,
                @AggregationType AS AggregationType,
                @PStart AS PeriodStart,
                @PEnd AS PeriodEnd,
                AVG(Field1) AS Field1Avg,
                MIN(Field1) AS Field1Min,
                MAX(Field1) AS Field1Max,
                STDEV(Field1) AS Field1StdDev,
                AVG(Field2) AS Field2Avg,
                MIN(Field2) AS Field2Min,
                MAX(Field2) AS Field2Max,
                STDEV(Field2) AS Field2StdDev,
                AVG(Field3) AS Field3Avg,
                MIN(Field3) AS Field3Min,
                MAX(Field3) AS Field3Max,
                STDEV(Field3) AS Field3StdDev,
                AVG(Field4) AS Field4Avg,
                MIN(Field4) AS Field4Min,
                MAX(Field4) AS Field4Max,
                STDEV(Field4) AS Field4StdDev,
                COUNT(*) AS ReadingCount
            FROM iot.SensorReadings
            WHERE ChannelID = @ChannelID
                AND CreatedAt >= @PStart
                AND CreatedAt < @PEnd
        ) AS source
        ON (target.ChannelID = source.ChannelID 
            AND target.AggregationType = source.AggregationType
            AND target.PeriodStart = source.PeriodStart)
        WHEN MATCHED THEN
            UPDATE SET
                Field1Avg = source.Field1Avg,
                Field1Min = source.Field1Min,
                Field1Max = source.Field1Max,
                Field1StdDev = source.Field1StdDev,
                Field2Avg = source.Field2Avg,
                Field2Min = source.Field2Min,
                Field2Max = source.Field2Max,
                Field2StdDev = source.Field2StdDev,
                Field3Avg = source.Field3Avg,
                Field3Min = source.Field3Min,
                Field3Max = source.Field3Max,
                Field3StdDev = source.Field3StdDev,
                Field4Avg = source.Field4Avg,
                Field4Min = source.Field4Min,
                Field4Max = source.Field4Max,
                Field4StdDev = source.Field4StdDev,
                ReadingCount = source.ReadingCount,
                CreatedAt = GETUTCDATE()
        WHEN NOT MATCHED AND source.ReadingCount > 0 THEN
            INSERT (ChannelID, AggregationType, PeriodStart, PeriodEnd,
                    Field1Avg, Field1Min, Field1Max, Field1StdDev,
                    Field2Avg, Field2Min, Field2Max, Field2StdDev,
                    Field3Avg, Field3Min, Field3Max, Field3StdDev,
                    Field4Avg, Field4Min, Field4Max, Field4StdDev,
                    ReadingCount)
            VALUES (source.ChannelID, source.AggregationType, source.PeriodStart, source.PeriodEnd,
                    source.Field1Avg, source.Field1Min, source.Field1Max, source.Field1StdDev,
                    source.Field2Avg, source.Field2Min, source.Field2Max, source.Field2StdDev,
                    source.Field3Avg, source.Field3Min, source.Field3Max, source.Field3StdDev,
                    source.Field4Avg, source.Field4Min, source.Field4Max, source.Field4StdDev,
                    source.ReadingCount);
        
        FETCH NEXT FROM period_cursor INTO @PStart, @PEnd;
    END
    
    CLOSE period_cursor;
    DEALLOCATE period_cursor;
    DROP TABLE #Periods;
    
    RETURN 0;
END
GO

-- =============================================
-- Stored Procedure: usp_DetectAnomalies
-- Description: Detects anomalies using statistical methods (Z-score)
-- =============================================
CREATE OR ALTER PROCEDURE iot.usp_DetectAnomalies
    @ChannelID INT,
    @FieldNumber INT,
    @ThresholdStdDev DECIMAL(5, 2) = 3.0,
    @LookbackDays INT = 30
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @StartDate DATETIME2 = DATEADD(DAY, -@LookbackDays, GETUTCDATE());
    
    -- Calculate statistics for the field
    DECLARE @FieldAvg DECIMAL(18, 6);
    DECLARE @FieldStdDev DECIMAL(18, 6);
    
    -- Dynamic SQL to handle different field numbers
    DECLARE @SQL NVARCHAR(MAX);
    SET @SQL = N'
        SELECT @Avg = AVG(Field' + CAST(@FieldNumber AS NVARCHAR) + N'),
               @StdDev = STDEV(Field' + CAST(@FieldNumber AS NVARCHAR) + N')
        FROM iot.SensorReadings
        WHERE ChannelID = @ChannelID
            AND CreatedAt >= @StartDate
            AND Field' + CAST(@FieldNumber AS NVARCHAR) + N' IS NOT NULL';
    
    EXEC sp_executesql @SQL,
        N'@ChannelID INT, @StartDate DATETIME2, @Avg DECIMAL(18, 6) OUTPUT, @StdDev DECIMAL(18, 6) OUTPUT',
        @ChannelID, @StartDate, @FieldAvg OUTPUT, @FieldStdDev OUTPUT;
    
    -- Return anomalies (readings outside threshold standard deviations)
    SET @SQL = N'
        SELECT 
            ReadingID,
            ChannelID,
            EntryID,
            CreatedAt,
            Field' + CAST(@FieldNumber AS NVARCHAR) + N' AS FieldValue,
            ' + CAST(@FieldAvg AS NVARCHAR(50)) + N' AS FieldAverage,
            ' + CAST(@FieldStdDev AS NVARCHAR(50)) + N' AS FieldStdDev,
            ABS(Field' + CAST(@FieldNumber AS NVARCHAR) + N' - ' + CAST(@FieldAvg AS NVARCHAR(50)) + N') / NULLIF(' + CAST(@FieldStdDev AS NVARCHAR(50)) + N', 0) AS ZScore
        FROM iot.SensorReadings
        WHERE ChannelID = @ChannelID
            AND CreatedAt >= @StartDate
            AND Field' + CAST(@FieldNumber AS NVARCHAR) + N' IS NOT NULL
            AND ABS(Field' + CAST(@FieldNumber AS NVARCHAR) + N' - ' + CAST(@FieldAvg AS NVARCHAR(50)) + N') > ' + CAST(@ThresholdStdDev AS NVARCHAR(10)) + N' * ' + CAST(@FieldStdDev AS NVARCHAR(50)) + N'
        ORDER BY CreatedAt DESC';
    
    EXEC sp_executesql @SQL, N'@ChannelID INT, @StartDate DATETIME2', @ChannelID, @StartDate;
    
    RETURN 0;
END
GO

-- =============================================
-- Stored Procedure: usp_CalculateDataQuality
-- Description: Calculates data quality metrics for a channel
-- =============================================
CREATE OR ALTER PROCEDURE iot.usp_CalculateDataQuality
    @ChannelID INT,
    @CheckDate DATETIME2 = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @CheckDate IS NULL
        SET @CheckDate = CAST(GETUTCDATE() AS DATE);
    
    DECLARE @TotalReadings INT;
    DECLARE @MissingReadings INT;
    DECLARE @OutOfRangeReadings INT;
    DECLARE @AnomaliesDetected INT;
    DECLARE @QualityScore DECIMAL(5, 2);
    
    -- Count total readings for the day
    SELECT @TotalReadings = COUNT(*)
    FROM iot.SensorReadings
    WHERE ChannelID = @ChannelID
        AND CAST(CreatedAt AS DATE) = CAST(@CheckDate AS DATE);
    
    -- Count missing readings (all fields NULL)
    SELECT @MissingReadings = COUNT(*)
    FROM iot.SensorReadings
    WHERE ChannelID = @ChannelID
        AND CAST(CreatedAt AS DATE) = CAST(@CheckDate AS DATE)
        AND Field1 IS NULL 
        AND Field2 IS NULL 
        AND Field3 IS NULL 
        AND Field4 IS NULL;
    
    -- Calculate out-of-range readings (example: negative values where they shouldn't be)
    SELECT @OutOfRangeReadings = COUNT(*)
    FROM iot.SensorReadings
    WHERE ChannelID = @ChannelID
        AND CAST(CreatedAt AS DATE) = CAST(@CheckDate AS DATE)
        AND (Field1 < 0 OR Field2 < 0 OR Field3 < 0 OR Field4 < 0);
    
    -- Estimate anomalies (simplified - could call usp_DetectAnomalies)
    SET @AnomaliesDetected = 0; -- Placeholder
    
    -- Calculate quality score (100 - weighted penalties)
    IF @TotalReadings > 0
    BEGIN
        SET @QualityScore = 100.0 
            - (CAST(@MissingReadings AS DECIMAL) / @TotalReadings * 30.0)
            - (CAST(@OutOfRangeReadings AS DECIMAL) / @TotalReadings * 40.0)
            - (CAST(@AnomaliesDetected AS DECIMAL) / @TotalReadings * 30.0);
        
        IF @QualityScore < 0
            SET @QualityScore = 0;
    END
    ELSE
        SET @QualityScore = 0;
    
    -- Insert quality metrics
    INSERT INTO iot.DataQuality (ChannelID, CheckDate, TotalReadings, MissingReadings,
                                   OutOfRangeReadings, AnomaliesDetected, QualityScore)
    VALUES (@ChannelID, @CheckDate, @TotalReadings, @MissingReadings,
            @OutOfRangeReadings, @AnomaliesDetected, @QualityScore);
    
    -- Return the quality metrics
    SELECT @ChannelID AS ChannelID,
           @CheckDate AS CheckDate,
           @TotalReadings AS TotalReadings,
           @MissingReadings AS MissingReadings,
           @OutOfRangeReadings AS OutOfRangeReadings,
           @AnomaliesDetected AS AnomaliesDetected,
           @QualityScore AS QualityScore;
    
    RETURN 0;
END
GO

-- =============================================
-- Stored Procedure: usp_GetTrendAnalysis
-- Description: Performs trend analysis on sensor data
-- =============================================
CREATE OR ALTER PROCEDURE iot.usp_GetTrendAnalysis
    @ChannelID INT,
    @FieldNumber INT,
    @Days INT = 30
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @StartDate DATETIME2 = DATEADD(DAY, -@Days, GETUTCDATE());
    
    -- Dynamic SQL to analyze specific field
    DECLARE @SQL NVARCHAR(MAX);
    SET @SQL = N'
        WITH DailyStats AS (
            SELECT 
                CAST(CreatedAt AS DATE) AS ReadingDate,
                AVG(Field' + CAST(@FieldNumber AS NVARCHAR) + N') AS DailyAvg,
                MIN(Field' + CAST(@FieldNumber AS NVARCHAR) + N') AS DailyMin,
                MAX(Field' + CAST(@FieldNumber AS NVARCHAR) + N') AS DailyMax,
                COUNT(*) AS ReadingCount
            FROM iot.SensorReadings
            WHERE ChannelID = @ChannelID
                AND CreatedAt >= @StartDate
                AND Field' + CAST(@FieldNumber AS NVARCHAR) + N' IS NOT NULL
            GROUP BY CAST(CreatedAt AS DATE)
        ),
        Trends AS (
            SELECT 
                ReadingDate,
                DailyAvg,
                DailyMin,
                DailyMax,
                ReadingCount,
                DailyAvg - LAG(DailyAvg, 1) OVER (ORDER BY ReadingDate) AS DayOverDayChange,
                AVG(DailyAvg) OVER (ORDER BY ReadingDate ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS SevenDayMA
            FROM DailyStats
        )
        SELECT 
            ReadingDate,
            DailyAvg,
            DailyMin,
            DailyMax,
            ReadingCount,
            DayOverDayChange,
            SevenDayMA,
            CASE 
                WHEN DayOverDayChange > 0 THEN ''Increasing''
                WHEN DayOverDayChange < 0 THEN ''Decreasing''
                ELSE ''Stable''
            END AS Trend
        FROM Trends
        ORDER BY ReadingDate DESC';
    
    EXEC sp_executesql @SQL, N'@ChannelID INT, @StartDate DATETIME2', @ChannelID, @StartDate;
    
    RETURN 0;
END
GO

PRINT 'Stored procedures created successfully!';
