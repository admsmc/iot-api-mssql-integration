#!/usr/bin/env python3
"""
Channel Capacity Calculator
Calculates maximum number of ThingSpeak channels based on constraints
"""

def calculate_capacity(
    api_requests_per_second=1.0,
    schedule_interval_minutes=60,
    processing_overhead_seconds=2.0,
    records_per_channel=100,
    storage_limit_gb=None
):
    """
    Calculate maximum channel capacity
    
    Args:
        api_requests_per_second: API rate limit (1.0 for free, 3-4 for paid)
        schedule_interval_minutes: How often pipeline runs
        processing_overhead_seconds: Database/processing time per channel
        records_per_channel: Records fetched per run
        storage_limit_gb: Database storage limit (None = unlimited)
    """
    print("="*70)
    print("ThingSpeak Channel Capacity Calculator")
    print("="*70)
    
    # API Constraints
    requests_per_channel = 2  # metadata + feed data
    api_time_per_channel = requests_per_channel / api_requests_per_second
    total_time_per_channel = api_time_per_channel + processing_overhead_seconds
    
    print(f"\n📡 API Configuration:")
    print(f"  Requests per second: {api_requests_per_second}")
    print(f"  Requests per channel: {requests_per_channel}")
    print(f"  API time per channel: {api_time_per_channel:.1f}s")
    print(f"  Processing overhead: {processing_overhead_seconds:.1f}s")
    print(f"  Total time per channel: {total_time_per_channel:.1f}s")
    
    # Time Constraints
    available_time_seconds = schedule_interval_minutes * 60
    max_channels_by_time = int(available_time_seconds / total_time_per_channel)
    
    print(f"\n⏱️  Time Constraints:")
    print(f"  Schedule interval: {schedule_interval_minutes} minutes")
    print(f"  Available time: {available_time_seconds} seconds")
    print(f"  Max channels (time): {max_channels_by_time}")
    
    # Storage Constraints
    if storage_limit_gb:
        # Rough estimates
        kb_per_reading = 0.5  # ~500 bytes per reading
        readings_per_day = records_per_channel  # Assuming daily runs
        readings_per_year = readings_per_day * 365
        mb_per_channel_per_year = (readings_per_year * kb_per_reading) / 1024
        gb_per_channel_per_year = mb_per_channel_per_year / 1024
        
        max_channels_by_storage = int(storage_limit_gb / gb_per_channel_per_year)
        
        print(f"\n💾 Storage Constraints:")
        print(f"  Storage limit: {storage_limit_gb} GB")
        print(f"  Per channel per year: {mb_per_channel_per_year:.1f} MB")
        print(f"  Max channels (1 year): {max_channels_by_storage}")
    else:
        max_channels_by_storage = float('inf')
        print(f"\n💾 Storage: No limit specified")
    
    # Final Recommendation
    max_channels = min(max_channels_by_time, max_channels_by_storage)
    safe_margin = 0.8  # 80% of theoretical max
    recommended_max = int(max_channels * safe_margin)
    
    print(f"\n✅ Capacity Summary:")
    print(f"  Theoretical maximum: {max_channels}")
    print(f"  Recommended maximum: {recommended_max} (with 20% safety margin)")
    
    # Usage scenarios
    print(f"\n📊 Usage Scenarios:")
    scenarios = [
        (5, "Every 5 minutes"),
        (15, "Every 15 minutes"),
        (60, "Every hour"),
        (1440, "Once daily"),
    ]
    
    for interval, description in scenarios:
        available = interval * 60
        max_ch = int(available / total_time_per_channel)
        recommended_ch = int(max_ch * safe_margin)
        print(f"  {description:20s}: {recommended_ch:4d} channels (max: {max_ch})")
    
    print("="*70)
    
    return {
        'max_channels_by_time': max_channels_by_time,
        'max_channels_by_storage': max_channels_by_storage,
        'recommended_max': recommended_max
    }


def main():
    print("\n" + "="*70)
    print("Scenario 1: Free Tier, Hourly Pipeline")
    print("="*70)
    calculate_capacity(
        api_requests_per_second=1.0,
        schedule_interval_minutes=60,
        processing_overhead_seconds=2.0,
        storage_limit_gb=10  # 10 GB database
    )
    
    print("\n\n" + "="*70)
    print("Scenario 2: Paid API, 15-Minute Pipeline")
    print("="*70)
    calculate_capacity(
        api_requests_per_second=3.0,
        schedule_interval_minutes=15,
        processing_overhead_seconds=2.0,
        storage_limit_gb=50  # 50 GB database
    )
    
    print("\n\n" + "="*70)
    print("Scenario 3: Free Tier, Daily Batch")
    print("="*70)
    calculate_capacity(
        api_requests_per_second=1.0,
        schedule_interval_minutes=1440,  # 24 hours
        processing_overhead_seconds=2.0,
        storage_limit_gb=100  # 100 GB database
    )
    
    print("\n\n" + "="*70)
    print("Custom Scenario")
    print("="*70)
    print("Edit this script to calculate for your specific requirements:")
    print("  - api_requests_per_second: 1.0 (free) or 3-4 (paid)")
    print("  - schedule_interval_minutes: How often you run the pipeline")
    print("  - processing_overhead_seconds: Database write time (~2s typical)")
    print("  - storage_limit_gb: Your database storage limit")
    print("="*70)


if __name__ == "__main__":
    main()
