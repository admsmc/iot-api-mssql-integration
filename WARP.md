# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a production-ready IoT data integration pipeline that fetches high-volume sensor data from ThingSpeak's public API and stores it in Microsoft SQL Server with complex data processing using stored procedures. The architecture follows a three-layer pattern: API Client → Python Pipeline → SQL Server + Stored Procedures.

## Common Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### Database Setup
```bash
# Initialize database schema (using sqlcmd if available)
sqlcmd -S localhost -U sa -P your_password -i sql/01_create_schema.sql
sqlcmd -S localhost -U sa -P your_password -i sql/02_create_stored_procedures.sql

# Alternative: Execute SQL files manually through SSMS or Azure Data Studio
```

### Running the Pipeline
```bash
# Run the full pipeline (fetch 100 records)
python src/pipeline.py

# Run from project root (important for imports)
cd /Users/andrewmathers/projects/iot-api-mssql-integration
python src/pipeline.py
```

### Testing
```bash
# Run tests (when implemented)
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Troubleshooting Commands
```bash
# Check ODBC drivers installed
odbcinst -q -d

# Test ThingSpeak API connectivity
curl "https://api.thingspeak.com/channels/9/feeds.json?results=1"

# Verify Python can import pyodbc
python -c "import pyodbc; print(pyodbc.drivers())"
```

## High-Level Architecture

### Data Flow
```
1. ThingSpeak API (External)
   ↓ HTTP GET requests (rate-limited)
2. ThingSpeakClient (src/thingspeak_client.py)
   ↓ Returns JSON feed data
3. IoTDataPipeline (src/pipeline.py)
   ↓ Orchestrates ETL
4. DatabaseConnection (src/database.py)
   ↓ pyodbc connection
5. MS SQL Server (Local/Azure)
   ↓ Raw data → iot.SensorReadings
6. Stored Procedures (sql/02_create_stored_procedures.sql)
   ↓ Complex aggregation & analysis
