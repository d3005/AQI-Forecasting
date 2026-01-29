import React, { useState, useEffect, useCallback } from 'react';
import Charts from './Charts';
import './Dashboard.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Get AQI category class
function getAQIClass(aqi) {
    if (aqi <= 50) return 'good';
    if (aqi <= 100) return 'moderate';
    if (aqi <= 150) return 'unhealthy-sensitive';
    if (aqi <= 200) return 'unhealthy';
    if (aqi <= 300) return 'very-unhealthy';
    return 'hazardous';
}

// Get AQI emoji
function getAQIEmoji(aqi) {
    if (aqi <= 50) return '😊';
    if (aqi <= 100) return '😐';
    if (aqi <= 150) return '😷';
    if (aqi <= 200) return '🤢';
    if (aqi <= 300) return '😨';
    return '💀';
}

// Get health advisory
function getHealthAdvisory(aqi) {
    if (aqi <= 50) return 'Air quality is satisfactory. Enjoy outdoor activities!';
    if (aqi <= 100) return 'Acceptable air quality. Sensitive individuals should limit prolonged outdoor exertion.';
    if (aqi <= 150) return 'Sensitive groups may experience health effects. Consider reducing outdoor activities.';
    if (aqi <= 200) return 'Everyone may begin to experience health effects. Limit outdoor activities.';
    if (aqi <= 300) return 'Health alert! Everyone may experience serious health effects. Avoid outdoor activities.';
    return 'Health emergency! The air is hazardous. Stay indoors!';
}

