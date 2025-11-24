# IoT API to MS SQL Integration

A production-ready data pipeline that fetches high-volume IoT sensor data from ThingSpeak's public API and stores it in Microsoft SQL Server with complex data processing using stored procedures.

## Overview

This project demonstrates a complete IoT data integration solution that:

- **Fetches** real-time sensor data from ThingSpeak IoT platform
- **Stores** data in a well-structured MS SQL Server database
- **Processes** data using complex stored procedures for aggregation and analysis
- **Monitors** data quality with automated metrics
- **Detects** anomalies using statistical methods

## Architecture

```
ThingSpeak API → Python Client → MS SQL Server → Stored Procedures
                                       ↓
                           Aggregated Data & Analytics
```

## Features

### Python Components
- **ThingSpeak API Client**: Rate-limited HTTP client with error handling
- **Database Connection Manager**: Robust MS SQL Server connection handling with pyodbc
- **Data Pipeline**: Orchestrates the entire ETL process
- **Type Safety**: Full type hints for better code quality

### Database Schema
- **Channels Table**: Stores IoT channel metadata
- **SensorReadings Table**: Raw time-series sensor data with indexing
- **AggregatedData Table**: Pre-computed hourly/daily/weekly statistics
- **DataQuality Table**: Quality metrics and monitoring

### Stored Procedures
1. **usp_ProcessSensorReadings**: Aggregates sensor data by time periods (hourly/daily/weekly)
2. **usp_DetectAnomalies**: Identifies outliers using Z-score statistical analysis
3. **usp_CalculateDataQuality**: Computes quality scores based on completeness and validity
4. **usp_GetTrendAnalysis**: Performs trend analysis with moving averages

## Prerequisites

- Python 3.8+
- Microsoft SQL Server 2016+ (or Azure SQL Database)
- ODBC Driver 17 for SQL Server (or compatible)
- ThingSpeak account (free public channels available)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd iot-api-mssql-integration
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install ODBC Driver

**macOS:**
```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
brew install msodbcsql17
```

**Linux (Ubuntu/Debian):**
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
sudo add-apt-repository "$(curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list)"
sudo apt-get update
sudo apt-get install -y msodbcsql17
```

**Windows:**
Download from [Microsoft's official site](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

### 5. Configure Environment

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
THINGSPEAK_CHANNEL_ID=9
THINGSPEAK_API_KEY=  # Leave empty for public channels

DB_SERVER=localhost
DB_NAME=IoTSensorDB
DB_USERNAME=sa
DB_PASSWORD=your_secure_password
DB_TRUSTED_CONNECTION=False
```

### 6. Set Up Database

Run the SQL scripts in order:

```bash
# Using sqlcmd (if available)
sqlcmd -S localhost -U sa -P your_password -i sql/01_create_schema.sql
sqlcmd -S localhost -U sa -P your_password -i sql/02_create_stored_procedures.sql
```

Or execute them manually through SQL Server Management Studio (SSMS) or Azure Data Studio.

## Usage

### Basic Usage

Run the complete pipeline:

```bash
python src/pipeline.py
```

This will:
1. Connect to ThingSpeak and fetch the latest 100 sensor readings
2. Store the data in MS SQL Server
3. Run aggregation procedures (hourly and daily)
4. Calculate data quality metrics

### Programmatic Usage

```python
from src.pipeline import IoTDataPipeline

# Initialize pipeline
pipeline = IoTDataPipeline()

# Run full pipeline with 500 records
pipeline.run_full_pipeline(fetch_results=500)
```

### Using Individual Components

#### ThingSpeak Client

```python
from src.thingspeak_client import ThingSpeakClient

client = ThingSpeakClient(channel_id="9")

# Get latest entry
latest = client.get_last_entry()

# Get channel feed
feed = client.get_channel_feed(results=100)

# Get specific field data
field_data = client.get_field_data(field_number=1, results=50)
```

#### Database Operations

```python
from src.database import DatabaseConnection

db = DatabaseConnection(
    server="localhost",
    database="IoTSensorDB",
    username="sa",
    password="your_password"
)

db.connect()

# Execute stored procedure
results = db.call_stored_procedure(
    'iot.usp_ProcessSensorReadings',
    params=(9, 'DAILY', None, None)
)

db.disconnect()
```

## Project Structure