7. Aggregated Data (iot.AggregatedData, iot.DataQuality)
```

### Key Architectural Patterns

**Rate Limiting**: `ThingSpeakClient` implements per-request rate limiting with configurable delays to prevent API throttling.

**Batch Processing**: Database inserts use batch transactions with duplicate detection via `UQ_ChannelEntry` constraint.

**MERGE Pattern**: Both channel metadata and aggregated data use SQL MERGE operations for idempotent upserts.

**Stored Procedure Pattern**: Complex aggregations (hourly/daily/weekly) and statistical analysis (Z-score anomaly detection) are implemented in T-SQL stored procedures for performance.

**Schema Organization**: All IoT-related tables live in the `iot` schema for namespace isolation.

### Database Schema Key Points

**iot.Channels**: Channel metadata (Field1Name-Field8Name store sensor field labels)

**iot.SensorReadings**: Time-series raw data with composite unique constraint on (ChannelID, EntryID) to prevent duplicates. Critical indexes: `IX_SensorReadings_ChannelID_CreatedAt` for time-range queries.

**iot.AggregatedData**: Pre-computed statistics (avg, min, max, stddev) per time period (HOURLY/DAILY/WEEKLY) for up to 4 fields. Unique constraint on (ChannelID, AggregationType, PeriodStart).

**iot.DataQuality**: Quality metrics including missing readings, out-of-range values, anomalies detected, and 0-100 quality score.

### Stored Procedures

**usp_ProcessSensorReadings**: Generates time period boundaries, iterates with cursor, computes aggregations per period using MERGE. Takes @ChannelID, @AggregationType ('HOURLY'|'DAILY'|'WEEKLY'), optional @StartDate/@EndDate.

**usp_DetectAnomalies**: Uses dynamic SQL to compute mean/stddev for specified field, returns readings outside threshold Z-score (default 3.0 standard deviations).

**usp_CalculateDataQuality**: Computes quality score weighted by missing readings (30%), out-of-range values (40%), and anomalies (30%).

**usp_GetTrendAnalysis**: Performs day-over-day change analysis with 7-day moving averages.

### Python Module Architecture

**src/thingspeak_client.py**: Stateful API client with rate limiting. Methods: `get_channel_feed()`, `get_last_entry()`, `get_field_data()`, `get_channel_info()`. Handles HTTP errors gracefully.

**src/database.py**: Database connection manager using pyodbc. Key methods: `connect()`, `upsert_channel()`, `insert_sensor_readings()` (batch with duplicate skip), `call_stored_procedure()` (returns list of dicts).

**src/pipeline.py**: Main orchestration class `IoTDataPipeline`. Loads config from .env, coordinates: `sync_channel_metadata()` → `fetch_and_store_data()` → `process_aggregations()` → `calculate_data_quality()`.

## Development Patterns

### Adding New Stored Procedures

1. Add procedure definition to `sql/02_create_stored_procedures.sql` using `CREATE OR ALTER PROCEDURE iot.usp_YourProcName`
2. Add wrapper method in `DatabaseConnection` class: `self.db_connection.call_stored_procedure('iot.usp_YourProcName', params=(...))`
3. Call from pipeline orchestration in `IoTDataPipeline` class

### Adding New ThingSpeak Operations

1. Add method to `ThingSpeakClient` class following pattern: `_rate_limit()` → `requests.get()` → error handling → return JSON or None
2. Update pipeline to consume new method

### Error Handling Pattern

All API and database operations return `None` or `False` on error with logged exceptions. Pipeline checks return values before proceeding. Use `try/except` with `logger.error()` and rollback transactions on database failures.

### Type Hints

All function signatures include type hints. Use `Optional[T]` for nullable returns, `Dict`, `List[Dict]`, etc. for structured data.

## Important Constraints

**API Rate Limits**: ThingSpeak free tier limits to ~1 request/second. Production code uses `rate_limit_delay=1.0` by default.

**ODBC Driver**: Requires "ODBC Driver 17 for SQL Server" or compatible. On macOS: `brew install msodbcsql17`. Driver name is configurable in `DatabaseConnection`.

**Connection String**: Uses SQL auth by default. For Windows auth, set `DB_TRUSTED_CONNECTION=True` in .env and omit username/password.

**Field Limits**: ThingSpeak supports up to 8 fields per channel. Schema mirrors this (Field1-Field8).

**Duplicate Prevention**: `insert_sensor_readings()` catches `pyodbc.IntegrityError` on unique constraint violation and continues (skip duplicates).

**Aggregation Windows**: Stored procedures use cursor-based iteration over time periods. For large date ranges, this can be slow; consider batching by month.

## Environment Variables

See `.env.example` for required variables:
- `THINGSPEAK_CHANNEL_ID`: Channel to fetch from (e.g., "9" for weather station)
- `THINGSPEAK_API_KEY`: Only needed for private channels (leave empty for public)
- `DB_SERVER`: SQL Server hostname (e.g., "localhost" or Azure endpoint)
- `DB_NAME`: Database name (default "IoTSensorDB")
- `DB_USERNAME` / `DB_PASSWORD`: SQL authentication credentials
- `DB_TRUSTED_CONNECTION`: "True" for Windows auth, "False" for SQL auth

## Testing Strategy

**Unit Tests** (to be implemented): Mock `requests.get()` for `ThingSpeakClient`, mock `pyodbc.connect()` for `DatabaseConnection`.

**Integration Tests** (to be implemented): Use testcontainers or local SQL Server instance, verify end-to-end pipeline with sample data.

**Stored Procedure Tests**: Execute procedures with known test data, verify aggregation math and anomaly detection logic.

## Known Issues & Gotchas

**Import Path**: Must run `python src/pipeline.py` from project root, not from within src/ directory, due to relative imports in pipeline.py.

**NULL Handling**: `_safe_float()` method converts empty strings and None to SQL NULL. Fields with invalid numeric data are silently NULLed.

**Timezone**: All timestamps use `GETUTCDATE()` in SQL and ThingSpeak returns ISO 8601 UTC timestamps.

**Cursor Leak**: Stored procedures use cursors; ensure proper CLOSE/DEALLOCATE even on error paths.

**Dynamic SQL Injection**: `usp_DetectAnomalies` uses parameterized dynamic SQL but field numbers are CAST to NVARCHAR directly - ensure field numbers are validated as integers 1-8.
