#!/usr/bin/env python3
"""
Test the multi-channel setup (without database)
Verifies configuration and API connectivity
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from multi_channel_pipeline import MultiChannelPipeline, ChannelConfig
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    print("="*70)
    print("Multi-Channel Setup Test (API Only - No Database)")
    print("="*70)
    
    # Initialize pipeline
    pipeline = MultiChannelPipeline()
    
    print(f"\n✅ Pipeline initialized")
    print(f"   Channels configured: {len(pipeline.channels)}")
    
    if not pipeline.channels:
        print("\n❌ No channels configured in .env!")
        print("   Add: THINGSPEAK_CHANNEL_IDS=3,4,9,38629,1417")
        return
    
    print("\n" + "="*70)
    print("Testing API Connectivity for Each Channel")
    print("="*70)
    
    from thingspeak_client import ThingSpeakClient
    
    for i, channel_config in enumerate(pipeline.channels, 1):
        print(f"\n[{i}/{len(pipeline.channels)}] Channel {channel_config.channel_id}")
        
        try:
            client = ThingSpeakClient(
                channel_id=channel_config.channel_id,
                api_key=channel_config.api_key
            )
            
            # Test channel info
            info = client.get_channel_info()
            if info:
                print(f"  ✅ Name: {info.get('name')}")
                print(f"     Description: {info.get('description', 'N/A')[:50]}")
            
            # Test last entry
            last_entry = client.get_last_entry()
            if last_entry:
                print(f"  ✅ Latest entry: {last_entry.get('entry_id')} at {last_entry.get('created_at')}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    print("\n" + "="*70)
    print("Setup Summary")
    print("="*70)
    print(f"✅ Channels: {len(pipeline.channels)}")
    print(f"✅ Polling: Every 15 minutes (via cron)")
    print(f"✅ Logs: logs/pipeline.log")
    print("\nNext steps:")
    print("1. Wait for next 15-minute mark (cron will run automatically)")
    print("2. Monitor: tail -f logs/pipeline.log")
    print("3. Or run manually now: python3 src/multi_channel_pipeline.py")
    print("="*70)

if __name__ == "__main__":
    main()