```
iot-api-mssql-integration/
├── src/
│   ├── __init__.py
│   ├── thingspeak_client.py    # API client
│   ├── database.py              # Database operations
│   └── pipeline.py              # Main pipeline orchestration
├── sql/
│   ├── 01_create_schema.sql    # Database schema
│   └── 02_create_stored_procedures.sql  # Stored procedures
├── tests/
│   └── (test files to be added)
├── config/
│   └── (configuration files)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Database Schema Details

### iot.Channels
Stores metadata about ThingSpeak channels.

**Key Columns:**
- `ChannelID`: Unique channel identifier
- `Field1Name` through `Field8Name`: Sensor field names
- `Latitude/Longitude`: Geographic location

### iot.SensorReadings
Time-series data from sensors.

**Key Columns:**
- `ReadingID`: Auto-increment primary key
- `EntryID`: ThingSpeak entry ID
- `CreatedAt`: Timestamp of reading
- `Field1` through `Field8`: Sensor values

**Indexes:**
- `IX_SensorReadings_ChannelID_CreatedAt`: Optimizes time-range queries
- `UQ_ChannelEntry`: Prevents duplicate entries

### iot.AggregatedData
Pre-computed statistics for performance.

**Aggregation Types:**
- `HOURLY`: 1-hour windows
- `DAILY`: 24-hour windows
- `WEEKLY`: 7-day windows

**Metrics per field:**
- Average, Min, Max, Standard Deviation

## Stored Procedures

### usp_ProcessSensorReadings
Aggregates raw sensor data into time-based summaries.

```sql
EXEC iot.usp_ProcessSensorReadings 
    @ChannelID = 9,
    @AggregationType = 'DAILY',
    @StartDate = '2024-01-01',
    @EndDate = '2024-01-31'
```

### usp_DetectAnomalies
Identifies statistical outliers using Z-score method.

```sql
EXEC iot.usp_DetectAnomalies 
    @ChannelID = 9,
    @FieldNumber = 1,
    @ThresholdStdDev = 3.0,
    @LookbackDays = 30
```

### usp_CalculateDataQuality
Computes quality score (0-100) based on:
- Missing readings (30% weight)
- Out-of-range values (40% weight)
- Detected anomalies (30% weight)

```sql
EXEC iot.usp_CalculateDataQuality 
    @ChannelID = 9,
    @CheckDate = '2024-01-15'
```

### usp_GetTrendAnalysis
Performs trend analysis with day-over-day changes and 7-day moving averages.

```sql
EXEC iot.usp_GetTrendAnalysis 
    @ChannelID = 9,
    @FieldNumber = 1,
    @Days = 30
```

## Example ThingSpeak Channels

Here are some public channels to try:

1. **Channel 9**: Weather station data
2. **Channel 12397**: Air quality monitoring
3. **Channel 301051**: Temperature and humidity sensors

Search for more at: https://thingspeak.com/channels/public

## Scheduling

To run the pipeline on a schedule, you can use:

### Cron (Linux/macOS)

```bash
# Edit crontab
crontab -e

# Add line to run every hour
0 * * * * cd /path/to/iot-api-mssql-integration && /path/to/venv/bin/python src/pipeline.py >> logs/pipeline.log 2>&1
```

### Windows Task Scheduler

Create a batch file `run_pipeline.bat`:

```batch
@echo off
cd C:\path\to\iot-api-mssql-integration
call venv\Scripts\activate
python src\pipeline.py
```

Then schedule it using Task Scheduler.

### Python Schedule Library

```python
import schedule
import time
from src.pipeline import IoTDataPipeline

def run_pipeline():
    pipeline = IoTDataPipeline()
    pipeline.run_full_pipeline()

# Run every hour
schedule.every().hour.do(run_pipeline)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## Testing

```bash
# Run tests (when implemented)
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

## Troubleshooting

### ODBC Driver Issues

**Error: "Data source name not found"**
- Verify ODBC driver is installed: `odbcinst -q -d`
- Update driver name in `.env` to match installed version

### Database Connection Issues

**Error: "Login failed for user"**
- Verify SQL Server authentication mode
- Check username/password in `.env`
- Try using trusted connection if on Windows

### ThingSpeak API Issues

**Error: Rate limit exceeded**
- Increase `rate_limit_delay` in ThingSpeakClient
- Use API key for higher rate limits

## Security Best Practices

1. **Never commit `.env` file** - It contains sensitive credentials
2. **Use environment variables** - Don't hardcode credentials
3. **Restrict database permissions** - Use least privilege principle
4. **Enable SSL/TLS** - For database connections in production
5. **Rotate credentials regularly** - Update passwords periodically

## Performance Optimization

1. **Batch Processing**: Insert multiple records in transactions
2. **Indexing**: Indexes on ChannelID and CreatedAt for fast queries
3. **Pre-aggregation**: Stored procedures compute statistics ahead of time
4. **Connection Pooling**: Reuse database connections where possible

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Acknowledgments

- ThingSpeak by MathWorks for the IoT platform
- Microsoft for SQL Server and ODBC drivers
- Python community for excellent libraries

## Support

For issues and questions:
- Open an issue on GitHub
- Check ThingSpeak documentation: https://thingspeak.com/docs
- SQL Server documentation: https://docs.microsoft.com/sql

## Roadmap

- [ ] Add comprehensive unit tests
- [ ] Implement real-time streaming with MQTT
- [ ] Add data visualization dashboard
- [ ] Support for additional IoT platforms
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Monitoring and alerting
- [ ] API endpoint for data access
