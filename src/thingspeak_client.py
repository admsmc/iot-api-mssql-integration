"""
ThingSpeak IoT API Client
Fetches real-time sensor data from ThingSpeak public channels
"""
import requests
import time
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ThingSpeakClient:
    """Client for interacting with ThingSpeak IoT API"""
    
    BASE_URL = "https://api.thingspeak.com"
    
    def __init__(self, channel_id: str, api_key: Optional[str] = None, rate_limit_delay: float = 1.0):
        """
        Initialize ThingSpeak client
        
        Args:
            channel_id: ThingSpeak channel ID
            api_key: Optional API key for private channels
            rate_limit_delay: Delay between API calls in seconds
        """
        self.channel_id = channel_id
        self.api_key = api_key
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Implement rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
        
    def get_channel_feed(self, results: int = 100) -> Optional[Dict]:
        """
        Get channel feed with latest sensor readings
        
        Args:
            results: Number of results to retrieve (max 8000)
            
        Returns:
            Dictionary containing channel data and feeds
        """
        self._rate_limit()
        
        url = f"{self.BASE_URL}/channels/{self.channel_id}/feeds.json"
        params = {"results": results}
        
        if self.api_key:
            params["api_key"] = self.api_key
            
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Successfully fetched {len(data.get('feeds', []))} records from channel {self.channel_id}")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching channel feed: {e}")
            return None
            
    def get_last_entry(self) -> Optional[Dict]:
        """
        Get the most recent entry from the channel
        
        Returns:
            Dictionary containing the latest sensor reading
        """
        self._rate_limit()
        
        url = f"{self.BASE_URL}/channels/{self.channel_id}/feeds/last.json"
        params = {}
        
        if self.api_key:
            params["api_key"] = self.api_key
            
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Successfully fetched last entry from channel {self.channel_id}")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching last entry: {e}")
            return None
            
    def get_field_data(self, field_number: int, results: int = 100) -> Optional[List[Dict]]:
        """
        Get data for a specific field
        
        Args:
            field_number: Field number (1-8)
            results: Number of results to retrieve
            
        Returns:
            List of field data entries
        """
        self._rate_limit()
        
        url = f"{self.BASE_URL}/channels/{self.channel_id}/fields/{field_number}.json"
        params = {"results": results}
        
        if self.api_key:
            params["api_key"] = self.api_key
            
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            feeds = data.get('feeds', [])
            logger.info(f"Successfully fetched {len(feeds)} records for field {field_number}")
            return feeds
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching field data: {e}")
            return None
            
    def get_channel_info(self) -> Optional[Dict]:
        """
        Get channel metadata and information
        
        Returns:
            Dictionary containing channel information
        """
        self._rate_limit()
        
        url = f"{self.BASE_URL}/channels/{self.channel_id}.json"
        params = {}
        
        if self.api_key:
            params["api_key"] = self.api_key
            
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Successfully fetched channel info for {self.channel_id}")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching channel info: {e}")
            return None
