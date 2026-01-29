import React from 'react';
import { Wind, Activity, Cpu } from 'lucide-react';
import './Header.css';

/**
 * Application Header Component
 */
export default function Header({ connectionStatus, modelInfo }) {
    const getStatusClass = () => {
        switch (connectionStatus) {
            case 'connected': return 'status-online';
            case 'connecting': return 'status-connecting';
            default: return 'status-offline';
        }
    };

    const getStatusLabel = () => {
        switch (connectionStatus) {
            case 'connected': return 'Live';
            case 'connecting': return 'Connecting...';
            default: return 'Offline';
        }
    };

    return (
        <header className="app-header">
            <div className="container">
                <div className="header-content">
                    {/* Logo & Title */}
                    <div className="header-brand">
                        <div className="header-logo">
                            <Wind size={28} />
                        </div>
                        <div className="header-title">
                            <h1>AQI Prediction</h1>
                            <span className="header-subtitle">Real-Time Air Quality Monitoring</span>
                        </div>
                    </div>

                    {/* Status Indicators */}
                    <div className="header-status">
                        {/* Connection Status */}
                        <div className="status-item">
                            <Activity size={16} />
                            <span className={`status-dot ${getStatusClass()}`}></span>
                            <span className="status-label">{getStatusLabel()}</span>
                        </div>

                        {/* Model Status */}
                        {modelInfo && (
                            <div className="status-item model-status">
                                <Cpu size={16} />
                                <span className="status-label">
                                    GA-KELM {modelInfo.model_version}
                                </span>
                                <span className="model-accuracy">
                                    RMSE: {modelInfo.val_rmse?.toFixed(2)}
                                </span>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
}
