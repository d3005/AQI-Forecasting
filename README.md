# Real-Time AQI Prediction System

<div align="center">

![AQI Prediction](https://img.shields.io/badge/AQI-Prediction-blue?style=for-the-badge)
![GA-KELM](https://img.shields.io/badge/ML-GA--KELM-purple?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge)
![React](https://img.shields.io/badge/Frontend-React-61DAFB?style=for-the-badge)
![Firebase](https://img.shields.io/badge/Database-Firebase-FFCA28?style=for-the-badge)

**Real-time air quality monitoring and prediction using Genetic Algorithm optimized Kernel Extreme Learning Machine**

[Live Demo](https://aqi-forecasting-index.vercel.app) • [API Health](https://aqi-forecasting-production.up.railway.app/health) • [Documentation](./docs/)

</div>

---

## 🌐 Live Deployment

| Service | Platform | URL |
|---------|----------|-----|
| **Frontend** | Vercel | [aqi-forecasting-index.vercel.app](https://aqi-forecasting-index.vercel.app) |
| **Backend API** | Railway | [aqi-forecasting-production.up.railway.app](https://aqi-forecasting-production.up.railway.app) |
| **Database** | Firebase | Realtime Database |

---

## 🌟 Features

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
- **Email Alerts** - Get notified when AQI exceeds threshold (via EmailJS)
- **Customizable Thresholds** - Set your preferred alert level (50-300)
- **Smart Cooldown** - Max 1 alert per hour per location

### Data & Weather
- **Weather Integration** - The Weather Company API with UV index
- **Firebase Database** - Real-time cloud database
- **Auto Scheduler** - Automatic data collection every 15 minutes

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React App     │────▶│   FastAPI       │────▶│    Firebase     │
│   (Vercel)      │◀────│   (Railway)     │◀────│   (Realtime DB) │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                        ┌────────▼────────┐
                        │   GA-KELM ML    │
                        │   Engine        │
                        └────────┬────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          ▼                      ▼                      ▼
   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
   │    WAQI     │      │    Ambee    │      │ OpenWeather │
   │    API      │      │    API      │      │    API      │
   └─────────────┘      └─────────────┘      └─────────────┘
```

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
AQI_Index/
├── AQI-RealTime-System/          # Main application
│   ├── backend/
│   │   ├── main.py               # FastAPI server
│   │   ├── model.py              # GA-KELM ML model
│   │   ├── data_fetch.py         # Multi-API data fetcher
│   │   ├── database.py           # Firebase connection
│   │   ├── scheduler.py          # Auto data update
│   │   └── requirements.txt
│   │
│   └── frontend/
│       ├── src/
│       │   ├── contexts/AuthContext.js    # Google Auth
│       │   ├── components/AlertSettings.js # Email alerts
│       │   ├── services/alertService.js   # EmailJS integration
│       │   ├── pages/
│       │   │   ├── HomePage.js            # Main dashboard
│       │   │   ├── LoginPage.js           # Google Sign-In
│       │   │   └── AdminPage.js           # User management
│       │   └── firebase-config.js
│       └── package.json
│
├── docs/                          # Documentation
│   ├── abstract.md
│   ├── introduction.md
│   ├── proposed_system.md
│   ├── database_schema.md
│   └── deployment_guide.md
│
├── Dockerfile                     # Railway deployment
├── railway.json                   # Railway config
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
cd AQI-RealTime-System/backend

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
cd AQI-RealTime-System/frontend

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
FIREBASE_URL=https://your-project-default-rtdb.firebaseio.com
FIREBASE_CREDENTIALS=<base64-encoded-service-account-json>

# API Keys
API_KEY=your_openweathermap_key
WAQI_API_KEY=your_waqi_token
AMBEE_API_KEY=your_ambee_key

# CORS
FRONTEND_URL=https://your-frontend.vercel.app
```

### Frontend (.env)

```env
REACT_APP_API_URL=https://your-backend.up.railway.app
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
| POST | `/train` | Retrain ML model |

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

## ☁️ Deployment

### Frontend → Vercel

1. Connect GitHub repo to Vercel
2. Set Root Directory: `AQI-RealTime-System/frontend`
3. Add environment variable: `REACT_APP_API_URL`
4. Deploy

### Backend → Railway

1. Connect GitHub repo to Railway
2. Use the Dockerfile in root directory
3. Add environment variables (see above)
4. Deploy

### Firebase Setup

1. Create Firebase project
2. Enable Realtime Database
3. Enable Google Authentication
4. Add Vercel domain to authorized domains
5. Download service account key and encode as base64 for Railway

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
- ✅ CORS protection

---

## 📱 User Interface

- **Dark Theme** - Professional GitHub-inspired design
- **Responsive** - Works on desktop and mobile
- **Real-time Updates** - Live data refresh
- **Interactive Charts** - Trend visualization
- **City Search** - Find any of 45+ cities

---

## 📚 Documentation

- [Abstract](./docs/abstract.md) - Project overview
- [Introduction](./docs/introduction.md) - Background and motivation
- [Proposed System](./docs/proposed_system.md) - Architecture and methodology
- [Database Schema](./docs/database_schema.md) - Data model
- [Deployment Guide](./docs/deployment_guide.md) - Deployment instructions

---

## 👨‍💻 Author

Developed by **DJ** for real-time air quality monitoring and prediction.

---

## 📄 License

MIT License - feel free to use and modify.

---

<div align="center">

**Built with ❤️ for cleaner air**

</div>
