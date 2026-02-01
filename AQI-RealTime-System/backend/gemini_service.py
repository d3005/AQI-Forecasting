"""
Gemini AI Service
Provides AI-powered health recommendations based on AQI data
"""

import os
from dotenv import load_dotenv

# Try to import Gemini (fail gracefully if not installed)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    print("[WARNING] google-generativeai not installed. AI features disabled.")
    GEMINI_AVAILABLE = False
    genai = None

load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def init_gemini():
    """Initialize Gemini API"""
    if not GEMINI_AVAILABLE:
        print("[WARNING] Gemini package not installed. AI features disabled.")
        return False
    
    if not GEMINI_API_KEY:
        print("[WARNING] GEMINI_API_KEY not set. AI features disabled.")
        return False
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("[OK] Gemini AI initialized successfully!")
        return True
    except Exception as e:
        print(f"[ERROR] Gemini initialization failed: {e}")
        return False


def get_health_advice(aqi: int, category: str, location: str, weather: dict = None) -> dict:
    """
    Get AI-powered health recommendations based on AQI and weather data
    
    Args:
        aqi: Current AQI value
        category: AQI category (Good, Moderate, Unhealthy, etc.)
        location: Location name
        weather: Weather data dict (temperature, humidity, etc.)
    
    Returns:
        dict with 'success', 'advice', and 'recommendations' keys
    """
    if not GEMINI_AVAILABLE or not GEMINI_API_KEY:
        return {
            "success": False,
            "error": "AI service not configured",
            "advice": get_fallback_advice(aqi, category)
        }
    
    try:
        # Build context prompt
        weather_context = ""
        if weather:
            weather_context = f"""
Weather Conditions:
- Temperature: {weather.get('temperature', 'N/A')}°C
- Humidity: {weather.get('humidity', 'N/A')}%
- Weather: {weather.get('weather', 'N/A')}
- Wind Speed: {weather.get('wind_speed', 'N/A')} km/h
- UV Index: {weather.get('uv_index', 'N/A')}
"""
        
        prompt = f"""You are an air quality health advisor. Provide personalized, actionable health advice based on the current air quality conditions.

Current Conditions for {location}:
- AQI: {aqi} ({category})
{weather_context}

Provide a response in this exact format:
1. A brief 1-2 sentence summary of the current air quality situation
2. 4-5 specific health recommendations as bullet points
3. Who should be most cautious (sensitive groups)
4. Expected duration or when conditions might improve (if applicable)

Keep the response concise, practical, and focused on actionable advice. Do not use emojis. Be professional but friendly."""

        # Initialize model and generate
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        advice_text = response.text if response.text else get_fallback_advice(aqi, category)
        
        return {
            "success": True,
            "advice": advice_text,
            "aqi": aqi,
            "category": category,
            "location": location
        }
        
    except Exception as e:
        print(f"[ERROR] Gemini API error: {e}")
        return {
            "success": False,
            "error": str(e),
            "advice": get_fallback_advice(aqi, category)
        }


def get_fallback_advice(aqi: int, category: str) -> str:
    """Fallback advice when AI is unavailable"""
    
    advice_map = {
        "Good": """Air quality is satisfactory.

Recommendations:
- Enjoy outdoor activities freely
- Great day for exercise outside
- No special precautions needed
- Keep windows open for fresh air

All groups can participate in outdoor activities without concern.""",

        "Moderate": """Air quality is acceptable but may concern some sensitive individuals.

Recommendations:
- Most people can be active outdoors
- Unusually sensitive individuals should reduce prolonged outdoor exertion
- Consider indoor activities if you experience symptoms
- Stay hydrated

Sensitive Groups: People with respiratory conditions should monitor symptoms.""",

        "Unhealthy for Sensitive Groups": """Air quality may affect sensitive groups.

Recommendations:
- Sensitive groups should limit prolonged outdoor exertion
- Keep outdoor activities short
- Use air purifiers indoors if available
- Keep windows closed
- Monitor for symptoms like coughing or shortness of breath

Sensitive Groups: Children, elderly, and those with heart or lung conditions.""",

        "Unhealthy": """Air quality is unhealthy for everyone.

Recommendations:
- Avoid prolonged outdoor exertion
- Move activities indoors
- Keep windows and doors closed
- Use air purifiers if available
- Wear N95 masks if going outside is necessary

Everyone may begin to experience health effects. Sensitive groups may experience more serious effects.""",

        "Very Unhealthy": """Health alert: significant health effects possible for everyone.

Recommendations:
- Avoid all outdoor physical activities
- Stay indoors with windows closed
- Run air purifiers on high
- Wear N95 mask if outdoor exposure is unavoidable
- Seek medical attention if experiencing symptoms

Everyone should avoid outdoor exertion. Sensitive groups should remain indoors.""",

        "Hazardous": """Emergency conditions! Everyone may experience serious health effects.

Recommendations:
- Stay indoors completely
- Keep all windows and doors sealed
- Run air purifiers continuously
- Avoid any outdoor exposure
- Seek medical attention for any symptoms

This is a health emergency. All individuals should avoid any outdoor activity."""
    }
    
    return advice_map.get(category, advice_map["Moderate"])


def get_smart_alert_message(aqi: int, category: str, location: str, threshold: int) -> dict:
    """
    Generate AI-powered alert message for notifications
    
    Args:
        aqi: Current AQI value
        category: AQI category
        location: Location name  
        threshold: User's alert threshold
    
    Returns:
        dict with alert subject and body
    """
    if not GEMINI_AVAILABLE or not GEMINI_API_KEY:
        return {
            "success": False,
            "subject": f"AQI Alert: {category} in {location}",
            "body": f"The AQI in {location} has reached {aqi} ({category}), exceeding your threshold of {threshold}. Please take appropriate precautions."
        }
    
    try:
        prompt = f"""Generate a brief, professional AQI alert notification.

Context:
- Location: {location}
- Current AQI: {aqi} ({category})
- User's threshold: {threshold}

Generate:
1. A short email subject line (under 50 characters)
2. A brief alert body (2-3 sentences max) that explains the situation and gives 1-2 key actions

Format your response as:
SUBJECT: [subject line]
BODY: [alert body]

Be concise and actionable. No emojis."""

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        # Parse response
        text = response.text
        subject = f"AQI Alert: {category} in {location}"
        body = text
        
        if "SUBJECT:" in text and "BODY:" in text:
            parts = text.split("BODY:")
            subject = parts[0].replace("SUBJECT:", "").strip()
            body = parts[1].strip() if len(parts) > 1 else text
        
        return {
            "success": True,
            "subject": subject,
            "body": body
        }
        
    except Exception as e:
        print(f"[ERROR] Smart alert generation failed: {e}")
        return {
            "success": False,
            "subject": f"AQI Alert: {category} in {location}",
            "body": f"The AQI in {location} has reached {aqi} ({category}), exceeding your threshold of {threshold}. Please take appropriate precautions."
        }
