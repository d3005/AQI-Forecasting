import React from 'react';
import {
    TrendingUp,
    TrendingDown,
    Minus,
    Clock,
    BarChart3,
    Target
} from 'lucide-react';
import './StatsCard.css';

/**
 * Statistics Card Component
 * Displays AQI statistics and trends
 */
export default function StatsCard({ stats, isLoading }) {
    if (isLoading) {
        return (
            <div className="stats-card glass-card">
                <div className="stats-header">
                    <div className="skeleton" style={{ width: '150px', height: '24px' }}></div>
                </div>
                <div className="stats-grid">
                    {[1, 2, 3, 4].map(i => (
                        <div key={i} className="skeleton stat-skeleton"></div>
                    ))}
                </div>
            </div>
        );
    }

    if (!stats) {
        return (
            <div className="stats-card glass-card">
                <div className="stats-empty">
                    <BarChart3 size={32} />
                    <p>No statistics available</p>
                </div>
            </div>
        );
    }

    const getTrendIcon = () => {
        switch (stats.trend) {
            case 'improving':
                return <TrendingDown className="trend-improving" />;
            case 'worsening':
                return <TrendingUp className="trend-worsening" />;
            default:
                return <Minus className="trend-stable" />;
        }
    };

    const getTrendLabel = () => {
        switch (stats.trend) {
            case 'improving': return 'Improving';
            case 'worsening': return 'Worsening';
            case 'stable': return 'Stable';
            default: return 'Unknown';
        }
    };

    return (
        <div className="stats-card glass-card">
            <div className="stats-header">
                <div className="stats-title">
                    <BarChart3 size={20} />
                    <h3>Statistics ({stats.hours}h)</h3>
                </div>
                <div className="stats-location">{stats.city}</div>
            </div>

            <div className="stats-grid">
                {/* Min AQI */}
                <div className="stat-item">
                    <div className="stat-icon stat-icon-success">
                        <TrendingDown size={18} />
                    </div>
                    <div className="stat-content">
                        <span className="stat-label">Minimum</span>
                        <span className="stat-value">{stats.min ?? '--'}</span>
                    </div>
                </div>

                {/* Max AQI */}
                <div className="stat-item">
                    <div className="stat-icon stat-icon-danger">
                        <TrendingUp size={18} />
                    </div>
                    <div className="stat-content">
                        <span className="stat-label">Maximum</span>
                        <span className="stat-value">{stats.max ?? '--'}</span>
                    </div>
                </div>

                {/* Average */}
                <div className="stat-item">
                    <div className="stat-icon stat-icon-primary">
                        <Target size={18} />
                    </div>
                    <div className="stat-content">
                        <span className="stat-label">Average</span>
                        <span className="stat-value">{stats.avg ?? '--'}</span>
                    </div>
                </div>

                {/* Trend */}
                <div className="stat-item">
                    <div className={`stat-icon stat-icon-${stats.trend || 'default'}`}>
                        {getTrendIcon()}
                    </div>
                    <div className="stat-content">
                        <span className="stat-label">Trend</span>
                        <span className="stat-value stat-trend">{getTrendLabel()}</span>
                    </div>
                </div>
            </div>

            <div className="stats-footer">
                <Clock size={14} />
                <span>Based on {stats.count} readings</span>
            </div>
        </div>
    );
}
