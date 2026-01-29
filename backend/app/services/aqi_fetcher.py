"""
AQI Data Fetcher Service
Integrates with OpenWeatherMap Air Pollution API and AQICN as backup
"""

import httpx
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class AQIFetcher:
    """
    Service for fetching real-time AQI data from external APIs.
    Primary: OpenWeatherMap Air Pollution API
    Backup: AQICN API
    """
    
    # OpenWeatherMap Air Pollution API endpoint
    OWM_BASE_URL = "http://api.openweathermap.org/data/2.5/air_pollution"
    
    # AQICN API endpoint
    AQICN_BASE_URL = "https://api.waqi.info/feed"
    
    # EPA AQI breakpoints for conversion
    AQI_BREAKPOINTS = {
        'pm25': [
            (0, 12.0, 0, 50),
            (12.1, 35.4, 51, 100),
            (35.5, 55.4, 101, 150),
            (55.5, 150.4, 151, 200),
            (150.5, 250.4, 201, 300),
            (250.5, 350.4, 301, 400),
            (350.5, 500.4, 401, 500),
        ],
        'pm10': [
            (0, 54, 0, 50),
            (55, 154, 51, 100),
            (155, 254, 101, 150),
            (255, 354, 151, 200),
            (355, 424, 201, 300),
            (425, 504, 301, 400),
            (505, 604, 401, 500),
        ],
        'o3': [  # 8-hour average in ppb
            (0, 54, 0, 50),
            (55, 70, 51, 100),
            (71, 85, 101, 150),
            (86, 105, 151, 200),
            (106, 200, 201, 300),
        ],
        'no2': [  # 1-hour average in ppb
            (0, 53, 0, 50),
            (54, 100, 51, 100),
            (101, 360, 101, 150),
            (361, 649, 151, 200),
            (650, 1249, 201, 300),
            (1250, 1649, 301, 400),
            (1650, 2049, 401, 500),
        ],
        'so2': [  # 1-hour average in ppb
            (0, 35, 0, 50),
            (36, 75, 51, 100),
            (76, 185, 101, 150),
            (186, 304, 151, 200),
            (305, 604, 201, 300),
            (605, 804, 301, 400),
            (805, 1004, 401, 500),
        ],
        'co': [  # 8-hour average in ppm
            (0, 4.4, 0, 50),
            (4.5, 9.4, 51, 100),
            (9.5, 12.4, 101, 150),
            (12.5, 15.4, 151, 200),
            (15.5, 30.4, 201, 300),
            (30.5, 40.4, 301, 400),
            (40.5, 50.4, 401, 500),
        ],
    }
    
    def __init__(self):
        self.owm_api_key = settings.OPENWEATHERMAP_API_KEY
        self.aqicn_token = settings.AQICN_API_TOKEN
        
    async def fetch_current_aqi(
        self, 
        latitude: float, 
        longitude: float
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch current AQI data for given coordinates.
        Returns normalized AQI data dictionary.
        """
        try:
            # Try OpenWeatherMap first
            data = await self._fetch_from_owm(latitude, longitude)
            if data:
                return data
                
            # Fallback to AQICN if available
            if self.aqicn_token:
                data = await self._fetch_from_aqicn(latitude, longitude)
                if data:
                    return data
                    
            logger.warning(f"Failed to fetch AQI data for ({latitude}, {longitude})")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching AQI data: {e}")
            return None
    
    async def _fetch_from_owm(
        self, 
        latitude: float, 
        longitude: float
    ) -> Optional[Dict[str, Any]]:
        """Fetch AQI data from OpenWeatherMap API"""
        if not self.owm_api_key:
            logger.warning("OpenWeatherMap API key not configured")
            return None
            
        url = f"{self.OWM_BASE_URL}?lat={latitude}&lon={longitude}&appid={self.owm_api_key}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                if "list" not in data or len(data["list"]) == 0:
                    return None
                    
                # Extract latest reading
                reading = data["list"][0]
                components = reading.get("components", {})
                
                # OpenWeatherMap provides concentrations in μg/m³
                pm25 = components.get("pm2_5", 0)
                pm10 = components.get("pm10", 0)
                o3 = components.get("o3", 0)
                no2 = components.get("no2", 0)
                so2 = components.get("so2", 0)
                co = components.get("co", 0)
                
                # Calculate AQI from PM2.5 (primary pollutant)
                aqi_value = self._calculate_aqi(pm25, "pm25")
                
                # Get overall AQI considering all pollutants
                aqi_values = [
                    self._calculate_aqi(pm25, "pm25"),
                    self._calculate_aqi(pm10, "pm10"),
                ]
                overall_aqi = max(aqi_values) if aqi_values else aqi_value
                
                return {
                    "pm25": pm25,
                    "pm10": pm10,
                    "o3": o3,
                    "no2": no2,
                    "so2": so2,
                    "co": co,
                    "aqi_value": overall_aqi,
                    "aqi_category": self._get_category(overall_aqi),
                    "recorded_at": datetime.fromtimestamp(reading.get("dt", datetime.now().timestamp())),
                    "source": "openweathermap"
                }
                
            except httpx.HTTPError as e:
                logger.error(f"OpenWeatherMap API error: {e}")
                return None
    
    async def _fetch_from_aqicn(
        self, 
        latitude: float, 
        longitude: float
    ) -> Optional[Dict[str, Any]]:
        """Fetch AQI data from AQICN API (backup)"""
        if not self.aqicn_token:
            return None
            
        url = f"{self.AQICN_BASE_URL}/geo:{latitude};{longitude}/?token={self.aqicn_token}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") != "ok":
                    return None
                    
                aqi_data = data.get("data", {})
                iaqi = aqi_data.get("iaqi", {})
                
                return {
                    "pm25": iaqi.get("pm25", {}).get("v"),
                    "pm10": iaqi.get("pm10", {}).get("v"),
                    "o3": iaqi.get("o3", {}).get("v"),
                    "no2": iaqi.get("no2", {}).get("v"),
                    "so2": iaqi.get("so2", {}).get("v"),
                    "co": iaqi.get("co", {}).get("v"),
                    "aqi_value": aqi_data.get("aqi", 0),
                    "aqi_category": self._get_category(aqi_data.get("aqi", 0)),
                    "recorded_at": datetime.now(),
                    "source": "aqicn"
                }
                
            except httpx.HTTPError as e:
                logger.error(f"AQICN API error: {e}")
                return None
    
    def _calculate_aqi(self, concentration: float, pollutant: str) -> int:
        """
        Calculate AQI from pollutant concentration using EPA breakpoints.
        Formula: AQI = ((I_high - I_low) / (C_high - C_low)) * (C - C_low) + I_low
        """
        if pollutant not in self.AQI_BREAKPOINTS:
            return 0
            
        breakpoints = self.AQI_BREAKPOINTS[pollutant]
        
        for c_low, c_high, i_low, i_high in breakpoints:
            if c_low <= concentration <= c_high:
                aqi = ((i_high - i_low) / (c_high - c_low)) * (concentration - c_low) + i_low
                return round(aqi)
        
        # If concentration exceeds all breakpoints
        return 500
    
    def _get_category(self, aqi_value: int) -> str:
        """Get AQI category from value"""
        if aqi_value <= 50:
            return "Good"
        elif aqi_value <= 100:
            return "Moderate"
        elif aqi_value <= 150:
            return "Unhealthy for Sensitive Groups"
        elif aqi_value <= 200:
            return "Unhealthy"
        elif aqi_value <= 300:
            return "Very Unhealthy"
        else:
            return "Hazardous"
    
    async def fetch_forecast(
        self, 
        latitude: float, 
        longitude: float,
        hours: int = 24
    ) -> Optional[list[Dict[str, Any]]]:
        """
        Fetch AQI forecast data (if available from API).
        OpenWeatherMap provides 4-day hourly forecast.
        """
        if not self.owm_api_key:
            return None
            
        url = f"{self.OWM_BASE_URL}/forecast?lat={latitude}&lon={longitude}&appid={self.owm_api_key}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                forecasts = []
                for reading in data.get("list", [])[:hours]:
                    components = reading.get("components", {})
                    pm25 = components.get("pm2_5", 0)
                    aqi_value = self._calculate_aqi(pm25, "pm25")
                    
                    forecasts.append({
                        "aqi_value": aqi_value,
                        "aqi_category": self._get_category(aqi_value),
                        "forecast_for": datetime.fromtimestamp(reading.get("dt")),
                        "pm25": pm25,
                    })
                
                return forecasts
                
            except httpx.HTTPError as e:
                logger.error(f"Forecast API error: {e}")
                return None


# Singleton instance
aqi_fetcher = AQIFetcher()
