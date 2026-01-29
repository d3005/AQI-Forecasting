# Real-Time Air Quality Prediction System

<div align="center">

![AQI Prediction](https://img.shields.io/badge/AQI-Prediction-blue?style=for-the-badge)
![GA-KELM](https://img.shields.io/badge/ML-GA--KELM-purple?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge)
![React](https://img.shields.io/badge/Frontend-React-61DAFB?style=for-the-badge)
![Railway](https://img.shields.io/badge/Deploy-Railway-0B0D0E?style=for-the-badge)

**Real-time air quality monitoring and prediction using Genetic Algorithm optimized Kernel Extreme Learning Machine**

[Live Demo](#) • [API Docs](#) • [Documentation](./docs/)

</div>

---

## 🌟 Features

- **🔴 Real-Time Monitoring**: Live AQI updates via WebSocket connections
- **🧠 GA-KELM Predictions**: Machine learning predictions up to 72 hours ahead
- **📊 Interactive Dashboard**: Modern React dashboard with charts and visualizations
- **🌍 Multi-Location Support**: Monitor air quality in multiple cities worldwide
- **📡 External API Integration**: Data from OpenWeatherMap Air Pollution API
- **☁️ Cloud-Native**: Designed for Railway deployment with PostgreSQL

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React App     │────▶│   FastAPI       │────▶│   PostgreSQL    │
│   (Dashboard)   │◀────│   (Backend)     │◀────│   (Database)    │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                        ┌────────▼────────┐
                        │   GA-KELM ML    │
                        │   Engine        │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │  OpenWeatherMap │
                        │  API            │
                        └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- OpenWeatherMap API key

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run development server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with API URL

# Run development server
npm run dev
```

### Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📁 Project Structure

```
AQI_Index/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI application
│   │   ├── config.py         # Configuration settings
│   │   ├── database.py       # Database connection
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── routers/          # API endpoints
│   │   ├── services/         # Business logic
│   │   └── ml/               # GA-KELM engine
│   ├── requirements.txt
│   └── Procfile
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── hooks/            # Custom hooks
│   │   ├── services/         # API client
│   │   └── styles/           # CSS
│   ├── package.json
│   └── vite.config.js
└── docs/
    ├── abstract.md
    ├── introduction.md
    ├── proposed_system.md
    ├── database_schema.md
    └── deployment_guide.md
```

## 🧠 GA-KELM: How It Works

**GA-KELM** combines:

1. **Kernel Extreme Learning Machine (KELM)**
   - Fast training via closed-form solution
   - RBF kernel for non-linear pattern capture
   - No iterative gradient descent needed

2. **Genetic Algorithm (GA)**
   - Optimizes hyperparameters (C, γ)
   - Global search avoids local optima
   - Population-based evolutionary approach

### Advantages over SVM/ANN

| Aspect | SVM/ANN | GA-KELM |
|--------|---------|---------|
| Training Speed | Minutes-Hours | Seconds-Minutes |
| Hyperparameter Tuning | Manual | Automatic |
| Local Optima | Possible | Avoided |
| Real-Time Capability | Limited | Native |

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/aqi/current/{id}` | Current AQI |
| GET | `/api/v1/aqi/history/{id}` | Historical data |
| GET | `/api/v1/predictions/{id}` | Future predictions |
| POST | `/api/v1/predictions/train` | Train model |
| POST | `/api/v1/locations` | Add location |
| WS | `/ws/aqi/{id}` | Real-time updates |

## 📊 AQI Categories

| AQI | Category | Color |
|-----|----------|-------|
| 0-50 | Good | 🟢 Green |
| 51-100 | Moderate | 🟡 Yellow |
| 101-150 | Unhealthy (Sensitive) | 🟠 Orange |
| 151-200 | Unhealthy | 🔴 Red |
| 201-300 | Very Unhealthy | 🟣 Purple |
| 301-500 | Hazardous | 🟤 Maroon |

## ☁️ Deployment

Deploy to Railway with one click:

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new)

See [Deployment Guide](./docs/deployment_guide.md) for detailed instructions.

## 🛠️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | ✅ |
| `OPENWEATHERMAP_API_KEY` | API key for weather data | ✅ |
| `SECRET_KEY` | JWT secret key | ✅ |
| `CORS_ORIGINS` | Allowed origins | ✅ |
| `DATA_FETCH_INTERVAL_MINUTES` | Data collection interval | ❌ |
| `MODEL_RETRAIN_INTERVAL_HOURS` | Model retraining interval | ❌ |

## 📚 Documentation

- [Abstract](./docs/abstract.md) - Project overview
- [Introduction](./docs/introduction.md) - Background and motivation
- [Proposed System](./docs/proposed_system.md) - Architecture and methodology
- [Database Schema](./docs/database_schema.md) - Data model
- [Deployment Guide](./docs/deployment_guide.md) - Railway deployment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [OpenWeatherMap](https://openweathermap.org/) for air pollution data
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent framework
- [Railway](https://railway.app/) for seamless deployment
- [Recharts](https://recharts.org/) for data visualization

---

<div align="center">

**Built with ❤️ for cleaner air**

</div>
