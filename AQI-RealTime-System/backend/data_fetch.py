"""
Data Fetcher Module - Multi-Source AQI API
Uses WAQI (primary), Ambee (secondary), OpenWeatherMap (fallback)
Real-Time AQI Prediction System
"""

import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENWEATHERMAP_KEY = os.getenv("API_KEY")
WAQI_API_KEY = os.getenv("WAQI_API_KEY", "c573cdb300b84975dd16d507414ec2dc84804d22")
AMBEE_API_KEY = os.getenv("AMBEE_API_KEY", "c85176e0b52f74d7ac727fbd6d0277c7bb16cac82bd9a23fc7958fe125723706")

LATITUDE = float(os.getenv("LATITUDE", "15.5057"))  # Ongole default
LONGITUDE = float(os.getenv("LONGITUDE", "80.0499"))


def get_aqi_category(aqi: int) -> str:
    """Get AQI category label"""
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


def fetch_from_waqi(lat: float, lon: float):
    """Fetch AQI from WAQI API (primary source - most accurate)"""
    try:
        url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={WAQI_API_KEY}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get("status") != "ok":
            print(f"[WAQI] Error: {data.get('data', 'Unknown')}")
            return None
        
        aqi_data = data["data"]
        iaqi = aqi_data.get("iaqi", {})
        
        aqi = aqi_data.get("aqi", 0)
        if isinstance(aqi, str) and aqi == "-":
            return None
        aqi = int(aqi) if aqi else 0
        
        # Get station name
        city_info = aqi_data.get("city", {})
        station_name = city_info.get("name", "Unknown")
        
        result = {
            "aqi": aqi,
            "pm25": iaqi.get("pm25", {}).get("v", 0),
            "pm10": iaqi.get("pm10", {}).get("v", 0),
            "no2": iaqi.get("no2", {}).get("v", 0),
            "o3": iaqi.get("o3", {}).get("v", 0),
            "so2": iaqi.get("so2", {}).get("v", 0),
            "co": iaqi.get("co", {}).get("v", 0),
            "category": get_aqi_category(aqi),
            "station": station_name,
            "source": "WAQI",
            "latitude": lat,
            "longitude": lon,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"[WAQI] {station_name}: AQI={aqi}, PM2.5={result['pm25']}")
        return result
        
    except Exception as e:
        print(f"[WAQI] Error: {e}")
        return None


def fetch_from_ambee(lat: float, lon: float):
    """Fetch AQI from Ambee API (secondary source)"""
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
        aqi = station.get("AQI", 0)
        
        result = {
            "aqi": aqi,
            "pm25": station.get("PM25", 0),
            "pm10": station.get("PM10", 0),
            "no2": station.get("NO2", 0),
            "o3": station.get("OZONE", 0),
            "so2": station.get("SO2", 0),
            "co": station.get("CO", 0),
            "category": get_aqi_category(aqi),
            "station": station.get("stationName", "Ambee Station"),
            "source": "Ambee",
            "latitude": lat,
            "longitude": lon,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"[Ambee] AQI={aqi}, PM2.5={result['pm25']}")
        return result
        
    except Exception as e:
        print(f"[Ambee] Error: {e}")
        return None


def fetch_from_openweathermap(lat: float, lon: float):
    """Fetch AQI from OpenWeatherMap (fallback)"""
    if not OPENWEATHERMAP_KEY:
        return None
    
    try:
        url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHERMAP_KEY}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "list" not in data or len(data["list"]) == 0:
            return None
        
        pollution = data["list"][0]
        components = pollution.get("components", {})
        
        pm25 = components.get("pm2_5", 0)
        
        # Calculate EPA AQI from PM2.5
        if pm25 <= 12:
            aqi = (50/12) * pm25
        elif pm25 <= 35.4:
            aqi = 50 + ((100-50)/(35.4-12.1)) * (pm25 - 12.1)
        elif pm25 <= 55.4:
            aqi = 100 + ((150-100)/(55.4-35.5)) * (pm25 - 35.5)
        elif pm25 <= 150.4:
            aqi = 150 + ((200-150)/(150.4-55.5)) * (pm25 - 55.5)
        elif pm25 <= 250.4:
            aqi = 200 + ((300-200)/(250.4-150.5)) * (pm25 - 150.5)
        else:
            aqi = 300 + ((500-300)/(500.4-250.5)) * (pm25 - 250.5)
        
        aqi = int(min(500, max(0, aqi)))
        
        result = {
            "aqi": aqi,
            "pm25": round(pm25, 2),
            "pm10": round(components.get("pm10", 0), 2),
            "no2": round(components.get("no2", 0), 2),
            "o3": round(components.get("o3", 0), 2),
            "so2": round(components.get("so2", 0), 2),
            "co": round(components.get("co", 0) / 1000, 3),
            "category": get_aqi_category(aqi),
            "station": "OpenWeatherMap",
            "source": "OpenWeatherMap",
            "latitude": lat,
            "longitude": lon,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"[OWM] AQI={aqi}, PM2.5={pm25}")
        return result
        
    except Exception as e:
        print(f"[OWM] Error: {e}")
        return None