function Dashboard() {
    const [currentData, setCurrentData] = useState(null);
    const [prediction, setPrediction] = useState(null);
    const [history, setHistory] = useState([]);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [lastUpdate, setLastUpdate] = useState(null);

    // Fetch all data
    const fetchAllData = useCallback(async () => {
        try {
            setError(null);

            // Fetch current AQI
            const currentRes = await fetch(`${API_URL}/current`);
            if (currentRes.ok) {
                const data = await currentRes.json();
                setCurrentData(data);
            }

            // Fetch prediction
            const predRes = await fetch(`${API_URL}/predict`);
            if (predRes.ok) {
                const data = await predRes.json();
                setPrediction(data);
            }

            // Fetch history
            const histRes = await fetch(`${API_URL}/history?limit=24`);
            if (histRes.ok) {
                const data = await histRes.json();
                setHistory(data.data || []);
            }

            // Fetch stats
            const statsRes = await fetch(`${API_URL}/stats`);
            if (statsRes.ok) {
                const data = await statsRes.json();
                setStats(data);
            }

            setLastUpdate(new Date());

        } catch (err) {
            console.error('Fetch error:', err);
            setError('Failed to connect to server. Is the backend running?');
        } finally {
            setLoading(false);
        }
    }, []);

    // Initial fetch and auto-refresh
    useEffect(() => {
        fetchAllData();

        // Auto-refresh every 60 seconds
        const interval = setInterval(fetchAllData, 60000);
        return () => clearInterval(interval);
    }, [fetchAllData]);

    // Handle manual refresh
    const handleRefresh = async () => {
        setLoading(true);
        try {
            await fetch(`${API_URL}/update`);
            await fetchAllData();
        } catch (err) {
            setError('Failed to update data');
        }
    };

    // Loading state
    if (loading && !currentData) {
        return (
            <div className="dashboard container">
                <div className="loading">
                    <div className="spinner"></div>
                </div>
            </div>
        );
    }

    const aqi = currentData?.aqi || prediction?.AQI_Prediction || 0;
    const category = currentData?.category || prediction?.category || 'Unknown';
    const aqiClass = getAQIClass(aqi);

    return (
        <div className="dashboard container">
            {/* Error Banner */}
            {error && (
                <div className="error-banner">
                    ⚠️ {error}
                </div>
            )}

            {/* Header */}
            <div className="dashboard-header">
                <div>
                    <h2>Real-Time AQI Dashboard</h2>
                    {lastUpdate && (
                        <p className="last-update">
                            Last updated: {lastUpdate.toLocaleTimeString()}
                        </p>
                    )}
                </div>
                <button className="btn btn-primary" onClick={handleRefresh} disabled={loading}>
                    {loading ? '⏳ Updating...' : '🔄 Refresh'}
                </button>
            </div>

            {/* Main Grid */}
            <div className="dashboard-grid">
                {/* AQI Card */}
                <div className={`card aqi-card bg-${aqiClass} fade-in`}>
                    <div className="aqi-header">
                        <span className="location">📍 Current Location</span>
                        <span className={`aqi-badge aqi-${aqiClass}`}>{category}</span>
                    </div>

                    <div className="aqi-display">
                        <span className="aqi-emoji">{getAQIEmoji(aqi)}</span>
                        <span className={`aqi-value aqi-${aqiClass}`}>{Math.round(aqi)}</span>
                        <span className="aqi-label">Air Quality Index</span>
                    </div>

                    <div className="health-advisory">
                        <strong>💡 Health Advisory:</strong>
                        <p>{getHealthAdvisory(aqi)}</p>
                    </div>
                </div>

                {/* Prediction Card */}
                <div className="card prediction-card fade-in">
                    <h3>🧬 GA-KELM Prediction</h3>
                    <div className="prediction-display">
                        <span className={`prediction-value aqi-${getAQIClass(prediction?.AQI_Prediction || aqi)}`}>
                            {Math.round(prediction?.AQI_Prediction || aqi)}
                        </span>
                        <span className="prediction-label">Predicted AQI</span>
                    </div>
                    <p className="prediction-note">
                        Powered by Genetic Algorithm optimized Kernel Extreme Learning Machine
                    </p>
                </div>

                {/* Pollutants Card */}
                <div className="card pollutants-card fade-in">
                    <h3>🌫️ Pollutant Levels</h3>
                    <div className="pollutants-grid">
                        <div className="pollutant-item">
                            <span className="pollutant-value">{currentData?.pm25?.toFixed(1) || '--'}</span>
                            <span className="pollutant-label">PM2.5</span>
                            <span className="pollutant-unit">μg/m³</span>
                        </div>
                        <div className="pollutant-item">
                            <span className="pollutant-value">{currentData?.pm10?.toFixed(1) || '--'}</span>
                            <span className="pollutant-label">PM10</span>
                            <span className="pollutant-unit">μg/m³</span>
                        </div>
                        <div className="pollutant-item">
                            <span className="pollutant-value">{currentData?.o3?.toFixed(1) || '--'}</span>
                            <span className="pollutant-label">O₃</span>
                            <span className="pollutant-unit">μg/m³</span>
                        </div>
                        <div className="pollutant-item">
                            <span className="pollutant-value">{currentData?.no2?.toFixed(1) || '--'}</span>
                            <span className="pollutant-label">NO₂</span>
                            <span className="pollutant-unit">μg/m³</span>
                        </div>
                        <div className="pollutant-item">
                            <span className="pollutant-value">{currentData?.so2?.toFixed(1) || '--'}</span>
                            <span className="pollutant-label">SO₂</span>
                            <span className="pollutant-unit">μg/m³</span>
                        </div>
                        <div className="pollutant-item">
                            <span className="pollutant-value">{currentData?.co?.toFixed(2) || '--'}</span>
                            <span className="pollutant-label">CO</span>
                            <span className="pollutant-unit">mg/m³</span>
                        </div>
                    </div>
                </div>

                {/* Stats Card */}
                <div className="card stats-card fade-in">
                    <h3>📊 Statistics (24h)</h3>
                    <div className="stats-grid">
                        <div className="stat-item">
                            <span className="stat-value aqi-good">{stats?.min || '--'}</span>
                            <span className="stat-label">Min AQI</span>
                        </div>
                        <div className="stat-item">
                            <span className="stat-value aqi-unhealthy">{stats?.max || '--'}</span>
                            <span className="stat-label">Max AQI</span>
                        </div>
                        <div className="stat-item">
                            <span className="stat-value">{stats?.avg || '--'}</span>
                            <span className="stat-label">Avg AQI</span>
                        </div>
                        <div className="stat-item">
                            <span className="stat-value">{stats?.count || '--'}</span>
                            <span className="stat-label">Readings</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Charts */}
            <Charts history={history} />
        </div>
    );
}

export default Dashboard;
