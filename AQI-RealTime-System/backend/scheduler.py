"""
Scheduler Module - Background Tasks
Real-Time AQI Prediction System

Handles:
- Periodic AQI data fetching
- Automatic model retraining
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import threading

from data_fetch import fetch_data
from database import save_data, get_training_data, save_model_info
from model import train_model, predict_from_data, get_model


class AQIScheduler:
    """
    Background scheduler for automated tasks
    """
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.is_running = False
        self._lock = threading.Lock()
        
    def _fetch_and_save(self):
        """Fetch AQI data and save to database"""
        with self._lock:
            try:
                print(f"[{datetime.now()}] [FETCH] Fetching AQI data...")
                data = fetch_data()
                
                if data:
                    save_data(data)
                    print(f"[{datetime.now()}] [OK] Data saved: AQI = {data.get('aqi')}")
                    
                    # Also make and save prediction
                    model = get_model()
                    if model.is_trained:
                        predicted = predict_from_data(data)
                        print(f"[{datetime.now()}] [PREDICT] Prediction: {predicted}")
                        
            except Exception as e:
                print(f"[{datetime.now()}] [ERROR] Fetch error: {e}")
    
    def _retrain_model(self):
        """Retrain the GA-KELM model with latest data"""
        with self._lock:
            try:
                print(f"[{datetime.now()}] [TRAIN] Starting model retraining...")
                
                # Get training data from database
                data_list = get_training_data()
                
                if len(data_list) < 20:
                    print(f"[{datetime.now()}] [WARNING] Not enough data for training")
                    return
                
                # Train model
                result = train_model(data_list)
                
                if result:
                    save_model_info(result)
                    print(f"[{datetime.now()}] [OK] Model retrained successfully")
                    
            except Exception as e:
                print(f"[{datetime.now()}] [ERROR] Training error: {e}")
    
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            return
        
        # Fetch data every 15 minutes
        self.scheduler.add_job(
            self._fetch_and_save,
            trigger=IntervalTrigger(minutes=15),
            id='fetch_aqi_data',
            name='Fetch AQI Data',
            replace_existing=True
        )
        
        # Retrain model every 24 hours
        self.scheduler.add_job(
            self._retrain_model,
            trigger=IntervalTrigger(hours=24),
            id='retrain_model',
            name='Retrain GA-KELM Model',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        print("[SCHEDULER] Scheduler started")
        
        # Run initial fetch
        self._fetch_and_save()
    
    def stop(self):
        """Stop the scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            print("[SCHEDULER] Scheduler stopped")
    
    def trigger_fetch(self):
        """Manually trigger data fetch"""
        self._fetch_and_save()
    
    def trigger_retrain(self):
        """Manually trigger model retraining"""
        self._retrain_model()


# Global scheduler instance
scheduler = AQIScheduler()


def start_scheduler():
    """Start the global scheduler"""
    scheduler.start()


def stop_scheduler():
    """Stop the global scheduler"""
    scheduler.stop()


# Test
if __name__ == "__main__":
    print("Testing Scheduler...")
    scheduler.trigger_fetch()
