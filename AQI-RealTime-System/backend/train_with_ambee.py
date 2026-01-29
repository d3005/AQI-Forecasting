"""
Fetch real historical AQI data from Ambee API and train GA-KELM model
Ambee provides high-quality air quality data with historical analysis
"""
import requests
import time
from datetime import datetime, timedelta
from model import train_model, get_model_info, get_model
from database import save_data

# Ambee API Configuration
AMBEE_API_KEY = "c85176e0b52f74d7ac727fbd6d0277c7bb16cac82bd9a23fc7958fe125723706"
AMBEE_BASE_URL = "https://api.ambeedata.com"

# Headers for Ambee API
HEADERS = {
    "x-api-key": AMBEE_API_KEY,
    "Content-type": "application/json"
}

# Indian cities with coordinates for data collection
CITIES = [
    {"name": "Delhi", "lat": 28.6139, "lon": 77.2090},
    {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
    {"name": "Bangalore", "lat": 12.9716, "lon": 77.5946},
    {"name": "Hyderabad", "lat": 17.3850, "lon": 78.4867},
    {"name": "Chennai", "lat": 13.0827, "lon": 80.2707},
    {"name": "Kolkata", "lat": 22.5726, "lon": 88.3639},
    {"name": "Pune", "lat": 18.5204, "lon": 73.8567},
    {"name": "Ahmedabad", "lat": 23.0225, "lon": 72.5714},
    {"name": "Jaipur", "lat": 26.9124, "lon": 75.7873},
    {"name": "Lucknow", "lat": 26.8467, "lon": 80.9462},
    {"name": "Visakhapatnam", "lat": 17.6868, "lon": 83.2185},
    {"name": "Ongole", "lat": 15.5057, "lon": 80.0499},
    {"name": "Vijayawada", "lat": 16.5062, "lon": 80.6480},
    {"name": "Nagpur", "lat": 21.1458, "lon": 79.0882},
    {"name": "Bhopal", "lat": 23.2599, "lon": 77.4126},
    {"name": "Patna", "lat": 25.5941, "lon": 85.1376},
    {"name": "Varanasi", "lat": 25.3176, "lon": 82.9739},
    {"name": "Agra", "lat": 27.1767, "lon": 78.0081},
    {"name": "Chandigarh", "lat": 30.7333, "lon": 76.7794},
    {"name": "Coimbatore", "lat": 11.0168, "lon": 76.9558},
]


def fetch_current_aqi(lat: float, lon: float, city_name: str) -> dict:
    """Fetch current AQI from Ambee for coordinates"""
    try:
        url = f"{AMBEE_BASE_URL}/latest/by-lat-lng"
        params = {"lat": lat, "lng": lon}
        
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        
        if response.status_code != 200:
            print(f"  [SKIP] {city_name}: HTTP {response.status_code}")
            return None
        
        data = response.json()
        
        if "stations" not in data or len(data["stations"]) == 0:
            print(f"  [SKIP] {city_name}: No station data")
            return None
        
        station = data["stations"][0]
        
        result = {
            "aqi": station.get("AQI", 0),
            "pm25": station.get("PM25", 0),
            "pm10": station.get("PM10", 0),
            "no2": station.get("NO2", 0),
            "o3": station.get("OZONE", 0),
            "so2": station.get("SO2", 0),
            "co": station.get("CO", 0),
            "city": city_name,
            "latitude": lat,
            "longitude": lon,
            "source": "Ambee",
            "timestamp": datetime.now().isoformat()
        }
        
        # Get category
        aqi = result["aqi"]
        if aqi <= 50:
            result["category"] = "Good"
        elif aqi <= 100:
            result["category"] = "Moderate"
        elif aqi <= 150:
            result["category"] = "Unhealthy for Sensitive Groups"
        elif aqi <= 200:
            result["category"] = "Unhealthy"
        elif aqi <= 300:
            result["category"] = "Very Unhealthy"
        else:
            result["category"] = "Hazardous"
        
        return result
        
    except Exception as e:
        print(f"  [ERROR] {city_name}: {e}")
        return None


def fetch_historical_aqi(lat: float, lon: float, city_name: str, from_date: str, to_date: str) -> list:
    """Fetch historical AQI from Ambee"""
    try:
        url = f"{AMBEE_BASE_URL}/history/by-lat-lng"
        params = {
            "lat": lat,
            "lng": lon,
            "from": from_date,
            "to": to_date
        }
        
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"  [SKIP] {city_name} history: HTTP {response.status_code}")
            return []
        
        data = response.json()
        
        if "history" not in data:
            return []
        
        results = []
        for entry in data["history"]:
            result = {
                "aqi": entry.get("AQI", 0),
                "pm25": entry.get("PM25", 0),
                "pm10": entry.get("PM10", 0),
                "no2": entry.get("NO2", 0),
                "o3": entry.get("OZONE", 0),
                "so2": entry.get("SO2", 0),
                "co": entry.get("CO", 0),
                "city": city_name,
                "latitude": lat,
                "longitude": lon,
                "source": "Ambee Historical",
                "timestamp": entry.get("time", datetime.now().isoformat())
            }
            
            aqi = result["aqi"]
            if aqi <= 50:
                result["category"] = "Good"
            elif aqi <= 100:
                result["category"] = "Moderate"
            elif aqi <= 150:
                result["category"] = "Unhealthy for Sensitive Groups"
            elif aqi <= 200:
                result["category"] = "Unhealthy"
            elif aqi <= 300:
                result["category"] = "Very Unhealthy"
            else:
                result["category"] = "Hazardous"
            
            results.append(result)
        
        return results
        
    except Exception as e:
        print(f"  [ERROR] {city_name} history: {e}")
        return []


