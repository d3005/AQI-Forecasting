import React from 'react';
import {
    Wind,
    Droplets,
    AlertTriangle,
    Leaf
} from 'lucide-react';
import './AQICard.css';

/**
 * Get AQI category info
 */
function getAQICategory(value) {
    if (value <= 50) return { label: 'Good', class: 'aqi-good', emoji: '😊' };
    if (value <= 100) return { label: 'Moderate', class: 'aqi-moderate', emoji: '😐' };
    if (value <= 150) return { label: 'Unhealthy for Sensitive', class: 'aqi-unhealthy-sensitive', emoji: '😷' };
    if (value <= 200) return { label: 'Unhealthy', class: 'aqi-unhealthy', emoji: '🤢' };
    if (value <= 300) return { label: 'Very Unhealthy', class: 'aqi-very-unhealthy', emoji: '😨' };
    return { label: 'Hazardous', class: 'aqi-hazardous', emoji: '💀' };
}

/**
 * AQI Card Component
 * Displays current AQI with color-coded status
 */
export default function AQICard({ data, isLoading, isLive }) {
    if (isLoading) {
        return (
            <div className="aqi-card glass-card">
                <div className="aqi-card-header">
                    <div className="skeleton" style={{ width: '150px', height: '24px' }}></div>
                </div>
                <div className="aqi-value-container">
                    <div className="skeleton" style={{ width: '120px', height: '80px' }}></div>
                </div>
                <div className="aqi-pollutants">
                    {[1, 2, 3, 4].map(i => (
                        <div key={i} className="skeleton" style={{ width: '100%', height: '40px' }}></div>
                    ))}
                </div>
            </div>
        );
    }

    if (!data) {
        return (
            <div className="aqi-card glass-card">
                <div className="aqi-empty">
                    <Wind size={48} />
                    <p>No AQI data available</p>
                </div>
            </div>
        );
    }

    const category = getAQICategory(data.aqi_value);
    const recordedTime = new Date(data.recorded_at).toLocaleTimeString();

    return (
        <div className={`aqi-card glass-card glass-card-glow ${category.class}`}>
            {/* Header */}
            <div className="aqi-card-header">
                <div className="aqi-location">
                    <h3>{data.city}</h3>
                    {data.country && <span className="aqi-country">{data.country}</span>}
                </div>
                {isLive && (
                    <div className="aqi-live-badge">
                        <span className="status-dot status-online"></span>
                        Live
                    </div>
                )}
            </div>

            {/* Main AQI Display */}
            <div className="aqi-value-container">
                <div className="aqi-emoji">{category.emoji}</div>
                <div className="aqi-value">{data.aqi_value}</div>
                <div className="aqi-label">{category.label}</div>
                <div className="aqi-time">Updated: {recordedTime}</div>
            </div>

            {/* Health Advisory */}
            {data.health_advisory && (
                <div className="aqi-advisory">
                    <AlertTriangle size={16} />
                    <p>{data.health_advisory}</p>
                </div>
            )}

            {/* Pollutants Grid */}
            <div className="aqi-pollutants">
                <PollutantItem
                    icon={<Leaf size={16} />}
                    label="PM2.5"
                    value={data.pm25}
                    unit="μg/m³"
                />
                <PollutantItem
                    icon={<Droplets size={16} />}
                    label="PM10"
                    value={data.pm10}
                    unit="μg/m³"
                />
                <PollutantItem
                    icon={<Wind size={16} />}
                    label="O₃"
                    value={data.o3}
                    unit="μg/m³"
                />
                <PollutantItem
                    icon={<Wind size={16} />}
                    label="NO₂"
                    value={data.no2}
                    unit="μg/m³"
                />
                <PollutantItem
                    icon={<Wind size={16} />}
                    label="SO₂"
                    value={data.so2}
                    unit="μg/m³"
                />
                <PollutantItem
                    icon={<Wind size={16} />}
                    label="CO"
                    value={data.co}
                    unit="μg/m³"
                />
            </div>
        </div>
    );
}

/**
 * Individual pollutant display
 */
function PollutantItem({ icon, label, value, unit }) {
    const displayValue = value !== null && value !== undefined
        ? value.toFixed(1)
        : '--';

    return (
        <div className="pollutant-item">
            <div className="pollutant-icon">{icon}</div>
            <div className="pollutant-info">
                <span className="pollutant-label">{label}</span>
                <span className="pollutant-value">
                    {displayValue} <small>{unit}</small>
                </span>
            </div>
        </div>
    );
}
