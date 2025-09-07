#!/usr/bin/env python3
"""
Test script to add sample data to NetGuard database
"""

from backend.core.database_manager import DatabaseManager
from datetime import datetime, timedelta
import random

def add_sample_data():
    """Add sample detection and traffic data"""
    db_manager = DatabaseManager()
    
    # Sample gambling URLs
    gambling_urls = [
        "http://casino-example.com",
        "http://poker-site.net", 
        "http://betting-platform.org",
        "http://judol-site.com",
        "http://taruhan-online.id"
    ]
    
    # Sample safe URLs
    safe_urls = [
        "http://google.com",
        "http://wikipedia.org",
        "http://github.com",
        "http://stackoverflow.com",
        "http://news.com"
    ]
    
    print("Adding sample detection data...")
    
    # Add gambling detections
    for i, url in enumerate(gambling_urls):
        confidence = random.uniform(0.7, 0.95)
        db_manager.log_detection(
            url=url,
            confidence=confidence,
            is_gambling=True,
            blocked=confidence > 0.8,
            method="GET",
            status_code=200
        )
        print(f"Added gambling detection: {url} (confidence: {confidence:.2f})")
    
    # Add safe detections
    for i, url in enumerate(safe_urls):
        confidence = random.uniform(0.1, 0.4)
        db_manager.log_detection(
            url=url,
            confidence=confidence,
            is_gambling=False,
            blocked=False,
            method="GET",
            status_code=200
        )
        print(f"Added safe detection: {url} (confidence: {confidence:.2f})")
    
    # Add some blocked sites
    print("\nAdding blocked sites...")
    for url in gambling_urls[:3]:  # Block first 3 gambling sites
        db_manager.add_blocked_site(url, "High confidence gambling detection")
        print(f"Blocked site: {url}")
    
    # Add some network connections
    print("\nAdding network connections...")
    for i in range(10):
        db_manager.log_connection(
            local_ip="192.168.1.100",
            local_port=random.randint(50000, 60000),
            remote_ip=f"203.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            remote_port=random.choice([80, 443, 8080]),
            status="ESTABLISHED",
            pid=random.randint(1000, 9999),
            process_name=random.choice(["chrome.exe", "firefox.exe", "edge.exe"])
        )
    
    # Add some bandwidth history data
    print("\nAdding bandwidth history...")
    from datetime import datetime, timedelta
    current_time = datetime.now()
    
    for i in range(24):  # 24 hours of data
        timestamp = current_time - timedelta(hours=24-i)
        bandwidth = random.uniform(10, 100)  # Random bandwidth between 10-100 Mbps
        connections = random.randint(5, 30)
        
        # Manually insert bandwidth data with specific timestamp
        db_manager.db_path
        import sqlite3
        conn = sqlite3.connect(db_manager.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO bandwidth_history 
            (timestamp, bytes_sent, bytes_recv, bandwidth_mbps, active_connections)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            timestamp.isoformat(),
            random.randint(1000000, 10000000),  # bytes sent
            random.randint(5000000, 50000000),  # bytes received  
            bandwidth,
            connections
        ))
        conn.commit()
        conn.close()
        
        if i % 6 == 0:  # Print every 6 hours
            print(f"  Added bandwidth data for {timestamp.strftime('%Y-%m-%d %H:%M')}: {bandwidth:.1f} Mbps")
    
    # Get and display statistics
    print("\nCurrent statistics:")
    stats = db_manager.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\nSample data added successfully!")
    print("You can now start the application and see the stats on the dashboard.")

if __name__ == "__main__":
    add_sample_data()