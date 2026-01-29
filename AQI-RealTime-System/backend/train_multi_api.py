"""
Multi-API AQI Data Fetcher and GA-KELM Model Trainer
Sources: Ambee, Azure Maps, WAQI APIs
"""
import requests
import time
from datetime import datetime, timedelta
from model import train_model, get_model_info, get_model
from database import save_data

# ============ API KEYS ============
AMBEE_API_KEY = "c85176e0b52f74d7ac727fbd6d0277c7bb16cac82bd9a23fc7958fe125723706"
WAQI_API_KEY = "c573cdb300b84975dd16d507414ec2dc84804d22"
AZURE_MAPS_KEY = None  # Set this if you have Azure Maps subscription

# ============ CITIES ============
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
    {"name": "Kochi", "lat": 9.9312, "lon": 76.2673},
    {"name": "Thiruvananthapuram", "lat": 8.5241, "lon": 76.9366},
    {"name": "Guwahati", "lat": 26.1445, "lon": 91.7362},
    {"name": "Bhubaneswar", "lat": 20.2961, "lon": 85.8245},
    {"name": "Raipur", "lat": 21.2514, "lon": 81.6296},
]


def get_aqi_category(aqi):
    """Get AQI category based on value"""
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        return "Unhealthy"
    elif aqi <= 300:
        return "Very Unhealthy"
    else:
        return "Hazardous"


# ============ AMBEE API ============
def fetch_from_ambee(lat, lon, city_name):
    """Fetch current AQI from Ambee API"""
    try:
        url = "https://api.ambeedata.com/latest/by-lat-lng"
        headers = {"x-api-key": AMBEE_API_KEY, "Content-type": "application/json"}
        params = {"lat": lat, "lng": lon}
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        if "stations" not in data or len(data["stations"]) == 0:
            return None
        
        station = data["stations"][0]
        
        return {
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
            "category": get_aqi_category(station.get("AQI", 0)),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"    Ambee error for {city_name}: {e}")
        return None


# ============ WAQI API ============
def fetch_from_waqi(lat, lon, city_name):
    """Fetch current AQI from WAQI API"""
    try:
        url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={WAQI_API_KEY}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("status") != "ok":
            return None
        
        aqi_data = data["data"]
        iaqi = aqi_data.get("iaqi", {})
        
        aqi = aqi_data.get("aqi", 0)
        if isinstance(aqi, str):
            aqi = 0
        
        return {
            "aqi": int(aqi),
            "pm25": iaqi.get("pm25", {}).get("v", 0),
            "pm10": iaqi.get("pm10", {}).get("v", 0),
            "no2": iaqi.get("no2", {}).get("v", 0),
            "o3": iaqi.get("o3", {}).get("v", 0),
            "so2": iaqi.get("so2", {}).get("v", 0),
            "co": iaqi.get("co", {}).get("v", 0),
            "city": city_name,
            "latitude": lat,
            "longitude": lon,
            "source": "WAQI",
            "category": get_aqi_category(int(aqi)),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"    WAQI error for {city_name}: {e}")
        return None


# ============ AZURE MAPS API ============
def fetch_from_azure(lat, lon, city_name):
    """Fetch current AQI from Azure Maps API"""
    if not AZURE_MAPS_KEY:
        return None
    
    try:
        url = "https://atlas.microsoft.com/weather/airQuality/current/json"
        params = {
            "api-version": "1.1",
            "subscription-key": AZURE_MAPS_KEY,
            "query": f"{lat},{lon}",
            "pollutants": "true",
            "language": "en"
        }
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        if "results" not in data or len(data["results"]) == 0:
            return None
        
        result = data["results"][0]
        pollutants = {p["type"]: p.get("concentration", {}).get("value", 0) 
                      for p in result.get("pollutants", [])}
        
        # Azure uses different AQI scale, normalize to EPA
        aqi = result.get("index", 0)
        
        return {
            "aqi": aqi,
            "pm25": pollutants.get("PM2.5", 0),
            "pm10": pollutants.get("PM10", 0),
            "no2": pollutants.get("NO2", 0),
            "o3": pollutants.get("O3", 0),
            "so2": pollutants.get("SO2", 0),
            "co": pollutants.get("CO", 0),
            "city": city_name,
            "latitude": lat,
            "longitude": lon,
            "source": "Azure Maps",
            "category": get_aqi_category(aqi),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"    Azure error for {city_name}: {e}")
        return None


# ============ MAIN COLLECTOR ============
def collect_all_data():
    """Collect data from all APIs for all cities"""
    all_data = []
    
    print("\n" + "=" * 60)
    print("  Multi-API AQI Data Collection")
    print("=" * 60)
    
    for city in CITIES:
        city_data = []
        name = city["name"]
        lat, lon = city["lat"], city["lon"]
        
        print(f"\n[{name}]")
        
        # Try Ambee
        ambee_data = fetch_from_ambee(lat, lon, name)
        if ambee_data and ambee_data["aqi"] > 0:
            city_data.append(ambee_data)
            print(f"  Ambee: AQI={ambee_data['aqi']}, PM2.5={ambee_data['pm25']}")
        
        time.sleep(0.3)
        
        # Try WAQI
        waqi_data = fetch_from_waqi(lat, lon, name)
        if waqi_data and waqi_data["aqi"] > 0:
            city_data.append(waqi_data)
            print(f"  WAQI:  AQI={waqi_data['aqi']}, PM2.5={waqi_data['pm25']}")
        
        time.sleep(0.3)
        
        # Try Azure (if key available)
        if AZURE_MAPS_KEY:
            azure_data = fetch_from_azure(lat, lon, name)
            if azure_data and azure_data["aqi"] > 0:
                city_data.append(azure_data)
                print(f"  Azure: AQI={azure_data['aqi']}, PM2.5={azure_data['pm25']}")
            time.sleep(0.3)
        
        # Save all valid data
        for data in city_data:
            save_data(data)
            all_data.append(data)
    
    print("\n" + "-" * 60)
    print(f"[TOTAL] Collected {len(all_data)} data points from {len(CITIES)} cities")
    
    return all_data


def train_with_multi_api():
    """Main function: collect data and train model"""
    print("=" * 60)
    print("  GA-KELM Training with Multi-API Data")
    print("  Sources: Ambee, WAQI" + (", Azure Maps" if AZURE_MAPS_KEY else ""))
    print("=" * 60)
    
    # Collect data
    all_data = collect_all_data()
    
    if len(all_data) < 20:
        print("\n[WARN] Not enough new data, will use existing database records")
    
    # Train
    print("\n[TRAIN] Training GA-KELM model...")
    result = train_model(all_data)
    
    # Results
    print("\n" + "=" * 60)
    print("  Training Results")
    print("=" * 60)
    
    model = get_model()
    if model.is_trained:
        print(f"  Status: TRAINED")
        print(f"  R2 Score: {model.training_r2:.4f} ({model.training_r2*100:.1f}% accuracy)")
        print(f"  RMSE: {model.training_rmse:.4f}")
        print(f"  Data Points: {model.data_count}")
        print(f"  Optimal C: {model.best_params.get('C', 0):.4f}")
        print(f"  Optimal Gamma: {model.best_params.get('gamma', 0):.6f}")
    else:
        print("  Status: NOT TRAINED")
        print(f"  Result: {result}")
    
    print("\n[DONE] Training complete!")
    return result


if __name__ == "__main__":
    train_with_multi_api()
