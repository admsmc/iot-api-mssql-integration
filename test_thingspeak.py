#!/usr/bin/env python3
"""
Quick test script to verify ThingSpeak API connectivity
"""
import sys
import os
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from thingspeak_client import ThingSpeakClient

def main():
    load_dotenv()
    
    channel_id = os.getenv('THINGSPEAK_CHANNEL_ID')
    api_key = os.getenv('THINGSPEAK_API_KEY')
    
    print("=" * 60)
    print("ThingSpeak API Connection Test")
    print("=" * 60)
    print(f"Channel ID: {channel_id}")
    print(f"API Key: {'(set)' if api_key else '(not set - using public access)'}")
    print()
    
    # Initialize client
    client = ThingSpeakClient(channel_id=channel_id, api_key=api_key)
    
    # Test 1: Get channel info
    print("Test 1: Fetching channel information...")
    channel_info = client.get_channel_info()
    if channel_info:
        print(f"✅ Channel Name: {channel_info.get('name')}")
        print(f"   Description: {channel_info.get('description')}")
        print(f"   Location: {channel_info.get('latitude')}, {channel_info.get('longitude')}")
        print(f"   Field 1: {channel_info.get('field1')}")
        print(f"   Field 2: {channel_info.get('field2')}")
        print(f"   Last Entry ID: {channel_info.get('last_entry_id')}")
    else:
        print("❌ Failed to fetch channel info")
        return False
    
    print()
    
    # Test 2: Get last entry
    print("Test 2: Fetching last entry...")
    last_entry = client.get_last_entry()
    if last_entry:
        print(f"✅ Entry ID: {last_entry.get('entry_id')}")
        print(f"   Timestamp: {last_entry.get('created_at')}")
        print(f"   Field 1: {last_entry.get('field1')}")
        print(f"   Field 2: {last_entry.get('field2')}")
    else:
        print("❌ Failed to fetch last entry")
        return False
    
    print()
    
    # Test 3: Get channel feed (5 records)
    print("Test 3: Fetching recent feed data (5 records)...")
    feed_data = client.get_channel_feed(results=5)
    if feed_data:
        feeds = feed_data.get('feeds', [])
        print(f"✅ Retrieved {len(feeds)} records")
        if feeds:
            print(f"   First entry: ID={feeds[0].get('entry_id')}, Date={feeds[0].get('created_at')}")
            print(f"   Last entry:  ID={feeds[-1].get('entry_id')}, Date={feeds[-1].get('created_at')}")
    else:
        print("❌ Failed to fetch feed data")
        return False
    
    print()
    print("=" * 60)
    print("✅ All tests passed! ThingSpeak API is working correctly.")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
