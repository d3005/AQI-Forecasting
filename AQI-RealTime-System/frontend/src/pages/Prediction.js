import React, { useState, useEffect } from 'react';
import { useLocationData } from '../App';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import './Prediction.css';

function Prediction() {
    const { userLocation, locationName, isLoadingLocation, API_URL } = useLocationData();
    const [prediction, setPrediction] = useState(null);
    const [currentAQI, setCurrentAQI] = useState(null);
    const [history, setHistory] = useState([]);
    const [modelInfo, setModelInfo] = useState(null);
    const [loading, setLoading] = useState(true);
    const [training, setTraining] = useState(false);

    useEffect(() => {
        if (userLocation) {
            fetchData();
        }
    }, [userLocation]);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [predRes, currentRes, historyRes, modelRes] = await Promise.all([
                fetch(`${API_URL}/predict`),
                fetch(`${API_URL}/current`),
                fetch(`${API_URL}/history?limit=24`),
                fetch(`${API_URL}/model/info`)
            ]);

            setPrediction(await predRes.json());
            setCurrentAQI(await currentRes.json());
            const histData = await historyRes.json();
            setHistory(histData.data || []);
            setModelInfo(await modelRes.json());
        } catch (err) {
            console.error('Error:', err);
        }
        setLoading(false);
    };

    const trainModel = async () => {
        setTraining(true);
        try {
            const res = await fetch(`${API_URL}/train`, { method: 'POST' });
            const result = await res.json();
            alert(`Training ${result.status}: ${result.message}`);
            fetchData();
        } catch (err) {
            alert('Training failed: ' + err.message);
        }
        setTraining(false);
    };

    const getAQIClass = (aqi) => {
        if (aqi <= 50) return 'good';
        if (aqi <= 100) return 'moderate';
        if (aqi <= 150) return 'sensitive';
        if (aqi <= 200) return 'unhealthy';
        if (aqi <= 300) return 'very-unhealthy';
        return 'hazardous';
    };

    const chartData = history.slice().reverse().map((item, index) => ({
        time: index,
        aqi: item.aqi,
        timestamp: new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }));

    if (isLoadingLocation || loading) {
        return (
            <div className="loading">
                <div className="spinner"></div>
                <p>Loading prediction data...</p>
            </div>
        );
    }

    return (
        <div className="prediction-page fade-in">
            <div className="page-header">
                <h1 className="page-title">🔮 AQI Prediction</h1>
                <p className="page-subtitle">
                    AI-powered forecasting using GA-KELM for <strong>{locationName}</strong>
                </p>
            </div>

            {/* Prediction vs Current */}
            <div className="prediction-comparison">
                <div className={`comparison-card current ${getAQIClass(currentAQI?.aqi)}`}>
                    <div className="comparison-label">Current AQI</div>
                    <div className="comparison-value">{currentAQI?.aqi || '--'}</div>
                    <div className="comparison-category">{currentAQI?.category}</div>
                </div>

                <div className="comparison-arrow">→</div>

                <div className={`comparison-card prediction ${getAQIClass(prediction?.AQI_Prediction)}`}>
                    <div className="comparison-label">🧬 GA-KELM Prediction</div>
                    <div className="comparison-value">
                        {prediction?.AQI_Prediction ? Math.round(prediction.AQI_Prediction) : '--'}
                    </div>
                    <div className="comparison-category">{prediction?.category}</div>
                </div>
            </div>

            {/* Model Info */}
            <section className="section model-section">
                <div className="model-header">
                    <h2 className="section-title">🧠 GA-KELM Model</h2>
                    <button
                        onClick={trainModel}
                        className="btn btn-primary"
                        disabled={training}
                    >
                        {training ? 'Training...' : '🔄 Retrain Model'}
                    </button>
                </div>

                <div className="model-info-grid">
                    <div className="model-card">
                        <div className="model-label">Status</div>
                        <div className={`model-value ${modelInfo?.trained ? 'success' : 'warning'}`}>
                            {modelInfo?.trained ? '✅ Trained' : '⚠️ Not Trained'}
                        </div>
                    </div>

                    {modelInfo?.trained && modelInfo?.parameters && (
                        <>
                            <div className="model-card">
                                <div className="model-label">Algorithm</div>
                                <div className="model-value">{modelInfo.algorithm}</div>
                            </div>
                            <div className="model-card">
                                <div className="model-label">C (Regularization)</div>
                                <div className="model-value">{modelInfo.parameters.C?.toFixed(4)}</div>
                            </div>
                            <div className="model-card">
                                <div className="model-label">γ (Gamma)</div>
                                <div className="model-value">{modelInfo.parameters.gamma?.toFixed(4)}</div>
                            </div>
                        </>
                    )}
                </div>
            </section>

            {/* Algorithm Explanation */}
            <section className="section algorithm-section">
                <h2 className="section-title">📚 How GA-KELM Works</h2>
                <div className="algorithm-grid">
                    <div className="algo-card">
                        <div className="algo-icon">🧬</div>
                        <h3>Genetic Algorithm (GA)</h3>
                        <p>Optimizes hyperparameters (C, γ) through natural selection, crossover, and mutation to find the best model configuration.</p>
                    </div>
                    <div className="algo-card">
                        <div className="algo-icon">⚡</div>
                        <h3>Kernel ELM (KELM)</h3>
                        <p>Uses RBF kernel for non-linear mapping with fast closed-form solution, avoiding slow iterative training.</p>
                    </div>
                    <div className="algo-card">
                        <div className="algo-icon">🎯</div>
                        <h3>Prediction</h3>
                        <p>Combines pollutant data (PM2.5, PM10, O₃, etc.) to predict future AQI values with high accuracy.</p>
                    </div>
                </div>
            </section>

            {/* Historical Chart */}
            {chartData.length > 0 && (
                <section className="section chart-section">
                    <h2 className="section-title">📈 AQI Trend (Last 24 Readings)</h2>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height={350}>
                            <AreaChart data={chartData}>
                                <defs>
                                    <linearGradient id="aqiGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.1)" />
                                <XAxis
                                    dataKey="timestamp"
                                    stroke="#64748b"
                                    tick={{ fontSize: 12 }}
                                />
                                <YAxis
                                    stroke="#64748b"
                                    domain={[0, 'auto']}
                                    tick={{ fontSize: 12 }}
                                />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: '#1e293b',
                                        border: '1px solid rgba(148, 163, 184, 0.2)',
                                        borderRadius: '8px',
                                        color: '#f8fafc'
                                    }}
                                />
                                <ReferenceLine y={50} stroke="#22c55e" strokeDasharray="5 5" label="Good" />
                                <ReferenceLine y={100} stroke="#eab308" strokeDasharray="5 5" label="Moderate" />
                                <ReferenceLine y={150} stroke="#f97316" strokeDasharray="5 5" label="Sensitive" />
                                <ReferenceLine y={200} stroke="#ef4444" strokeDasharray="5 5" label="Unhealthy" />
                                <Area
                                    type="monotone"
                                    dataKey="aqi"
                                    stroke="#3b82f6"
                                    strokeWidth={3}
                                    fill="url(#aqiGradient)"
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </section>
            )}
        </div>
    );
}

export default Prediction;