def fetch_all_cities_current():
    """Fetch current AQI from all cities"""
    all_data = []
    
    print("\n[FETCH] Fetching current AQI data from Ambee API...")
    print("-" * 60)
    
    for city in CITIES:
        result = fetch_current_aqi(city["lat"], city["lon"], city["name"])
        if result and result["aqi"] > 0:
            all_data.append(result)
            save_data(result)
            print(f"  [OK] {city['name']}: AQI={result['aqi']}, PM2.5={result['pm25']}")
        
        # Rate limiting
        time.sleep(0.5)
    
    print("-" * 60)
    print(f"[DONE] Fetched {len(all_data)} current data points")
    
    return all_data


def fetch_historical_for_cities():
    """Fetch historical data for major cities"""
    all_data = []
    
    # Get last 7 days of data
    to_date = datetime.now()
    from_date = to_date - timedelta(days=7)
    
    from_str = from_date.strftime("%Y-%m-%d %H:%M:%S")
    to_str = to_date.strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"\n[FETCH] Fetching historical data ({from_str[:10]} to {to_str[:10]})...")
    print("-" * 60)
    
    # Fetch for major cities only (to avoid rate limits)
    major_cities = CITIES[:10]
    
    for city in major_cities:
        results = fetch_historical_aqi(city["lat"], city["lon"], city["name"], from_str, to_str)
        if results:
            for r in results:
                if r["aqi"] > 0:
                    all_data.append(r)
                    save_data(r)
            print(f"  [OK] {city['name']}: {len(results)} historical records")
        
        # Rate limiting
        time.sleep(1)
    
    print("-" * 60)
    print(f"[DONE] Fetched {len(all_data)} historical data points")
    
    return all_data


def train_with_ambee_data():
    """Fetch all available data and train the model"""
    print("=" * 60)
    print("  GA-KELM Model Training with Ambee AQI Data")
    print("=" * 60)
    
    all_data = []
    
    # 1. Fetch current data from all cities
    current_data = fetch_all_cities_current()
    all_data.extend(current_data)
    
    # 2. Try to fetch historical data (if API plan allows)
    print("\n[INFO] Attempting to fetch historical data...")
    historical_data = fetch_historical_for_cities()
    all_data.extend(historical_data)
    
    print(f"\n[DATA] Total data points collected: {len(all_data)}")
    
    if len(all_data) < 20:
        print("[WARN] Not enough data. Using existing database records...")
        # The data is already saved, so we can use the /train endpoint
    
    # Train the model
    print("\n[TRAIN] Training GA-KELM model...")
    result = train_model(all_data)
    
    print("\n" + "=" * 60)
    print("  Training Result")
    print("=" * 60)
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    # Get final model info
    print("\n[INFO] Model Status:")
    model = get_model()
    print(f"  Trained: {model.is_trained}")
    if model.is_trained:
        print(f"  RMSE: {model.training_rmse:.4f}")
        print(f"  R2 Score: {model.training_r2:.4f}")
        print(f"  Data Count: {model.data_count}")
        print(f"  Trained At: {model.trained_at}")
    
    print("\n[SUCCESS] Model training complete!")
    
    return result


if __name__ == "__main__":
    train_with_ambee_data()
