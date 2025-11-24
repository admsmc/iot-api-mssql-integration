-- IoT Sensor Data Database Schema
-- This script creates the necessary tables and indexes for storing ThingSpeak IoT data

-- Create database (uncomment if needed)
-- CREATE DATABASE IoTSensorDB;
-- GO
-- USE IoTSensorDB;
-- GO

-- Create schema for IoT data
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'iot')
BEGIN
    EXEC('CREATE SCHEMA iot');
END
GO

-- Channels table: stores information about ThingSpeak channels
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Channels' AND schema_id = SCHEMA_ID('iot'))
BEGIN
    CREATE TABLE iot.Channels (
        ChannelID INT PRIMARY KEY,
        ChannelName NVARCHAR(255) NOT NULL,
        Description NVARCHAR(MAX),
        Latitude DECIMAL(10, 8),
        Longitude DECIMAL(11, 8),
        Field1Name NVARCHAR(100),
        Field2Name NVARCHAR(100),
        Field3Name NVARCHAR(100),
        Field4Name NVARCHAR(100),
        Field5Name NVARCHAR(100),
        Field6Name NVARCHAR(100),
        Field7Name NVARCHAR(100),
        Field8Name NVARCHAR(100),
        CreatedAt DATETIME2 DEFAULT GETUTCDATE(),
        UpdatedAt DATETIME2 DEFAULT GETUTCDATE(),
        IsActive BIT DEFAULT 1
    );
END
GO

-- SensorReadings table: stores raw sensor data from ThingSpeak feeds
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'SensorReadings' AND schema_id = SCHEMA_ID('iot'))
BEGIN
    CREATE TABLE iot.SensorReadings (
        ReadingID BIGINT IDENTITY(1,1) PRIMARY KEY,
        ChannelID INT NOT NULL,
        EntryID BIGINT NOT NULL,
        CreatedAt DATETIME2 NOT NULL,
        Field1 DECIMAL(18, 6),
        Field2 DECIMAL(18, 6),
        Field3 DECIMAL(18, 6),
        Field4 DECIMAL(18, 6),
        Field5 DECIMAL(18, 6),
        Field6 DECIMAL(18, 6),
        Field7 DECIMAL(18, 6),
        Field8 DECIMAL(18, 6),
        Latitude DECIMAL(10, 8),
        Longitude DECIMAL(11, 8),
        Elevation DECIMAL(10, 2),
        Status NVARCHAR(50),
        ImportedAt DATETIME2 DEFAULT GETUTCDATE(),
        CONSTRAINT FK_SensorReadings_Channels FOREIGN KEY (ChannelID) 
            REFERENCES iot.Channels(ChannelID),
        CONSTRAINT UQ_ChannelEntry UNIQUE (ChannelID, EntryID)
    );
END
GO

-- Create indexes for better query performance
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_SensorReadings_ChannelID_CreatedAt')
BEGIN
    CREATE NONCLUSTERED INDEX IX_SensorReadings_ChannelID_CreatedAt 
    ON iot.SensorReadings(ChannelID, CreatedAt DESC);
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_SensorReadings_CreatedAt')
BEGIN
    CREATE NONCLUSTERED INDEX IX_SensorReadings_CreatedAt 
    ON iot.SensorReadings(CreatedAt DESC);
END
GO

-- AggregatedData table: stores pre-computed aggregations for faster reporting
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'AggregatedData' AND schema_id = SCHEMA_ID('iot'))
BEGIN
    CREATE TABLE iot.AggregatedData (
        AggregationID BIGINT IDENTITY(1,1) PRIMARY KEY,
        ChannelID INT NOT NULL,
        AggregationType NVARCHAR(20) NOT NULL, -- 'HOURLY', 'DAILY', 'WEEKLY'
        PeriodStart DATETIME2 NOT NULL,
        PeriodEnd DATETIME2 NOT NULL,
        Field1Avg DECIMAL(18, 6),
        Field1Min DECIMAL(18, 6),
        Field1Max DECIMAL(18, 6),
        Field1StdDev DECIMAL(18, 6),
        Field2Avg DECIMAL(18, 6),
        Field2Min DECIMAL(18, 6),
        Field2Max DECIMAL(18, 6),
        Field2StdDev DECIMAL(18, 6),
        Field3Avg DECIMAL(18, 6),
        Field3Min DECIMAL(18, 6),
        Field3Max DECIMAL(18, 6),
        Field3StdDev DECIMAL(18, 6),
        Field4Avg DECIMAL(18, 6),
        Field4Min DECIMAL(18, 6),
        Field4Max DECIMAL(18, 6),
        Field4StdDev DECIMAL(18, 6),
        ReadingCount INT NOT NULL,
        CreatedAt DATETIME2 DEFAULT GETUTCDATE(),
        CONSTRAINT FK_AggregatedData_Channels FOREIGN KEY (ChannelID) 
            REFERENCES iot.Channels(ChannelID),
        CONSTRAINT UQ_Aggregation UNIQUE (ChannelID, AggregationType, PeriodStart)
    );
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_AggregatedData_ChannelID_Type_Period')
BEGIN
    CREATE NONCLUSTERED INDEX IX_AggregatedData_ChannelID_Type_Period 
    ON iot.AggregatedData(ChannelID, AggregationType, PeriodStart DESC);
END
GO

-- DataQuality table: tracks data quality metrics and anomalies
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'DataQuality' AND schema_id = SCHEMA_ID('iot'))
BEGIN
    CREATE TABLE iot.DataQuality (
        QualityID BIGINT IDENTITY(1,1) PRIMARY KEY,
        ChannelID INT NOT NULL,
        CheckDate DATETIME2 NOT NULL,
        TotalReadings INT NOT NULL,
        MissingReadings INT NOT NULL,
        OutOfRangeReadings INT NOT NULL,
        AnomaliesDetected INT NOT NULL,
        QualityScore DECIMAL(5, 2), -- 0-100 score
        Notes NVARCHAR(MAX),
        CreatedAt DATETIME2 DEFAULT GETUTCDATE(),
        CONSTRAINT FK_DataQuality_Channels FOREIGN KEY (ChannelID) 
            REFERENCES iot.Channels(ChannelID)
    );
END
GO

PRINT 'Database schema created successfully!';
