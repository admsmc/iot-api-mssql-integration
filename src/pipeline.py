"""
IoT Data Pipeline
Main orchestration script that fetches data from ThingSpeak and loads it into MS SQL
"""
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

from thingspeak_client import ThingSpeakClient
from database import DatabaseConnection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IoTDataPipeline:
    """Main pipeline for processing IoT data"""
    
    def __init__(self):
        """Initialize pipeline with configuration"""
        load_dotenv()
        
        # ThingSpeak configuration
        self.channel_id = os.getenv('THINGSPEAK_CHANNEL_ID')
        self.api_key = os.getenv('THINGSPEAK_API_KEY')
        
        # Database configuration
        self.db_server = os.getenv('DB_SERVER')
        self.db_name = os.getenv('DB_NAME')
        self.db_username = os.getenv('DB_USERNAME')
        self.db_password = os.getenv('DB_PASSWORD')
        self.db_trusted_connection = os.getenv('DB_TRUSTED_CONNECTION', 'False').lower() == 'true'
        
        # Initialize clients
        self.thingspeak_client = None
        self.db_connection = None
        
    def initialize(self) -> bool:
        """
        Initialize API client and database connection
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Initialize ThingSpeak client
            if not self.channel_id:
                logger.error("THINGSPEAK_CHANNEL_ID not configured")
                return False
                
            self.thingspeak_client = ThingSpeakClient(
                channel_id=self.channel_id,
                api_key=self.api_key
            )
            logger.info(f"ThingSpeak client initialized for channel {self.channel_id}")
            
            # Initialize database connection
            if not self.db_server or not self.db_name:
                logger.error("Database configuration incomplete")
                return False
                
            self.db_connection = DatabaseConnection(
                server=self.db_server,
                database=self.db_name,
                username=self.db_username,
                password=self.db_password,
                trusted_connection=self.db_trusted_connection
            )
            
            if not self.db_connection.connect():
                logger.error("Failed to connect to database")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            return False
            
    def sync_channel_metadata(self) -> bool:
        """
        Fetch and store channel metadata
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Syncing channel metadata...")
        
        channel_info = self.thingspeak_client.get_channel_info()
        if not channel_info:
            logger.error("Failed to fetch channel info")
            return False
            
        channel_data = {
            'id': channel_info.get('id'),
            'name': channel_info.get('name'),
            'description': channel_info.get('description'),
            'latitude': channel_info.get('latitude'),
            'longitude': channel_info.get('longitude'),
            'field1': channel_info.get('field1'),
            'field2': channel_info.get('field2'),
            'field3': channel_info.get('field3'),
            'field4': channel_info.get('field4'),
            'field5': channel_info.get('field5'),
            'field6': channel_info.get('field6'),
            'field7': channel_info.get('field7'),
            'field8': channel_info.get('field8'),
        }
        
        return self.db_connection.upsert_channel(channel_data)
        
    def fetch_and_store_data(self, results: int = 100) -> int:
        """
        Fetch sensor data and store in database
        
        Args:
            results: Number of results to fetch
            
        Returns:
            Number of records stored
        """
        logger.info(f"Fetching {results} sensor readings...")
        
        feed_data = self.thingspeak_client.get_channel_feed(results=results)
        if not feed_data:
            logger.error("Failed to fetch channel feed")
            return 0
            
        feeds = feed_data.get('feeds', [])
        if not feeds:
            logger.warning("No feed data available")
            return 0
            
        # Store sensor readings
        inserted = self.db_connection.insert_sensor_readings(
            channel_id=int(self.channel_id),
            feeds=feeds
        )
        
        return inserted
        
    def process_aggregations(self, aggregation_type: str = 'DAILY') -> bool:
        """
        Process data aggregations using stored procedure
        
        Args:
            aggregation_type: Type of aggregation (HOURLY, DAILY, WEEKLY)
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Processing {aggregation_type} aggregations...")
        
        result = self.db_connection.call_stored_procedure(
            'iot.usp_ProcessSensorReadings',
            params=(int(self.channel_id), aggregation_type, None, None)
        )
        
        return result is not None
        
    def calculate_data_quality(self) -> bool:
        """
        Calculate data quality metrics
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Calculating data quality metrics...")
        
        result = self.db_connection.call_stored_procedure(
            'iot.usp_CalculateDataQuality',
            params=(int(self.channel_id), None)
        )
        
        if result:
            logger.info(f"Data quality results: {result}")
            return True
        return False
        
    def run_full_pipeline(self, fetch_results: int = 100):
        """
        Execute the full data pipeline
        
        Args:
            fetch_results: Number of results to fetch from API
        """
        logger.info("=" * 60)
        logger.info("Starting IoT Data Pipeline")
        logger.info("=" * 60)
        
        try:
            # Initialize
            if not self.initialize():
                logger.error("Pipeline initialization failed")
                return
                
            # Sync channel metadata
            if not self.sync_channel_metadata():
                logger.error("Failed to sync channel metadata")
                return
                
            # Fetch and store sensor data
            records_stored = self.fetch_and_store_data(results=fetch_results)
            logger.info(f"Stored {records_stored} new sensor readings")
            
            # Process aggregations
            if records_stored > 0:
                self.process_aggregations('HOURLY')
                self.process_aggregations('DAILY')
                
                # Calculate data quality
                self.calculate_data_quality()
                
            logger.info("=" * 60)
            logger.info("Pipeline completed successfully")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
        finally:
            if self.db_connection:
                self.db_connection.disconnect()


def main():
    """Main entry point"""
    pipeline = IoTDataPipeline()
    pipeline.run_full_pipeline(fetch_results=100)


if __name__ == "__main__":
    main()
