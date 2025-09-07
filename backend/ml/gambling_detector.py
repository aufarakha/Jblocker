#!/usr/bin/env python3
"""
Machine Learning Model for Gambling Website Detection
Handles model creation, training, prediction, and management
"""

import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from urllib.parse import urlparse
from typing import Tuple, Optional, Dict, List
import numpy as np

class GamblingDetector:
    """Machine learning model for detecting gambling websites"""
    
    def __init__(self, model_path: str = 'models/gambling_detector.pkl'):
        self.model_path = model_path
        self.model = None
        self.db_manager = None
        
        # Ensure models directory exists
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
    def set_db_manager(self, db_manager):
        """Set database manager for getting sensitivity settings"""
        self.db_manager = db_manager
    
    def create_basic_model(self) -> Pipeline:
        """Create a basic gambling detection model with enhanced features"""
        # Enhanced gambling keywords including Indonesian terms
        gambling_keywords = [
            # English gambling terms
            'casino', 'poker', 'betting', 'jackpot', 'slots', 'roulette',
            'blackjack', 'gambling', 'wager', 'lottery', 'bingo', 'dice',
            'sportsbook', 'odds', 'bet365', 'william hill', 'ladbrokes',
            'baccarat', 'sicbo', 'dragon tiger', 'wheel fortune', 'keno',
            
            # Indonesian gambling terms
            'judol', 'judi', 'taruhan', 'kasino', 'slot', 'bandar',
            'togel', 'bola tangkas', 'domino', 'capsa', 'ceme', 'gaple',
            'sabung ayam', 'tembak ikan', 'live casino',
            
            # Common gambling site patterns
            'deposit', 'withdraw', 'bonus', 'promo', 'jackpot',
            'spin', 'win', 'lucky', 'fortune', 'chance', 'prize',
            'bet now', 'play now', 'register', 'sign up bonus',
            
            # Gambling-related domains and keywords
            'sbobet', 'maxbet', 'ibcbet', 'cmd368', 'mansion88',
            'dafabet', 'fun88', 'w88', 'm88', 'agen', 'agent'
        ]
        
        safe_keywords = [
            # Safe website categories
            'news', 'education', 'shopping', 'social', 'business', 'health',
            'technology', 'sports', 'entertainment', 'government', 'bank',
            'wikipedia', 'google', 'facebook', 'youtube', 'amazon',
            'microsoft', 'apple', 'netflix', 'linkedin', 'twitter',
            'instagram', 'whatsapp', 'telegram', 'email', 'weather',
            
            # Educational and informational
            'learn', 'study', 'course', 'tutorial', 'guide', 'help',
            'information', 'knowledge', 'research', 'academic',
            
            # Business and professional
            'company', 'corporate', 'professional', 'service', 'support',
            'contact', 'about', 'career', 'job', 'work',
            
            # E-commerce (non-gambling)
            'shop', 'store', 'buy', 'sell', 'product', 'price',
            'cart', 'checkout', 'shipping', 'delivery'
        ]
        
        # Create training data
        texts = gambling_keywords + safe_keywords
        labels = [1] * len(gambling_keywords) + [0] * len(safe_keywords)
        
        # Create pipeline with TF-IDF and Naive Bayes
        model = Pipeline([
            ('tfidf', TfidfVectorizer(
                ngram_range=(1, 3),  # Use 1-3 word combinations
                max_features=3000,   # Increased feature count
                stop_words='english',
                lowercase=True,
                min_df=1,           # Minimum document frequency
                max_df=0.95         # Maximum document frequency
            )),
            ('classifier', MultinomialNB(alpha=0.1))
        ])
        
        model.fit(texts, labels)
        return model
    
    def load_or_create_model(self) -> bool:
        """Load existing model or create new one"""
        try:
            if os.path.exists(self.model_path):
                print(f"Loading existing ML model from {self.model_path}")
                self.model = joblib.load(self.model_path)
                return True
            else:
                print("Creating new ML model...")
                self.model = self.create_basic_model()
                self.save_model()
                return True
        except Exception as e:
            print(f"Error loading/creating ML model: {e}")
            return False
    
    def save_model(self) -> bool:
        """Save the current model to disk"""
        try:
            if self.model:
                joblib.dump(self.model, self.model_path)
                print(f"Model saved to {self.model_path}")
                return True
            return False
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
    
    def extract_features_from_url(self, url: str, headers: Optional[Dict] = None, 
                                 content: Optional[str] = None) -> str:
        """Extract features from URL, headers, and content for ML classification"""
        try:
            # URL-based features
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            path = parsed_url.path.lower()
            query = parsed_url.query.lower()
            
            # Combine text for analysis
            text_content = f"{domain} {path} {query}"
            
            # Add domain-specific features
            domain_parts = domain.split('.')
            text_content += " " + " ".join(domain_parts)
            
            if headers:
                # Include relevant headers
                header_text = " ".join([f"{k.lower()}:{str(v).lower()}" 
                                       for k, v in headers.items() 
                                       if k.lower() in ['content-type', 'server', 'title', 'description']])
                text_content += " " + header_text
            
            if content:
                # Extract meaningful content (first 3000 chars for better analysis)
                content_snippet = content[:3000] if isinstance(content, str) else str(content)[:3000]
                text_content += " " + content_snippet.lower()
            
            return text_content
            
        except Exception as e:
            print(f"Error extracting features: {e}")
            return url.lower()  # Fallback to just URL
    
    def predict_gambling(self, url: str, headers: Optional[Dict] = None, 
                        content: Optional[str] = None) -> Tuple[float, bool]:
        """Predict if a URL is gambling-related using ML model"""
        if self.model is None:
            print("Warning: ML model not loaded")
            return 0.5, False
        
        try:
            # Extract features
            features = self.extract_features_from_url(url, headers, content)
            
            # Get prediction probability
            probabilities = self.model.predict_proba([features])
            gambling_prob = probabilities[0][1] if len(probabilities[0]) > 1 else 0.5
            
            # Get sensitivity setting from database
            sensitivity = 0.5  # Default sensitivity
            if self.db_manager:
                sensitivity_setting = self.db_manager.get_setting('sensitivity')
                if sensitivity_setting:
                    sensitivity = float(sensitivity_setting) / 100.0
            
            is_gambling = gambling_prob > sensitivity
            
            return float(gambling_prob), is_gambling
            
        except Exception as e:
            print(f"Error in ML prediction: {e}")
            return 0.5, False
    
    def add_training_data(self, url: str, is_gambling: bool, 
                         headers: Optional[Dict] = None, 
                         content: Optional[str] = None) -> bool:
        """Add new training data for model improvement"""
        try:
            # In a production system, you would:
            # 1. Store this feedback in a training dataset
            # 2. Periodically retrain the model with accumulated feedback
            # 3. Validate the new model before deployment
            
            # For now, we'll just log the feedback
            features = self.extract_features_from_url(url, headers, content)
            print(f"Training feedback received: {url} -> {'gambling' if is_gambling else 'safe'}")
            
            # TODO: Implement incremental learning or batch retraining
            return True
            
        except Exception as e:
            print(f"Error adding training data: {e}")
            return False
    
    def get_model_info(self) -> Dict:
        """Get information about the current model"""
        if not self.model:
            return {'status': 'not_loaded'}
        
        try:
            # Get model parameters
            tfidf = self.model.named_steps['tfidf']
            classifier = self.model.named_steps['classifier']
            
            return {
                'status': 'loaded',
                'model_type': 'Naive Bayes with TF-IDF',
                'features_count': len(tfidf.get_feature_names_out()) if hasattr(tfidf, 'get_feature_names_out') else 'unknown',
                'ngram_range': tfidf.ngram_range,
                'max_features': tfidf.max_features,
                'alpha': classifier.alpha,
                'model_path': self.model_path,
                'file_exists': os.path.exists(self.model_path)
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def retrain_model(self, training_data: List[Tuple[str, bool]]) -> bool:
        """Retrain the model with new data"""
        try:
            if not training_data:
                return False
            
            # Extract features and labels
            texts = []
            labels = []
            
            for url, is_gambling in training_data:
                features = self.extract_features_from_url(url)
                texts.append(features)
                labels.append(1 if is_gambling else 0)
            
            # Retrain the model
            self.model.fit(texts, labels)
            
            # Save the updated model
            return self.save_model()
            
        except Exception as e:
            print(f"Error retraining model: {e}")
            return False
    
    def validate_model(self, test_data: List[Tuple[str, bool]]) -> Dict:
        """Validate model performance on test data"""
        try:
            if not test_data or not self.model:
                return {'error': 'No test data or model not loaded'}
            
            correct_predictions = 0
            total_predictions = len(test_data)
            
            for url, actual_is_gambling in test_data:
                _, predicted_is_gambling = self.predict_gambling(url)
                if predicted_is_gambling == actual_is_gambling:
                    correct_predictions += 1
            
            accuracy = correct_predictions / total_predictions
            
            return {
                'accuracy': accuracy,
                'correct_predictions': correct_predictions,
                'total_predictions': total_predictions,
                'accuracy_percentage': round(accuracy * 100, 2)
            }
            
        except Exception as e:
            return {'error': str(e)}