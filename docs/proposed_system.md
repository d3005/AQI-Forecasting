# Proposed System

## System Overview

The Real-Time Air Quality Prediction System is designed as a modern, scalable, cloud-native application that combines machine learning with real-time data processing. The system continuously collects air quality data from external APIs, trains predictive models using GA-KELM, and presents live predictions through an interactive dashboard.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND LAYER                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    React Dashboard (Vite)                            │   │
│  │  ┌────────────┐  ┌────────────────┐  ┌─────────────────────────┐   │   │
│  │  │  AQI Card  │  │ Prediction     │  │  Location Search        │   │   │
│  │  │  (Live)    │  │ Chart          │  │  + Stats                │   │   │
│  │  └────────────┘  └────────────────┘  └─────────────────────────┘   │   │
│  │                        ↓ REST/WebSocket                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND LAYER                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      FastAPI Application                             │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │   │
│  │  │ REST API    │  │ WebSocket   │  │ Background  │  │ GA-KELM   │  │   │
│  │  │ Endpoints   │  │ Server      │  │ Scheduler   │  │ Engine    │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────┼───────────────────────────────────┐   │
│  │                                 ▼                                    │   │
│  │  ┌──────────────────────────────────────────────────────────────┐   │   │
│  │  │                   PostgreSQL Database                        │   │   │
│  │  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌───────────┐ │   │   │
│  │  │  │ locations  │ │aqi_readings│ │predictions │ │model_meta │ │   │   │
│  │  │  └────────────┘ └────────────┘ └────────────┘ └───────────┘ │   │   │
│  │  └──────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            EXTERNAL SERVICES                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  OpenWeatherMap Air Pollution API (Primary)                         │   │
│  │  AQICN API (Backup)                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## GA-KELM Methodology

### Kernel Extreme Learning Machine (KELM)

KELM extends the traditional Extreme Learning Machine by replacing the random hidden layer with a kernel function. This approach offers:

1. **No Hidden Layer Definition**: Unlike ELM, KELM doesn't require specifying the number of hidden neurons
2. **Kernel Trick**: Uses kernel functions to implicitly map inputs to high-dimensional space
3. **Closed-Form Solution**: Training is performed by solving a system of linear equations

#### Mathematical Formulation

Given training data {(xᵢ, yᵢ) | i = 1, ..., N}, KELM finds output weights β by solving:

```
β = (K + I/C)⁻¹ · Y
```

Where:
- **K** is the kernel matrix: Kᵢⱼ = K(xᵢ, xⱼ)
- **I** is the identity matrix
- **C** is the regularization parameter
- **Y** is the target vector

For the **RBF (Radial Basis Function) kernel**:

```
K(x, y) = exp(-γ · ||x - y||²)
```

Where γ (gamma) controls the kernel width.

### Genetic Algorithm Optimization

The GA optimizes KELM hyperparameters through evolutionary principles:

#### Chromosome Representation
Each individual encodes:
- **C** ∈ [0.01, 1000] - Log-uniform distribution
- **γ** ∈ [0.001, 10] - Log-uniform distribution

#### Fitness Function
```python
def fitness(C, gamma):
    kelm = KELM(C=C, gamma=gamma)
    kelm.fit(X_train, y_train)
    y_pred = kelm.predict(X_val)
    return -MSE(y_val, y_pred)  # Negative MSE (maximize)
```

#### Genetic Operators

1. **Selection**: Tournament selection with size 3
2. **Crossover**: Blend crossover (BLX-α) with α=0.5
3. **Mutation**: Gaussian mutation in log-space
4. **Elitism**: Top 2 individuals preserved each generation

### Training Pipeline

```
┌─────────────────┐
│  Raw AQI Data   │
│  (Readings)     │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Feature         │
│ Engineering     │
│ - Lag features  │
│ - Time encoding │
│ - Pollutants    │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Train/Val       │
│ Split (80/20)   │
└────────┬────────┘
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Genetic         │────▶│ Evaluate        │
│ Algorithm       │◀────│ KELM            │
│ (50 gen)        │     │ (Fitness)       │
└────────┬────────┘     └─────────────────┘
         ▼
┌─────────────────┐
│ Optimal C, γ    │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Final KELM      │
│ Training        │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Model           │
│ Persistence     │
└─────────────────┘
```

## Feature Engineering

### Time-Based Features
| Feature | Encoding | Purpose |
|---------|----------|---------|
| Hour | sin/cos (cyclical) | Capture daily patterns |
| Day of Week | sin/cos (cyclical) | Weekly patterns |
| Month | sin/cos (cyclical) | Seasonal patterns |
| Is Weekend | Binary | Weekend effects |
| Is Rush Hour | Binary | Traffic influence |

### Lag Features
| Lag | Description |
|-----|-------------|
| t-1 | Previous hour AQI |
| t-2 | 2 hours ago |
| t-3 | 3 hours ago |
| t-6 | 6 hours ago |
| t-12 | 12 hours ago |
| t-24 | 24 hours ago (same time yesterday) |

### Pollutant Features
Direct pollutant concentrations when available:
- PM2.5, PM10, O₃, NO₂

## API Design

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/aqi/current/{location_id}` | Current AQI |
| GET | `/api/v1/aqi/history/{location_id}` | Historical data |
| GET | `/api/v1/predictions/{location_id}` | Future predictions |
| POST | `/api/v1/predictions/train` | Trigger training |
| POST | `/api/v1/locations` | Add location |
| GET | `/api/v1/locations` | List locations |

### WebSocket Protocol

```json
// Client → Server
{"type": "refresh"}

// Server → Client
{
  "type": "update",
  "location": {...},
  "current": {"aqi_value": 75, ...},
  "predictions": [...],
  "timestamp": "2024-01-27T12:00:00Z"
}
```

## Database Schema

### Entity Relationship

```
locations (1) ──────< (N) aqi_readings
    │
    └──────────< (N) predictions

model_metadata (standalone)
```

### Tables

**locations**: Geographic points being monitored
**aqi_readings**: Historical AQI measurements
**predictions**: GA-KELM generated forecasts
**model_metadata**: Trained model information

## Real-Time Update Flow

```
1. OpenWeatherMap API
         │
         ▼
2. APScheduler (every 15 min)
         │
         ▼
3. AQI Fetcher Service
         │
         ▼
4. PostgreSQL (aqi_readings)
         │
         ▼
5. WebSocket Broadcast
         │
         ▼
6. React Dashboard Update
```

## Scalability Considerations

1. **Horizontal Scaling**: Stateless FastAPI allows multiple instances
2. **Database Connection Pooling**: AsyncPG with proper pool management
3. **Caching**: In-memory caching for frequently accessed data
4. **Background Processing**: Async job scheduling with APScheduler
5. **WebSocket Management**: Connection manager for efficient broadcasts

## Advantages Over Traditional Systems

| Aspect | Traditional (SVM/ANN) | GA-KELM System |
|--------|----------------------|----------------|
| Training Speed | Minutes to hours | Seconds to minutes |
| Hyperparameter Tuning | Manual grid search | Automatic (GA) |
| Real-Time Capability | Limited | Native support |
| Scalability | Challenging | Cloud-native |
| Deployment | Complex | One-click (Railway) |
| Maintenance | High | Automated retraining |
