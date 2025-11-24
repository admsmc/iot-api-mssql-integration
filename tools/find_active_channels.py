#!/usr/bin/env python3
"""
Find active public ThingSpeak channels for testing
Tests a list of known public channel IDs
"""
import sys
import os
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from thingspeak_client import ThingSpeakClient

# List of known public ThingSpeak channels
KNOWN_CHANNELS = [
    9,        # Home weather station
    12397,    # MathWorks Weather Station
    38629,    # Temperature monitoring
    49281,    # Environmental sensors
    9088,     # Weather data
    1417,     # Solar monitoring
    12345,    # Test channel
    301051,   # Temperature/Humidity
    98209,    # Air quality
    1455803,  # Weather station
    433033,   # Environmental
    501923,   # IoT demo
    1976416,  # Sensor data
    140612,   # Weather
    266256,   # Temperature
]

def check_channel(channel_id):
    """Check if a channel is active and accessible"""
    try:
        client = ThingSpeakClient(channel_id=str(channel_id), rate_limit_delay=0.5)
        
        # Get channel info
        info = client.get_channel_info()
        if not info:
            return None
        
        # Get last entry to check activity
        last_entry = client.get_last_entry()
        if not last_entry:
            return None
        
        # Parse timestamp
        created_at = last_entry.get('created_at')
        if not created_at:
            return None
        
        # Check how recent
        last_update = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        age_hours = (datetime.now(timezone.utc) - last_update).total_seconds() / 3600
        
        # Count fields
        field_count = sum(1 for i in range(1, 9) if info.get(f'field{i}'))
        
        return {
            'channel_id': channel_id,
            'name': info.get('name', 'Unknown'),
            'description': info.get('description', '')[:50],
            'last_entry_id': last_entry.get('entry_id'),
            'last_update': created_at,
            'age_hours': age_hours,
            'fields': field_count,
            'active': age_hours < 168  # Active if updated in last week
        }
        
    except Exception as e:
        print(f"  Error checking {channel_id}: {e}")
        return None

def main():
    print("="*70)
    print("Searching for Active Public ThingSpeak Channels")
    print("="*70)
    
    active_channels = []
    inactive_channels = []
    
    for channel_id in KNOWN_CHANNELS:
        print(f"\nChecking channel {channel_id}...", end=" ")
        result = check_channel(channel_id)
        
        if result:
            if result['active']:
                print(f"✅ ACTIVE")
                print(f"  Name: {result['name']}")
                print(f"  Last update: {result['age_hours']:.1f} hours ago")
                print(f"  Fields: {result['fields']}")
                active_channels.append(result)
            else:
                print(f"⚠️  INACTIVE ({result['age_hours']:.0f} hours ago)")
                inactive_channels.append(result)
        else:
            print("❌ NOT ACCESSIBLE")
    
    # Print summary
    print("\n" + "="*70)
    print("Summary")
    print("="*70)
    print(f"Active channels (< 7 days): {len(active_channels)}")
    print(f"Inactive channels: {len(inactive_channels)}")
    print(f"Not accessible: {len(KNOWN_CHANNELS) - len(active_channels) - len(inactive_channels)}")
    
    if active_channels:
        print("\n" + "="*70)
        print("Top 10 Active Channels (by recency)")
        print("="*70)
        
        # Sort by most recent
        active_channels.sort(key=lambda x: x['age_hours'])
        top_10 = active_channels[:10]
        
        print("\nChannel IDs for .env configuration:")
        print("THINGSPEAK_CHANNEL_IDS=" + ",".join(str(ch['channel_id']) for ch in top_10))
        
        print("\n\nDetailed list:")
        for i, ch in enumerate(top_10, 1):
            print(f"\n{i}. Channel {ch['channel_id']}: {ch['name']}")
            print(f"   Description: {ch['description']}")
            print(f"   Last update: {ch['age_hours']:.1f} hours ago")
            print(f"   Fields: {ch['fields']}")
            print(f"   Last entry: {ch['last_entry_id']}")
    else:
        print("\n⚠️  No active channels found. Using default channels:")
        print("THINGSPEAK_CHANNEL_IDS=9,12397")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
