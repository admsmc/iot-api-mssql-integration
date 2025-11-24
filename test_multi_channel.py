#!/usr/bin/env python3
"""
Test script for multi-channel ThingSpeak API connectivity
Tests 3 public channels without database
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from thingspeak_client import ThingSpeakClient

def test_channel(channel_id: str, description: str):
    """Test a single channel"""
    print(f"\n{'='*70}")
    print(f"Testing Channel {channel_id}: {description}")
    print('='*70)
    
    client = ThingSpeakClient(channel_id=channel_id)
    
    # Get channel info
    channel_info = client.get_channel_info()
    if not channel_info:
        print(f"❌ Failed to fetch channel {channel_id}")
        return False
    
    print(f"✅ Name: {channel_info.get('name')}")
    print(f"   Description: {channel_info.get('description')}")
    print(f"   Location: {channel_info.get('latitude')}, {channel_info.get('longitude')}")
    
    # Show field names
    fields = []
    for i in range(1, 9):
        field_name = channel_info.get(f'field{i}')
        if field_name:
            fields.append(f"Field{i}: {field_name}")
    
    if fields:
        print(f"   Fields: {', '.join(fields[:3])}{'...' if len(fields) > 3 else ''}")
    
    # Get latest entry
    last_entry = client.get_last_entry()
    if last_entry:
        print(f"   Latest Entry: ID={last_entry.get('entry_id')}, Time={last_entry.get('created_at')}")
        
        # Show first few field values
        for i in range(1, 4):
            value = last_entry.get(f'field{i}')
            if value:
                print(f"     Field{i} = {value}")
    
    # Get recent feed count
    feed_data = client.get_channel_feed(results=5)
    if feed_data:
        feed_count = len(feed_data.get('feeds', []))
        print(f"   Recent Readings: {feed_count} records retrieved")
    
    return True

def main():
    print("="*70)
    print("Multi-Channel ThingSpeak API Test")
    print("Testing 3 Popular Public Channels")
    print("="*70)
    
    # Test multiple public channels
    channels = [
        ("9", "Home Weather Station"),
        ("12397", "Air Quality Monitoring"),
        ("301051", "Temperature & Humidity Sensors"),
    ]
    
    successful = 0
    failed = 0
    
    for channel_id, description in channels:
        if test_channel(channel_id, description):
            successful += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n{'='*70}")
    print("Test Summary")
    print("="*70)
    print(f"Channels Tested: {len(channels)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n✅ All channels are accessible and working!")
        print("\nTo use multi-channel mode, update your .env:")
        print("  THINGSPEAK_CHANNEL_IDS=9,12397,301051")
        print("\nThen run:")
        print("  python3 src/multi_channel_pipeline.py")
    else:
        print(f"\n⚠️  {failed} channel(s) failed")
    
    print("="*70)

if __name__ == "__main__":
    main()
