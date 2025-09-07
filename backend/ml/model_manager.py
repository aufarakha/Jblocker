#!/usr/bin/env python3
"""
ML Model Manager - Interface for machine learning operations
"""

from .gambling_detector import GamblingDetector
from typing import Tuple, Optional, Dict

# Global instance
gambling_detector = GamblingDetector()

def init_ml_model(db_manager=None) -> bool:
    """Initialize the ML model"""
    if db_manager:
        gambling_detector.set_db_manager(db_manager)
    return gambling_detector.load_or_create_model()

def predict_gambling(url: str, headers: Optional[Dict] = None, 
                    content: Optional[str] = None) -> Tuple[float, bool]:
    """Predict if a URL is gambling-related"""
    return gambling_detector.predict_gambling(url, headers, content)

def get_model_info() -> Dict:
    """Get model information"""
    return gambling_detector.get_model_info()

def add_training_feedback(url: str, is_gambling: bool, 
                         headers: Optional[Dict] = None, 
                         content: Optional[str] = None) -> bool:
    """Add training feedback"""
    return gambling_detector.add_training_data(url, is_gambling, headers, content)

def retrain_model(training_data) -> bool:
    """Retrain the model with new data"""
    return gambling_detector.retrain_model(training_data)

def validate_model(test_data) -> Dict:
    """Validate model performance"""
    return gambling_detector.validate_model(test_data)