# Database Schema

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATABASE SCHEMA                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐                                                    │
│  │      locations      │                                                    │
│  ├─────────────────────┤                                                    │
│  │ id          PK      │                                                    │
│  │ city        VARCHAR │                                                    │
│  │ country     VARCHAR │◀──────────────────────────────────────────┐       │
│  │ latitude    FLOAT   │                                           │       │
│  │ longitude   FLOAT   │                                           │       │
│  │ created_at DATETIME │                                           │       │
│  └─────────────────────┘                                           │       │
│           │                                                         │       │
│           │ 1:N                                                     │ 1:N   │
│           ▼                                                         │       │
│  ┌─────────────────────┐                             ┌─────────────────────┐
│  │    aqi_readings     │                             │     predictions     │
│  ├─────────────────────┤                             ├─────────────────────┤
│  │ id          PK      │                             │ id          PK      │
│  │ location_id FK      │                             │ location_id FK      │
│  │ pm25        FLOAT   │                             │ predicted_aqi INT   │
│  │ pm10        FLOAT   │                             │ predicted_cat VARCHAR│
│  │ o3          FLOAT   │                             │ confidence   FLOAT  │
│  │ no2         FLOAT   │                             │ prediction_for TIME │
│  │ so2         FLOAT   │                             │ created_at  DATETIME│
│  │ co          FLOAT   │                             └─────────────────────┘
│  │ aqi_value   INT     │                                                    │
│  │ aqi_category VARCHAR│                                                    │
│  │ recorded_at DATETIME│                             ┌─────────────────────┐
│  │ created_at DATETIME │                             │   model_metadata    │
│  └─────────────────────┘                             ├─────────────────────┤
│                                                      │ id          PK      │
│                                                      │ model_version VARCHAR│
│                                                      │ best_c      FLOAT   │
│                                                      │ best_gamma  FLOAT   │
│                                                      │ train_rmse  FLOAT   │
│                                                      │ val_rmse    FLOAT   │
│                                                      │ train_mae   FLOAT   │
│                                                      │ val_mae     FLOAT   │
│                                                      │ generations_run INT │
│                                                      │ population_size INT │
│                                                      │ trained_at DATETIME │
│                                                      │ model_binary BYTEA  │
│                                                      └─────────────────────┘
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Table Definitions

### 1. locations

Stores geographic locations being monitored for air quality.

```sql
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100),
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_coordinates UNIQUE (latitude, longitude)
);

CREATE INDEX idx_locations_city ON locations(city);
CREATE INDEX idx_locations_coordinates ON locations(latitude, longitude);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-incrementing identifier |
| city | VARCHAR(100) | NOT NULL | City name |
| country | VARCHAR(100) | NULLABLE | Country name |
| latitude | FLOAT | NOT NULL | Geographic latitude (-90 to 90) |
| longitude | FLOAT | NOT NULL | Geographic longitude (-180 to 180) |
| created_at | TIMESTAMP | DEFAULT NOW() | Record creation time |

### 2. aqi_readings

Stores historical air quality readings from external APIs.

```sql
CREATE TABLE aqi_readings (
    id SERIAL PRIMARY KEY,
    location_id INTEGER NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    pm25 FLOAT,
    pm10 FLOAT,
    o3 FLOAT,
    no2 FLOAT,
    so2 FLOAT,
    co FLOAT,
    aqi_value INTEGER NOT NULL,
    aqi_category VARCHAR(50) NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_aqi CHECK (aqi_value >= 0 AND aqi_value <= 500)
);

CREATE INDEX idx_aqi_readings_location ON aqi_readings(location_id);
CREATE INDEX idx_aqi_readings_recorded ON aqi_readings(recorded_at DESC);
CREATE INDEX idx_aqi_readings_location_time ON aqi_readings(location_id, recorded_at DESC);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-incrementing identifier |
| location_id | INTEGER | FK (locations.id) | Reference to location |
| pm25 | FLOAT | NULLABLE | PM2.5 concentration (μg/m³) |
| pm10 | FLOAT | NULLABLE | PM10 concentration (μg/m³) |
| o3 | FLOAT | NULLABLE | Ozone concentration (μg/m³) |
| no2 | FLOAT | NULLABLE | NO₂ concentration (μg/m³) |
| so2 | FLOAT | NULLABLE | SO₂ concentration (μg/m³) |
| co | FLOAT | NULLABLE | CO concentration (μg/m³) |
| aqi_value | INTEGER | NOT NULL, CHECK | AQI value (0-500) |
| aqi_category | VARCHAR(50) | NOT NULL | Category label |
| recorded_at | TIMESTAMP | NOT NULL | Time of measurement |
| created_at | TIMESTAMP | DEFAULT NOW() | Record creation time |

