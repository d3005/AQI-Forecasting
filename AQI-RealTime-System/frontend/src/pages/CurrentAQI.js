import React, { useState, useEffect } from 'react';
import { useLocationData } from '../App';
import './CurrentAQI.css';

function CurrentAQI() {
    const { userLocation, locationName, isLoadingLocation, API_URL } = useLocationData();
    const [data, setData] = useState(null);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [lastUpdate, setLastUpdate] = useState(null);

    useEffect(() => {
        if (userLocation) {
            fetchData();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [userLocation]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [currentRes, statsRes] = await Promise.all([
                fetch(`${API_URL}/current?lat=${userLocation.lat}&lon=${userLocation.lon}`),
                fetch(`${API_URL}/stats`)
            ]);

            const currentData = await currentRes.json();
            const statsData = await statsRes.json();

            setData(currentData);
            setStats(statsData);
            setLastUpdate(new Date());
        } catch (err) {
            console.error('Error:', err);
        }
        setLoading(false);
    };

    const getAQIClass = (aqi) => {
        if (aqi <= 50) return 'good';
        if (aqi <= 100) return 'moderate';
        if (aqi <= 150) return 'sensitive';
        if (aqi <= 200) return 'unhealthy';
        if (aqi <= 300) return 'very-unhealthy';
        return 'hazardous';
    };

    const getAQIEmoji = (aqi) => {
        if (aqi <= 50) return '😊';
        if (aqi <= 100) return '🙂';
        if (aqi <= 150) return '😐';
        if (aqi <= 200) return '😷';
        if (aqi <= 300) return '🤢';
        return '💀';
    };

    const getHealthAdvice = (category) => {
        const advice = {
            'Good': 'Air quality is satisfactory. Enjoy outdoor activities!',
            'Moderate': 'Air quality is acceptable. Unusually sensitive people should reduce outdoor activities.',
            'Unhealthy for Sensitive Groups': 'Sensitive groups should reduce prolonged outdoor exertion.',
            'Unhealthy': 'Everyone may begin to experience health effects. Limit outdoor activities.',
            'Very Unhealthy': 'Health warnings. Everyone should avoid outdoor activities.',
            'Hazardous': 'Emergency conditions! Stay indoors and keep windows closed.'
        };
        return advice[category] || 'Data unavailable';
    };

    if (isLoadingLocation || loading) {
        return (
            <div className="loading">
                <div className="spinner"></div>
                <p>Loading current air quality data...</p>
            </div>
        );
    }

    if (!data) {
        return (
            <div className="error-state">
                <h2>Unable to load data</h2>
                <button onClick={fetchData} className="btn btn-primary">Retry</button>
            </div>
        );
    }

    const aqiClass = getAQIClass(data.aqi);

    return (
        <div className="current-page fade-in">
            <div className="page-header">
                <h1 className="page-title">Current Air Quality</h1>
                <p className="page-subtitle">
                    📍 Real-time data for <strong>{locationName}</strong>
                </p>
                {lastUpdate && (
                    <p className="last-update">
                        Last updated: {lastUpdate.toLocaleTimeString()}
                        <button onClick={fetchData} className="refresh-btn">🔄 Refresh</button>
                    </p>
                )}
            </div>

            {/* Main AQI Card */}
            <div className={`main-aqi-card ${aqiClass}`}>
                <div className="aqi-visual">
                    <div className="aqi-emoji">{getAQIEmoji(data.aqi)}</div>
                    <div className="aqi-number">{data.aqi}</div>
                    <div className="aqi-label">Air Quality Index</div>
                </div>
                <div className="aqi-info">
                    <div className={`aqi-badge ${aqiClass}`}>{data.category}</div>
                    <div className="health-advice">
                        <h3>💡 Health Advisory</h3>
                        <p>{getHealthAdvice(data.category)}</p>
                    </div>
                </div>
            </div>

            {/* Pollutants Grid */}
            <section className="section">
                <h2 className="section-title">🧪 Pollutant Levels</h2>
                <div className="pollutants-grid">
                    <div className="pollutant-card">
                        <div className="pollutant-name">PM2.5</div>
                        <div className="pollutant-value">{data.pm25}</div>
                        <div className="pollutant-unit">μg/m³</div>
                        <div className="pollutant-desc">Fine particles</div>
                    </div>
                    <div className="pollutant-card">
                        <div className="pollutant-name">PM10</div>
                        <div className="pollutant-value">{data.pm10}</div>
                        <div className="pollutant-unit">μg/m³</div>
                        <div className="pollutant-desc">Coarse particles</div>
                    </div>
                    <div className="pollutant-card">
                        <div className="pollutant-name">O₃</div>
                        <div className="pollutant-value">{data.o3}</div>
                        <div className="pollutant-unit">μg/m³</div>
                        <div className="pollutant-desc">Ozone</div>
                    </div>
                    <div className="pollutant-card">
                        <div className="pollutant-name">NO₂</div>
                        <div className="pollutant-value">{data.no2}</div>
                        <div className="pollutant-unit">μg/m³</div>
                        <div className="pollutant-desc">Nitrogen dioxide</div>
                    </div>
                    <div className="pollutant-card">
                        <div className="pollutant-name">SO₂</div>
                        <div className="pollutant-value">{data.so2}</div>
                        <div className="pollutant-unit">μg/m³</div>
                        <div className="pollutant-desc">Sulfur dioxide</div>
                    </div>
                    <div className="pollutant-card">
                        <div className="pollutant-name">CO</div>
                        <div className="pollutant-value">{data.co}</div>
                        <div className="pollutant-unit">mg/m³</div>
                        <div className="pollutant-desc">Carbon monoxide</div>
                    </div>
                </div>
            </section>

            {/* Statistics */}
            {stats && stats.count > 0 && (
                <section className="section">
                    <h2 className="section-title">📊 24-Hour Statistics</h2>
                    <div className="stats-grid">
                        <div className="stat-item">
                            <div className="stat-icon">⬇️</div>
                            <div className="stat-value aqi-good">{stats.min}</div>
                            <div className="stat-label">Minimum AQI</div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-icon">⬆️</div>
                            <div className="stat-value aqi-unhealthy">{stats.max}</div>
                            <div className="stat-label">Maximum AQI</div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-icon">📈</div>
                            <div className="stat-value">{stats.avg}</div>
                            <div className="stat-label">Average AQI</div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-icon">📝</div>
                            <div className="stat-value">{stats.count}</div>
                            <div className="stat-label">Data Points</div>
                        </div>
                    </div>
                </section>
            )}

            {/* Location Info */}
            <section className="section location-info">
                <h2 className="section-title">📍 Location Details</h2>
                <div className="location-grid">
                    <div className="location-item">
                        <strong>Latitude:</strong> {data.latitude}
                    </div>
                    <div className="location-item">
                        <strong>Longitude:</strong> {data.longitude}
                    </div>
                    <div className="location-item">
                        <strong>Data Source:</strong> {data.source}
                    </div>
                </div>
            </section>
        </div>
    );
}

export default CurrentAQI;
