"""
Fetch real AQI data from WAQI API and train GA-KELM model
Uses World Air Quality Index (aqicn.org) API for real data
"""
import requests
import time
from datetime import datetime
from model import train_model, get_model_info
from database import save_data

# WAQI API Token
WAQI_TOKEN = "c573cdb300b84975dd16d507414ec2dc84804d22"
WAQI_BASE_URL = "https://api.waqi.info"

# Indian cities to fetch data from (for diverse training)
CITIES = [
    "ongole",
    "visakhapatnam", 
    "hyderabad",
    "vijayawada",
    "chennai",
    "bangalore",
    "mumbai",
    "delhi",
    "kolkata",
    "pune",
    "ahmedabad",
    "jaipur",
    "lucknow",
    "kanpur",
    "nagpur",
    "patna",
    "indore",
    "bhopal",
    "coimbatore",
    "kochi"
]

def fetch_city_aqi(city: str) -> dict:
    """Fetch current AQI data from WAQI for a city"""
    try:
        url = f"{WAQI_BASE_URL}/feed/{city}/?token={WAQI_TOKEN}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("status") != "ok":
            print(f"  [SKIP] {city}: {data.get('data', 'Unknown error')}")
            return None
        
        aqi_data = data["data"]
        
        # Extract pollutant values from iaqi
        iaqi = aqi_data.get("iaqi", {})
        
        result = {
            "aqi": aqi_data.get("aqi", 0),
            "pm25": iaqi.get("pm25", {}).get("v", 0),
            "pm10": iaqi.get("pm10", {}).get("v", 0),
            "no2": iaqi.get("no2", {}).get("v", 0),
            "o3": iaqi.get("o3", {}).get("v", 0),
            "so2": iaqi.get("so2", {}).get("v", 0),
            "co": iaqi.get("co", {}).get("v", 0),
            "city": aqi_data.get("city", {}).get("name", city),
            "latitude": aqi_data.get("city", {}).get("geo", [0, 0])[0],
            "longitude": aqi_data.get("city", {}).get("geo", [0, 0])[1],
            "source": "WAQI",
            "timestamp": datetime.now().isoformat()
        }
        
        # Get category
        aqi = result["aqi"]
        if isinstance(aqi, str) and aqi == "-":
            return None
        
        aqi = int(aqi) if aqi else 0
        result["aqi"] = aqi
        
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
        print(f"  [ERROR] {city}: {e}")
        return None


def fetch_by_coordinates(lat: float, lon: float) -> dict:
    """Fetch AQI data for specific coordinates"""
    try:
        url = f"{WAQI_BASE_URL}/feed/geo:{lat};{lon}/?token={WAQI_TOKEN}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("status") != "ok":
            return None
        
        aqi_data = data["data"]
        iaqi = aqi_data.get("iaqi", {})
        
        aqi = aqi_data.get("aqi", 0)
        if isinstance(aqi, str):
            aqi = 0
        
        result = {
            "aqi": int(aqi),
            "pm25": iaqi.get("pm25", {}).get("v", 0),
            "pm10": iaqi.get("pm10", {}).get("v", 0),
            "no2": iaqi.get("no2", {}).get("v", 0),
            "o3": iaqi.get("o3", {}).get("v", 0),
            "so2": iaqi.get("so2", {}).get("v", 0),
            "co": iaqi.get("co", {}).get("v", 0),
            "city": aqi_data.get("city", {}).get("name", "Unknown"),
            "latitude": lat,
            "longitude": lon,
            "source": "WAQI",
            "timestamp": datetime.now().isoformat()
        }
        
        return result
        
    except Exception as e:
        print(f"  [ERROR] Coordinates ({lat}, {lon}): {e}")
        return None


def fetch_all_cities_data():
    """Fetch AQI data from multiple cities"""
    all_data = []
    
    print("\n[FETCH] Fetching real AQI data from WAQI API...")
    print("-" * 50)
    
    for city in CITIES:
        result = fetch_city_aqi(city)
        if result and result["aqi"] > 0 and result["pm25"] > 0:
            all_data.append(result)
            # Save to database
            save_data(result)
            print(f"  [OK] {city}: AQI={result['aqi']}, PM2.5={result['pm25']}")
        
        # Rate limiting
        time.sleep(0.5)
    
    print("-" * 50)
    print(f"[DONE] Fetched {len(all_data)} valid data points")
    
    return all_data


def train_with_real_data():
    """Fetch real data and train the model"""
    print("=" * 60)
    print("  GA-KELM Model Training with Real WAQI Data")
    print("=" * 60)
    
    # Fetch data from multiple cities
    data_list = fetch_all_cities_data()
    
    if len(data_list) < 10:
        print("\n[WARN] Not enough data for training. Fetching more...")
        # Try fetching more cities via search
        additional_cities = [
            "tirupati", "guntur", "nellore", "rajahmundry", "kakinada",
            "warangal", "karimnagar", "nizamabad", "khammam", "mahabubnagar",
            "kurnool", "kadapa", "anantapur", "chittoor", "srikakulam"
        ]
        for city in additional_cities:
            result = fetch_city_aqi(city)
            if result and result["aqi"] > 0:
                data_list.append(result)
                save_data(result)
                print(f"  [OK] {city}: AQI={result['aqi']}")
            time.sleep(0.5)
    
    print(f"\n[DATA] Total data points: {len(data_list)}")
    
    if len(data_list) < 20:
        print("[ERROR] Still not enough data points (need 20+)")
        print("        The WAQI API may not have data for some cities.")
        return None
    
    # Train the model
    print("\n[TRAIN] Training GA-KELM model with real data...")
    result = train_model(data_list)
    
    print("\n" + "=" * 60)
    print("  Training Result")
    print("=" * 60)
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    # Get model info
    print("\n[INFO] Model Info:")
    info = get_model_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    print("\n[SUCCESS] Model trained with real WAQI data!")
    
    return result


if __name__ == "__main__":
    train_with_real_data()
