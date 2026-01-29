import React, { useMemo } from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Area,
    ComposedChart,
    ReferenceLine,
} from 'recharts';
import { TrendingUp, Brain } from 'lucide-react';
import './PredictionChart.css';

/**
 * Get color for AQI value
 */
function getAQIColor(value) {
    if (value <= 50) return '#22c55e';
    if (value <= 100) return '#eab308';
    if (value <= 150) return '#f97316';
    if (value <= 200) return '#ef4444';
    if (value <= 300) return '#a855f7';
    return '#7c2d12';
}

/**
 * Custom tooltip component
 */
function CustomTooltip({ active, payload, label }) {
    if (!active || !payload?.length) return null;

    const data = payload[0].payload;
    const isPrediction = data.isPrediction;

    return (
        <div className="chart-tooltip">
            <p className="tooltip-time">{label}</p>
            <p className="tooltip-value" style={{ color: getAQIColor(data.aqi) }}>
                AQI: {Math.round(data.aqi)}
                {isPrediction && (
                    <span className="tooltip-badge">Predicted</span>
                )}
            </p>
            {data.confidence && (
                <p className="tooltip-confidence">
                    Confidence: {(data.confidence * 100).toFixed(0)}%
                </p>
            )}
        </div>
    );
}

/**
 * Prediction Chart Component
 * Displays historical AQI and future predictions
 */
export default function PredictionChart({ history, predictions, isLoading }) {
    // Combine and format data
    const chartData = useMemo(() => {
        const data = [];

        // Add historical data
        if (history?.length) {
            const sortedHistory = [...history].sort(
                (a, b) => new Date(a.recorded_at) - new Date(b.recorded_at)
            );

            sortedHistory.forEach(reading => {
                const time = new Date(reading.recorded_at);
                data.push({
                    time: time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                    timestamp: time.getTime(),
                    aqi: reading.aqi_value,
                    isPrediction: false,
                });
            });
        }

        // Add predictions
        if (predictions?.length) {
            predictions.forEach(pred => {
                const time = new Date(pred.prediction_for);
                data.push({
                    time: time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                    timestamp: time.getTime(),
                    aqi: pred.predicted_aqi,
                    confidence: pred.confidence,
                    isPrediction: true,
                });
            });
        }

        // Sort by timestamp
        data.sort((a, b) => a.timestamp - b.timestamp);

        return data;
    }, [history, predictions]);

    // Find where predictions start
    const predictionStartIndex = chartData.findIndex(d => d.isPrediction);

    if (isLoading) {
        return (
            <div className="chart-container glass-card">
                <div className="chart-header">
                    <div className="skeleton" style={{ width: '200px', height: '24px' }}></div>
                </div>
                <div className="skeleton" style={{ width: '100%', height: '300px' }}></div>
            </div>
        );
    }

    if (!chartData.length) {
        return (
            <div className="chart-container glass-card">
                <div className="chart-empty">
                    <TrendingUp size={48} />
                    <p>No data available for chart</p>
                </div>
            </div>
        );
    }

    return (
        <div className="chart-container glass-card">
            <div className="chart-header">
                <div className="chart-title">
                    <TrendingUp size={20} />
                    <h3>AQI Trend & Predictions</h3>
                </div>
                <div className="chart-legend">
                    <div className="legend-item">
                        <span className="legend-dot" style={{ background: '#3b82f6' }}></span>
                        Historical
                    </div>
                    <div className="legend-item">
                        <span className="legend-dot legend-dot-dashed" style={{ background: '#8b5cf6' }}></span>
                        GA-KELM Predictions
                    </div>
                </div>
            </div>

            <div className="chart-wrapper">
                <ResponsiveContainer width="100%" height={350}>
                    <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 20 }}>
                        <defs>
                            <linearGradient id="colorAqi" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                            </linearGradient>
                            <linearGradient id="colorPrediction" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                            </linearGradient>
                        </defs>

                        <CartesianGrid
                            strokeDasharray="3 3"
                            stroke="rgba(148, 163, 184, 0.1)"
                            vertical={false}
                        />

                        <XAxis
                            dataKey="time"
                            stroke="#64748b"
                            fontSize={12}
                            tickLine={false}
                            axisLine={{ stroke: 'rgba(148, 163, 184, 0.2)' }}
                        />

                        <YAxis
                            stroke="#64748b"
                            fontSize={12}
                            tickLine={false}
                            axisLine={false}
                            domain={[0, 'auto']}
                        />

                        <Tooltip content={<CustomTooltip />} />

                        {/* AQI threshold lines */}
                        <ReferenceLine y={50} stroke="#22c55e" strokeDasharray="3 3" strokeOpacity={0.5} />
                        <ReferenceLine y={100} stroke="#eab308" strokeDasharray="3 3" strokeOpacity={0.5} />
                        <ReferenceLine y={150} stroke="#f97316" strokeDasharray="3 3" strokeOpacity={0.5} />
                        <ReferenceLine y={200} stroke="#ef4444" strokeDasharray="3 3" strokeOpacity={0.5} />

                        {/* Historical area */}
                        <Area
                            type="monotone"
                            dataKey="aqi"
                            stroke="transparent"
                            fillOpacity={1}
                            fill="url(#colorAqi)"
                            connectNulls={false}
                            isAnimationActive={true}
                        />

                        {/* Historical line */}
                        <Line
                            type="monotone"
                            dataKey="aqi"
                            stroke="#3b82f6"
                            strokeWidth={2}
                            dot={false}
                            activeDot={{ r: 6, fill: '#3b82f6', stroke: '#1e293b', strokeWidth: 2 }}
                            connectNulls={false}
                            isAnimationActive={true}
                        />
                    </ComposedChart>
                </ResponsiveContainer>
            </div>

            {predictions?.length > 0 && (
                <div className="chart-footer">
                    <div className="prediction-badge">
                        <Brain size={16} />
                        <span>Predictions powered by GA-KELM (Genetic Algorithm - Kernel ELM)</span>
                    </div>
                </div>
            )}
        </div>
    );
}
