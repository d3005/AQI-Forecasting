"""
Database Module - Firebase Realtime Database
Real-Time AQI Prediction System

Firebase is free, easy to setup, and provides real-time sync!
"""

import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Firebase Configuration
FIREBASE_URL = os.getenv("FIREBASE_URL")  # Your Firebase Realtime Database URL
FIREBASE_CRED_PATH = os.getenv("FIREBASE_CRED_PATH", "firebase-credentials.json")

# Initialize Firebase (only once)
_initialized = False

def init_firebase():
    """Initialize Firebase Admin SDK"""
    global _initialized
    
    if _initialized:
        return True
    
    try:
        # Check if credentials file exists
        if os.path.exists(FIREBASE_CRED_PATH):
            cred = credentials.Certificate(FIREBASE_CRED_PATH)
        else:
            # Use environment variable for credentials JSON
            cred_json = os.getenv("FIREBASE_CREDENTIALS")
            if cred_json:
                cred_dict = json.loads(cred_json)
                cred = credentials.Certificate(cred_dict)
            else:
                print("[WARNING] No Firebase credentials found. Using mock mode.")
                return False
        
        firebase_admin.initialize_app(cred, {
            'databaseURL': FIREBASE_URL
        })
        
        _initialized = True
        print("[OK] Firebase Connected Successfully!")
        return True
        
    except Exception as e:
        print(f"[ERROR] Firebase Connection Failed: {e}")
        return False


def get_ref(path: str):
    """Get a Firebase database reference"""
    init_firebase()
    return db.reference(path)


# ============ AQI Records ============

def save_data(data: dict) -> str:
    """Save AQI data to Firebase"""
    try:
        ref = get_ref('records')
        
        # Add timestamp
        data['timestamp'] = datetime.now().isoformat()
        
        # Push creates a unique key
        new_ref = ref.push(data)
        
        print(f"[OK] Data saved with key: {new_ref.key}")
        return new_ref.key
        
    except Exception as e:
        print(f"[ERROR] Error saving data: {e}")
        return None


def get_latest_data() -> dict:
    """Get the most recent AQI reading"""
    try:
        ref = get_ref('records')
        
        # Query last record ordered by timestamp
        snapshot = ref.order_by_child('timestamp').limit_to_last(1).get()
        
        if snapshot:
            for key, value in snapshot.items():
                value['_id'] = key
                return value
        
        return None
        
    except Exception as e:
        print(f"[ERROR] Error getting latest data: {e}")
        return None


def get_historical_data(limit: int = 100) -> list:
    """Get historical AQI readings"""
    try:
        ref = get_ref('records')
        
        # Get all records (no ordering to avoid index requirement)
        snapshot = ref.get()
        
        if not snapshot:
            return []
        
        # Convert to list and add keys
        records = []
        for key, value in snapshot.items():
            if isinstance(value, dict):
                value['_id'] = key
                records.append(value)
        
        # Sort by timestamp descending in Python
        records.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Return only the requested limit
        return records[:limit]
        
    except Exception as e:
        print(f"[ERROR] Error getting historical data: {e}")
        return []


def get_training_data() -> list:
    """Get data for model training"""
    return get_historical_data(500)


# ============ Predictions ============

def save_prediction(prediction: dict) -> str:
    """Save a prediction to Firebase"""
    try:
        ref = get_ref('predictions')
        
        prediction['created_at'] = datetime.now().isoformat()
        new_ref = ref.push(prediction)
        
        return new_ref.key
        
    except Exception as e:
        print(f"[ERROR] Error saving prediction: {e}")
        return None


def get_predictions(limit: int = 24) -> list:
    """Get recent predictions"""
    try:
        ref = get_ref('predictions')
        
        snapshot = ref.order_by_child('created_at').limit_to_last(limit).get()
        
        if not snapshot:
            return []
        
        predictions = []
        for key, value in snapshot.items():
            value['_id'] = key
            predictions.append(value)
        
        predictions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return predictions
        
    except Exception as e:
        print(f"[ERROR] Error getting predictions: {e}")
        return []


# ============ Model Info ============

def save_model_info(model_info: dict) -> str:
    """Save trained model metadata"""
    try:
        ref = get_ref('models')
        
        model_info['trained_at'] = datetime.now().isoformat()
        new_ref = ref.push(model_info)
        
        return new_ref.key
        
    except Exception as e:
        print(f"[ERROR] Error saving model info: {e}")
        return None


def get_latest_model() -> dict:
    """Get the most recent model info"""
    try:
        ref = get_ref('models')
        
        snapshot = ref.order_by_child('trained_at').limit_to_last(1).get()
        
        if snapshot:
            for key, value in snapshot.items():
                value['_id'] = key
                return value
        
        return None
        
    except Exception as e:
        print(f"[ERROR] Error getting latest model: {e}")
        return None


# ============ Test Connection ============

def test_connection() -> bool:
    """Test Firebase connection"""
    try:
        if init_firebase():
            # Try a simple read
            ref = get_ref('/')
            ref.get()
            print("[OK] Firebase connection test passed!")
            return True
        return False
    except Exception as e:
        print(f"[ERROR] Firebase connection test failed: {e}")
        return False


# ============ Mock Mode (for demo without Firebase) ============

_mock_data = {
    'records': [],
    'predictions': [],
    'models': []
}

class MockDatabase:
    """Mock database for demo/testing without Firebase"""
    
    @staticmethod
    def save_data(data: dict) -> str:
        data['_id'] = f"mock_{len(_mock_data['records'])}"
        data['timestamp'] = datetime.now().isoformat()
        _mock_data['records'].insert(0, data)
        return data['_id']
    
    @staticmethod
    def get_latest_data() -> dict:
        return _mock_data['records'][0] if _mock_data['records'] else None
    
    @staticmethod
    def get_historical_data(limit: int = 100) -> list:
        return _mock_data['records'][:limit]
    
    @staticmethod
    def save_prediction(prediction: dict) -> str:
        prediction['_id'] = f"pred_{len(_mock_data['predictions'])}"
        prediction['created_at'] = datetime.now().isoformat()
        _mock_data['predictions'].insert(0, prediction)
        return prediction['_id']
    
    @staticmethod
    def get_predictions(limit: int = 24) -> list:
        return _mock_data['predictions'][:limit]


# Use mock if Firebase not configured
if not FIREBASE_URL or not os.path.exists(FIREBASE_CRED_PATH):
    print("[INFO] Firebase not configured. Using mock database for demo.")
    save_data = MockDatabase.save_data
    get_latest_data = MockDatabase.get_latest_data
    get_historical_data = MockDatabase.get_historical_data
    get_training_data = lambda: MockDatabase.get_historical_data(500)
    save_prediction = MockDatabase.save_prediction
    get_predictions = MockDatabase.get_predictions
    test_connection = lambda: True


# Test
if __name__ == "__main__":
    print("Testing Database...")
    test_connection()
