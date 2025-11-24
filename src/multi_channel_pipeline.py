"""
Multi-Channel IoT Data Pipeline
Fetches data from multiple ThingSpeak channels and loads into MS SQL
"""
import os
import sys
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

from thingspeak_client import ThingSpeakClient
from database import DatabaseConnection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChannelConfig:
    """Configuration for a single ThingSpeak channel"""
    
    def __init__(self, channel_id: str, api_key: Optional[str] = None, 
                 enabled: bool = True, description: str = ""):
        self.channel_id = channel_id
        self.api_key = api_key
        self.enabled = enabled
        self.description = description
    
    def __repr__(self):
        return f"Channel({self.channel_id}, enabled={self.enabled})"


class MultiChannelPipeline:
    """Pipeline for processing multiple IoT channels"""
    
    def __init__(self, channels: List[ChannelConfig] = None):
        """
        Initialize multi-channel pipeline
        
        Args:
            channels: List of ChannelConfig objects. If None, loads from environment.
        """
        load_dotenv()
        
        # Channel configurations
        self.channels = channels or self._load_channels_from_env()
        
        # Database configuration
        self.db_server = os.getenv('DB_SERVER')
        self.db_name = os.getenv('DB_NAME')
        self.db_username = os.getenv('DB_USERNAME')
        self.db_password = os.getenv('DB_PASSWORD')
        self.db_trusted_connection = os.getenv('DB_TRUSTED_CONNECTION', 'False').lower() == 'true'
        
        # Initialize database connection (shared across channels)
        self.db_connection = None
        
        # Statistics
        self.stats = {
            'channels_processed': 0,
            'channels_failed': 0,
            'total_records': 0,
            'errors': []
        }
    
    def _load_channels_from_env(self) -> List[ChannelConfig]:
        """
        Load channel configurations from environment variables
        
        Supports:
        - THINGSPEAK_CHANNEL_IDS=9,12397,301051 (comma-separated)
        - THINGSPEAK_API_KEYS=key1,key2,key3 (optional, comma-separated)
        - THINGSPEAK_CHANNEL_ID=9 (backward compatibility for single channel)
        """
        channels = []
        
        # Try multi-channel format first
        channel_ids_str = os.getenv('THINGSPEAK_CHANNEL_IDS')
        api_keys_str = os.getenv('THINGSPEAK_API_KEYS', '')
        
        if channel_ids_str:
            channel_ids = [cid.strip() for cid in channel_ids_str.split(',') if cid.strip()]
            api_keys = [key.strip() for key in api_keys_str.split(',') if key.strip()]
            
            # Pad api_keys list if shorter than channel_ids
            while len(api_keys) < len(channel_ids):
                api_keys.append(None)
            
            for channel_id, api_key in zip(channel_ids, api_keys):
                channels.append(ChannelConfig(
                    channel_id=channel_id,
                    api_key=api_key if api_key else None,
                    enabled=True
                ))
            
            logger.info(f"Loaded {len(channels)} channels from THINGSPEAK_CHANNEL_IDS")
        else:
            # Fall back to single channel format (backward compatibility)
            channel_id = os.getenv('THINGSPEAK_CHANNEL_ID')
            api_key = os.getenv('THINGSPEAK_API_KEY')
            
            if channel_id:
                channels.append(ChannelConfig(
                    channel_id=channel_id,
                    api_key=api_key if api_key else None,
                    enabled=True
                ))
                logger.info("Loaded 1 channel from THINGSPEAK_CHANNEL_ID (legacy mode)")
        
        if not channels:
            logger.warning("No channels configured in environment")
        
        return channels
    
    def initialize_database(self) -> bool:
        """
        Initialize database connection
        
        Returns:
            True if successful, False otherwise
        """
        try:
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
            
            logger.info("Database connection established")
            return True
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            return False
    
    def process_channel(self, channel_config: ChannelConfig, 
                       fetch_results: int = 100) -> Tuple[bool, int]:
        """
        Process a single channel
        
        Args:
            channel_config: Channel configuration
            fetch_results: Number of results to fetch
            
        Returns:
            Tuple of (success: bool, records_inserted: int)
        """
        if not channel_config.enabled:
            logger.info(f"Skipping disabled channel {channel_config.channel_id}")
            return True, 0
        
        logger.info(f"Processing channel {channel_config.channel_id}")
        
        try:
            # Initialize ThingSpeak client for this channel
            client = ThingSpeakClient(
                channel_id=channel_config.channel_id,
                api_key=channel_config.api_key
            )
            
            # Sync channel metadata
            logger.info(f"  Syncing metadata for channel {channel_config.channel_id}...")
            channel_info = client.get_channel_info()
            if not channel_info:
                logger.error(f"  Failed to fetch channel info for {channel_config.channel_id}")
                return False, 0
            
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
            
            if not self.db_connection.upsert_channel(channel_data):
                logger.error(f"  Failed to upsert channel metadata for {channel_config.channel_id}")
                return False, 0
            
            # Fetch and store sensor data
            logger.info(f"  Fetching {fetch_results} readings for channel {channel_config.channel_id}...")
            feed_data = client.get_channel_feed(results=fetch_results)
            if not feed_data:
                logger.error(f"  Failed to fetch feed data for {channel_config.channel_id}")
                return False, 0
            
            feeds = feed_data.get('feeds', [])
            if not feeds:
                logger.warning(f"  No feed data available for channel {channel_config.channel_id}")
                return True, 0
            
            inserted = self.db_connection.insert_sensor_readings(
                channel_id=int(channel_config.channel_id),
                feeds=feeds
            )
            
            logger.info(f"  ✅ Channel {channel_config.channel_id}: {inserted} records inserted")
            
            # Process aggregations for this channel
            self.process_channel_aggregations(channel_config.channel_id)
            
            return True, inserted
            
        except Exception as e:
            logger.error(f"  ❌ Error processing channel {channel_config.channel_id}: {e}", exc_info=True)
            self.stats['errors'].append({
                'channel_id': channel_config.channel_id,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
            return False, 0
    
    def process_channel_aggregations(self, channel_id: str):
        """
        Process aggregations for a single channel
        
        Args:
            channel_id: Channel ID to process
        """
        try:
            logger.info(f"  Processing aggregations for channel {channel_id}...")
            
            # HOURLY aggregation
            self.db_connection.call_stored_procedure(
                'iot.usp_ProcessSensorReadings',
                params=(int(channel_id), 'HOURLY', None, None)
            )
            
            # DAILY aggregation
            self.db_connection.call_stored_procedure(
                'iot.usp_ProcessSensorReadings',
                params=(int(channel_id), 'DAILY', None, None)
            )
            
            logger.info(f"  ✅ Aggregations completed for channel {channel_id}")
            
        except Exception as e:
            logger.warning(f"  ⚠️  Aggregation error for channel {channel_id}: {e}")
    
    def run_full_pipeline(self, fetch_results: int = 100):
        """
        Execute the full multi-channel pipeline
        
        Args:
            fetch_results: Number of results to fetch per channel
        """
        logger.info("=" * 70)
        logger.info("Starting Multi-Channel IoT Data Pipeline")
        logger.info(f"Channels to process: {len(self.channels)}")
        logger.info("=" * 70)
        
        # Reset statistics
        self.stats = {
            'channels_processed': 0,
            'channels_failed': 0,
            'total_records': 0,
            'errors': []
        }
        
        try:
            # Initialize database connection
            if not self.initialize_database():
                logger.error("Pipeline initialization failed")
                return
            
            # Process each channel
            for i, channel_config in enumerate(self.channels, 1):
                logger.info(f"\n[{i}/{len(self.channels)}] Processing {channel_config}")
                
                success, records = self.process_channel(channel_config, fetch_results)
                
                if success:
                    self.stats['channels_processed'] += 1
                    self.stats['total_records'] += records
                else:
                    self.stats['channels_failed'] += 1
            
            # Print summary
            self._print_summary()
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
        finally:
            if self.db_connection:
                self.db_connection.disconnect()
    
    def _print_summary(self):
        """Print pipeline execution summary"""
        logger.info("\n" + "=" * 70)
        logger.info("Pipeline Execution Summary")
        logger.info("=" * 70)
        logger.info(f"Total Channels:       {len(self.channels)}")
        logger.info(f"Successfully Processed: {self.stats['channels_processed']}")
        logger.info(f"Failed:               {self.stats['channels_failed']}")
        logger.info(f"Total Records:        {self.stats['total_records']}")
        
        if self.stats['errors']:
            logger.info(f"\nErrors Encountered:   {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                logger.error(f"  - Channel {error['channel_id']}: {error['error']}")
        
        logger.info("=" * 70)
        
        if self.stats['channels_failed'] == 0:
            logger.info("✅ All channels processed successfully!")
        else:
            logger.warning(f"⚠️  {self.stats['channels_failed']} channel(s) failed")


def main():
    """Main entry point"""
    # Example: Can configure channels programmatically
    # channels = [
    #     ChannelConfig("9", description="Weather Station"),
    #     ChannelConfig("12397", description="Air Quality Monitor"),
    #     ChannelConfig("301051", description="Temperature Sensors"),
    # ]
    # pipeline = MultiChannelPipeline(channels=channels)
    
    # Or use environment variables (recommended)
    pipeline = MultiChannelPipeline()
    pipeline.run_full_pipeline(fetch_results=100)


if __name__ == "__main__":
    main()
