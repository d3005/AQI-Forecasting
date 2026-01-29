# Real-Time AQI Prediction System

<div align="center">

![AQI](https://img.shields.io/badge/AQI-Prediction-blue?style=for-the-badge)
![GA-KELM](https://img.shields.io/badge/ML-GA--KELM-purple?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge)
![React](https://img.shields.io/badge/Frontend-React-61DAFB?style=for-the-badge)
![Firebase](https://img.shields.io/badge/Database-Firebase-FFCA28?style=for-the-badge)

**Real-time air quality prediction using Genetic Algorithm optimized Kernel Extreme Learning Machine**

</div>

---

## ✨ Features

### Core Features
- **Real-Time AQI Monitoring** - Live updates from WAQI, Ambee, and OpenWeatherMap APIs
- **GA-KELM Predictions** - Advanced ML predictions with 94%+ accuracy
- **Multi-City Support** - 45+ Indian cities including all metros and major cities
- **Location Detection** - Auto-detect user's location with manual override
- **24h Trend Charts** - Visual AQI trends with colored threshold lines

### Authentication & Security
- **Google Sign-In** - Secure authentication via Firebase Auth
- **Protected Routes** - Dashboard requires login
- **Admin Panel** - View all registered users (admin-only)
- **User Profiles** - Display user info in navbar

### Alerts & Notifications
- **Email Alerts** - Get notified when AQI exceeds threshold
- **Customizable Thresholds** - Set your preferred alert level (50-300)
- **Smart Cooldown** - Max 1 alert per hour per location

### Data & Weather
- **Weather Integration** - The Weather Company API with UV index
- **Firebase Database** - Real-time cloud database
- **Auto Scheduler** - Automatic data collection every 15 minutes

---

## 🏙️ Supported Cities (45+)

| Category | Cities |
|----------|--------|
| **Metro** | Delhi, Mumbai, Bangalore, Hyderabad, Chennai, Kolkata |
| **Major** | Pune, Ahmedabad, Jaipur, Lucknow, Kanpur, Nagpur, Indore, Bhopal, Patna, Surat |
| **AP & Telangana** | Visakhapatnam, Vijayawada, Guntur, Tirupati, Nellore, Kurnool, Warangal, **Ongole**, Amaravati |
| **South** | Coimbatore, Kochi, Thiruvananthapuram, Mysore, Mangalore |
| **North** | Chandigarh, Amritsar, Dehradun, Shimla, Varanasi, Agra |
| **Others** | Ranchi, Bhubaneswar, Guwahati, Raipur, Jodhpur, Udaipur, Goa |

---

## 📁 Project Structure

```
AQI-RealTime-System/
├── backend/
│   ├── main.py               # FastAPI server
│   ├── model.py              # GA-KELM ML model
│   ├── data_fetch.py         # Multi-API data fetcher
│   ├── database.py           # Firebase connection
│   ├── scheduler.py          # Auto data update
│   ├── requirements.txt
│   └── firebase-credentials.json
│
├── frontend/
│   ├── src/
│   │   ├── contexts/
│   │   │   └── AuthContext.js    # Google Auth
│   │   ├── components/
│   │   │   └── AlertSettings.js  # Email alerts
│   │   ├── services/
│   │   │   └── alertService.js   # EmailJS integration
│   │   ├── pages/
│   │   │   ├── HomePage.js       # Main dashboard
│   │   │   ├── LoginPage.js      # Google Sign-In
│   │   │   └── AdminPage.js      # User management
│   │   ├── firebase-config.js    # Firebase config
│   │   └── App.js
│   └── package.json
│
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Firebase project (free tier)
- API Keys: WAQI, Ambee, OpenWeatherMap (all free tiers)
- EmailJS account (free - 200 emails/month)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env with your API keys

# Run server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure Firebase
# Edit src/firebase-config.js with your Firebase config

# Run development server
npm start
```

---

## ⚙️ Environment Variables

### Backend (.env)

```env
# Firebase
FIREBASE_URL=https://your-project.firebaseio.com
FIREBASE_CRED_PATH=firebase-credentials.json

# API Keys
API_KEY=your_openweathermap_key
WAQI_API_KEY=your_waqi_token
AMBEE_API_KEY=your_ambee_key
TWC_API_KEY=your_weather_company_key

# Default Location
LATITUDE=15.5057
LONGITUDE=80.0499

# CORS
FRONTEND_URL=http://localhost:3000
```

### Frontend Configuration

**Firebase Config** (`src/firebase-config.js`):
```javascript
const firebaseConfig = {
  apiKey: "your-api-key",
  authDomain: "your-project.firebaseapp.com",
  databaseURL: "https://your-project.firebaseio.com",
  projectId: "your-project-id",
  // ... rest of config
};
```

**Admin Email** (`src/contexts/AuthContext.js`):
```javascript
const ADMIN_EMAILS = ['your-admin@gmail.com'];
```

---

## 🔐 Authentication Setup

1. **Enable Google Auth in Firebase Console**
   - Firebase Console → Authentication → Sign-in method → Enable Google

2. **Add Firebase Web App**
   - Project Settings → Your apps → Add web app
   - Copy config to `firebase-config.js`

3. **Set Admin Email**
   - Edit `AuthContext.js` with admin Gmail

---

## 📧 Email Alerts Setup (EmailJS)

1. **Create EmailJS Account**: https://www.emailjs.com
2. **Add Gmail Service**: Connect your Gmail
3. **Create Template** with variables:
   - `{{email}}` - Recipient email
   - `{{user_name}}`, `{{aqi}}`, `{{location}}`, `{{category}}`
4. **Update** `src/services/alertService.js`:
   ```javascript
   const EMAILJS_SERVICE_ID = 'your_service_id';
   const EMAILJS_TEMPLATE_ID = 'your_template_id';
   const EMAILJS_PUBLIC_KEY = 'your_public_key';
   ```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/current` | Current AQI with lat/lon params |
| GET | `/predict` | GA-KELM prediction |
| GET | `/trend` | 24h AQI trend data |
| GET | `/weather` | Current weather data |
| GET | `/history` | Historical readings |
| GET | `/health` | API health check |

---

## 🧠 GA-KELM Model

**Genetic Algorithm + Kernel Extreme Learning Machine**

| Metric | Value |
|--------|-------|
| Data Points | 375+ |
| R² Score | 94.6% |
| RMSE | 0.041 |
| Training Time | ~2 min |

### How It Works

1. **Data Collection** - Multi-API data from 45+ cities
2. **Feature Engineering** - PM2.5, PM10, NO2, O3, SO2, CO, weather
3. **Genetic Optimization** - Finds optimal C and gamma
4. **KELM Training** - Fast closed-form RBF kernel solution
5. **Real-time Prediction** - Next hour AQI forecast

---

## 📊 Data Sources

| API | Purpose | Priority |
|-----|---------|----------|
| **WAQI** | Primary AQI data | 1st |
| **Ambee** | Fallback + Historical | 2nd |
| **OpenWeatherMap** | Weather + AQI fallback | 3rd |
| **The Weather Company** | Enhanced weather (UV) | Primary for weather |

---

## 🛡️ Security Features

- ✅ Google OAuth 2.0 authentication
- ✅ Protected routes (login required)
- ✅ Role-based admin access
- ✅ Firebase security rules
- ✅ Environment variables for secrets

---

## 📱 User Interface

- **Dark Theme** - Professional GitHub-inspired design
- **Responsive** - Works on desktop and mobile
- **Real-time Updates** - Live data refresh
- **Interactive Charts** - Trend visualization
- **City Search** - Find any of 45+ cities

---

## 👨‍💻 Author

Developed for real-time air quality monitoring and prediction.

---

## 📄 License

MIT License - feel free to use and modify.