### 3. predictions

Stores GA-KELM model predictions for future AQI values.

```sql
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    location_id INTEGER NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    predicted_aqi INTEGER NOT NULL,
    predicted_category VARCHAR(50) NOT NULL,
    confidence FLOAT,
    prediction_for TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_predicted_aqi CHECK (predicted_aqi >= 0 AND predicted_aqi <= 500),
    CONSTRAINT valid_confidence CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1))
);

CREATE INDEX idx_predictions_location ON predictions(location_id);
CREATE INDEX idx_predictions_for ON predictions(prediction_for);
CREATE INDEX idx_predictions_location_for ON predictions(location_id, prediction_for);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-incrementing identifier |
| location_id | INTEGER | FK (locations.id) | Reference to location |
| predicted_aqi | INTEGER | NOT NULL, CHECK | Predicted AQI value |
| predicted_category | VARCHAR(50) | NOT NULL | Predicted category |
| confidence | FLOAT | CHECK (0-1) | Model confidence score |
| prediction_for | TIMESTAMP | NOT NULL | Future time being predicted |
| created_at | TIMESTAMP | DEFAULT NOW() | Prediction creation time |

### 4. model_metadata

Stores information about trained GA-KELM models.

```sql
CREATE TABLE model_metadata (
    id SERIAL PRIMARY KEY,
    model_version VARCHAR(50) NOT NULL,
    best_c FLOAT NOT NULL,
    best_gamma FLOAT NOT NULL,
    train_rmse FLOAT,
    val_rmse FLOAT,
    train_mae FLOAT,
    val_mae FLOAT,
    generations_run INTEGER,
    population_size INTEGER,
    trained_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    model_binary BYTEA
);

CREATE INDEX idx_model_metadata_version ON model_metadata(model_version);
CREATE INDEX idx_model_metadata_trained ON model_metadata(trained_at DESC);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Auto-incrementing identifier |
| model_version | VARCHAR(50) | NOT NULL | Version identifier |
| best_c | FLOAT | NOT NULL | Optimal C hyperparameter |
| best_gamma | FLOAT | NOT NULL | Optimal gamma hyperparameter |
| train_rmse | FLOAT | NULLABLE | Training RMSE |
| val_rmse | FLOAT | NULLABLE | Validation RMSE |
| train_mae | FLOAT | NULLABLE | Training MAE |
| val_mae | FLOAT | NULLABLE | Validation MAE |
| generations_run | INTEGER | NULLABLE | GA generations executed |
| population_size | INTEGER | NULLABLE | GA population size |
| trained_at | TIMESTAMP | DEFAULT NOW() | Training completion time |
| model_binary | BYTEA | NULLABLE | Serialized model (joblib) |

## AQI Category Values

The `aqi_category` and `predicted_category` fields use EPA standard categories:

| AQI Range | Category |
|-----------|----------|
| 0-50 | Good |
| 51-100 | Moderate |
| 101-150 | Unhealthy for Sensitive Groups |
| 151-200 | Unhealthy |
| 201-300 | Very Unhealthy |
| 301-500 | Hazardous |

## Data Retention Policy

For production deployment, implement data retention:

```sql
-- Delete AQI readings older than 30 days
DELETE FROM aqi_readings 
WHERE recorded_at < NOW() - INTERVAL '30 days';

-- Delete predictions that have passed
DELETE FROM predictions 
WHERE prediction_for < NOW() - INTERVAL '7 days';

-- Keep only the latest 5 trained models
DELETE FROM model_metadata 
WHERE id NOT IN (
    SELECT id FROM model_metadata 
    ORDER BY trained_at DESC 
    LIMIT 5
);
```

## Query Examples

### Get Current AQI for Location
```sql
SELECT * FROM aqi_readings 
WHERE location_id = $1 
ORDER BY recorded_at DESC 
LIMIT 1;
```

### Get 24-Hour Statistics
```sql
SELECT 
    MIN(aqi_value) as min_aqi,
    MAX(aqi_value) as max_aqi,
    ROUND(AVG(aqi_value)) as avg_aqi,
    COUNT(*) as reading_count
FROM aqi_readings 
WHERE location_id = $1 
AND recorded_at >= NOW() - INTERVAL '24 hours';
```

### Get Future Predictions
```sql
SELECT * FROM predictions 
WHERE location_id = $1 
AND prediction_for > NOW() 
ORDER BY prediction_for ASC;
```

### Get Latest Trained Model
```sql
SELECT * FROM model_metadata 
ORDER BY trained_at DESC 
LIMIT 1;
```