def fetch_weather(lat: float = None, lon: float = None):
    """Fetch weather data from The Weather Company API (primary) or OpenWeatherMap (fallback)"""
    lat = lat or LATITUDE
    lon = lon or LONGITUDE
    
    # Try The Weather Company API first
    TWC_API_KEY = os.getenv("TWC_API_KEY", "0c1fa686d71f487b9fa686d71ff87b66")
    
    try:
        # The Weather Company current conditions API
        url = f"https://api.weather.com/v3/wx/observations/current?geocode={lat},{lon}&units=m&language=en-US&format=json&apiKey={TWC_API_KEY}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"[TWC] Weather fetched successfully")
            return {
                "temperature": data.get("temperature", 25),
                "feels_like": data.get("temperatureFeelsLike", 25),
                "humidity": data.get("relativeHumidity", 60),
                "pressure": data.get("pressureMeanSeaLevel", 1013),
                "wind_speed": round((data.get("windSpeed", 0) or 0), 1),
                "wind_deg": data.get("windDirection", 0) or 0,
                "weather": data.get("wxPhraseLong", "Clear"),
                "weather_desc": data.get("wxPhraseLong", "clear sky"),
                "weather_icon": data.get("iconCode", 32),
                "clouds": data.get("cloudCover", 0) or 0,
                "visibility": round((data.get("visibility", 10) or 10), 1),
                "uv_index": data.get("uvIndex", 0) or 0
            }
    except Exception as e:
        print(f"[TWC] Error: {e}")
    
    # Fallback to OpenWeatherMap
    if not OPENWEATHERMAP_KEY:
        return _get_mock_weather()
    
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHERMAP_KEY}&units=metric"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return {
            "temperature": round(data["main"]["temp"], 1),
            "feels_like": round(data["main"]["feels_like"], 1),
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind_speed": round(data["wind"]["speed"] * 3.6, 1),
            "wind_deg": data["wind"].get("deg", 0),
            "weather": data["weather"][0]["main"],
            "weather_desc": data["weather"][0]["description"],
            "weather_icon": data["weather"][0]["icon"],
            "clouds": data["clouds"]["all"],
            "visibility": data.get("visibility", 10000) / 1000,
            "uv_index": 0
        }
    except Exception as e:
        print(f"[OWM Weather] Error: {e}")
        return _get_mock_weather()


def _get_mock_weather():
    """Mock weather data"""
    import random
    return {
        "temperature": 25,
        "feels_like": 27,
        "humidity": 63,
        "pressure": 1012,
        "wind_speed": 14,
        "wind_deg": 180,
        "weather": "Sunny",
        "weather_desc": "clear sky",
        "weather_icon": "01d",
        "clouds": 20,
        "visibility": 10.0,
        "uv_index": 5
    }


def fetch_data(lat: float = None, lon: float = None):
    """
    Fetch real-time AQI data from multiple sources
    Priority: WAQI > Ambee > OpenWeatherMap
    """
    lat = lat or LATITUDE
    lon = lon or LONGITUDE
    
    print(f"\n[FETCH] Getting AQI for ({lat}, {lon})...")
    
    # Try WAQI first (most accurate, matches IQAir/AQI.in data)
    result = fetch_from_waqi(lat, lon)
    
    # If WAQI fails, try Ambee
    if not result or result.get("aqi", 0) == 0:
        result = fetch_from_ambee(lat, lon)
    
    # If Ambee fails, try OpenWeatherMap
    if not result or result.get("aqi", 0) == 0:
        result = fetch_from_openweathermap(lat, lon)
    
    # If all fail, return mock data
    if not result:
        print("[WARN] All APIs failed, using fallback")
        result = {
            "aqi": 150,
            "pm25": 55,
            "pm10": 80,
            "no2": 30,
            "o3": 50,
            "so2": 10,
            "co": 0.5,
            "category": "Unhealthy for Sensitive Groups",
            "station": "Fallback",
            "source": "Fallback",
            "latitude": lat,
            "longitude": lon,
            "timestamp": datetime.now().isoformat()
        }
    
    # Add weather data
    result["weather"] = fetch_weather(lat, lon)
    
    return result


# For backwards compatibility
def calculate_aqi(pm25: float) -> int:
    """Calculate AQI from PM2.5 concentration (EPA formula)"""
    if pm25 <= 12:
        aqi = (50/12) * pm25
    elif pm25 <= 35.4:
        aqi = 50 + ((100-50)/(35.4-12.1)) * (pm25 - 12.1)
    elif pm25 <= 55.4:
        aqi = 100 + ((150-100)/(55.4-35.5)) * (pm25 - 35.5)
    elif pm25 <= 150.4:
        aqi = 150 + ((200-150)/(150.4-55.5)) * (pm25 - 55.5)
    elif pm25 <= 250.4:
        aqi = 200 + ((300-200)/(250.4-150.5)) * (pm25 - 150.5)
    else:
        aqi = 300 + ((500-300)/(500.4-250.5)) * (pm25 - 250.5)
    return int(min(500, max(0, aqi)))


if __name__ == "__main__":
    # Test with Ongole coordinates
    print("Testing data fetch...")
    data = fetch_data(15.5057, 80.0499)
    print(f"\nResult: AQI={data['aqi']}, Category={data['category']}")
    print(f"PM2.5={data['pm25']}, Station={data.get('station', 'N/A')}")
