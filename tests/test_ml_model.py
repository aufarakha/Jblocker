#!/usr/bin/env python3
"""
Test script for the ML model functionality
"""

from backend.ml.gambling_detector import GamblingDetector
from backend.ml import model_manager
from backend.core.database_manager import DatabaseManager

def test_ml_model():
    """Test the ML model functionality"""
    print("Testing ML Model")
    print("=" * 50)
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Initialize ML model
    print("1. Initializing ML model...")
    success = model_manager.init_ml_model(db_manager)
    
    if success:
        print("✓ ML model initialized successfully")
    else:
        print("✗ Failed to initialize ML model")
        return False
    
    # Get model information
    print("\n2. Getting model information...")
    model_info = model_manager.get_model_info()
    print(f"Model status: {model_info.get('status')}")
    print(f"Model type: {model_info.get('model_type')}")
    print(f"Features count: {model_info.get('features_count')}")
    print(f"Model file exists: {model_info.get('file_exists')}")
    
    # Test gambling site predictions
    print("\n3. Testing gambling site predictions...")
    gambling_urls = [
        "http://casino-example.com",
        "http://poker-site.net", 
        "http://betting-platform.org",
        "http://judol-site.com",
        "http://taruhan-online.id",
        "http://sbobet-agent.com"
    ]
    
    for url in gambling_urls:
        confidence, is_gambling = model_manager.predict_gambling(url)
        status = "GAMBLING" if is_gambling else "SAFE"
        print(f"  {url}: {status} (confidence: {confidence:.2f})")
    
    # Test safe site predictions
    print("\n4. Testing safe site predictions...")
    safe_urls = [
        "http://google.com",
        "http://wikipedia.org",
        "http://github.com",
        "http://stackoverflow.com",
        "http://news.com",
        "http://education-site.edu"
    ]
    
    for url in safe_urls:
        confidence, is_gambling = model_manager.predict_gambling(url)
        status = "GAMBLING" if is_gambling else "SAFE"
        print(f"  {url}: {status} (confidence: {confidence:.2f})")
    
    # Test with headers and content
    print("\n5. Testing with headers and content...")
    test_url = "http://example-casino.com"
    test_headers = {
        'content-type': 'text/html',
        'title': 'Best Online Casino - Play Slots and Poker'
    }
    test_content = "Welcome to our casino! Play poker, slots, and win big jackpots!"
    
    confidence, is_gambling = model_manager.predict_gambling(test_url, test_headers, test_content)
    status = "GAMBLING" if is_gambling else "SAFE"
    print(f"  {test_url} (with content): {status} (confidence: {confidence:.2f})")
    
    print("\n" + "=" * 50)
    print("ML Model test completed!")
    
    return True

if __name__ == "__main__":
    test_ml_model()