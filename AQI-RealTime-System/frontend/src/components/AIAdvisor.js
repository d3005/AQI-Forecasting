import React, { useState } from 'react';
import './AIAdvisor.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const AIAdvisor = ({ userLocation, onClose }) => {
    const [advice, setAdvice] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchAdvice = async () => {
        setLoading(true);
        setError(null);

        try {
            let url = `${API_URL}/ai/advice`;
            if (userLocation) {
                url += `?lat=${userLocation.lat}&lon=${userLocation.lon}`;
            }

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error('Failed to get AI advice');
            }

            const data = await response.json();
            setAdvice(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const formatAdvice = (text) => {
        if (!text) return null;

        // Split by bullet points or numbered items
        const lines = text.split('\n').filter(line => line.trim());

        return lines.map((line, index) => {
            // Check if it's a header-like line
            if (line.match(/^[0-9]+\./)) {
                return <p key={index} className="advice-numbered">{line}</p>;
            }
            if (line.startsWith('-') || line.startsWith('•')) {
                return <li key={index}>{line.replace(/^[-•]\s*/, '')}</li>;
            }
            if (line.includes(':') && line.length < 60) {
                return <h4 key={index}>{line}</h4>;
            }
            return <p key={index}>{line}</p>;
        });
    };

    return (
        <div className="ai-advisor-overlay" onClick={onClose}>
            <div className="ai-advisor-modal" onClick={e => e.stopPropagation()}>
                <div className="ai-advisor-header">
                    <div className="ai-advisor-title">
                        <span className="ai-icon">🤖</span>
                        <h2>AI Health Advisor</h2>
                    </div>
                    <button className="close-button" onClick={onClose}>×</button>
                </div>

                <div className="ai-advisor-content">
                    {!advice && !loading && !error && (
                        <div className="ai-intro">
                            <p>Get personalized health recommendations based on current air quality and weather conditions at your location.</p>
                            <button
                                className="get-advice-button"
                                onClick={fetchAdvice}
                            >
                                <span className="button-icon">✨</span>
                                Get AI Health Advice
                            </button>
                        </div>
                    )}

                    {loading && (
                        <div className="ai-loading">
                            <div className="loading-spinner"></div>
                            <p>Analyzing air quality data...</p>
                        </div>
                    )}

                    {error && (
                        <div className="ai-error">
                            <p>⚠️ {error}</p>
                            <button onClick={fetchAdvice}>Try Again</button>
                        </div>
                    )}

                    {advice && (
                        <div className="ai-result">
                            <div className="aqi-context">
                                <div className="context-item">
                                    <span className="context-label">Location</span>
                                    <span className="context-value">{advice.location}</span>
                                </div>
                                <div className="context-item">
                                    <span className="context-label">AQI</span>
                                    <span className={`context-value aqi-${advice.category?.toLowerCase().replace(/\s+/g, '-')}`}>
                                        {advice.aqi} ({advice.category})
                                    </span>
                                </div>
                                {advice.ai_powered && (
                                    <div className="ai-badge">
                                        <span>✨ AI Powered</span>
                                    </div>
                                )}
                            </div>

                            <div className="advice-text">
                                {formatAdvice(advice.advice)}
                            </div>

                            <button
                                className="refresh-button"
                                onClick={fetchAdvice}
                            >
                                🔄 Refresh Advice
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AIAdvisor;
