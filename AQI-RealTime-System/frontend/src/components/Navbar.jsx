import React from 'react';
import './Navbar.css';

function Navbar() {
    return (
        <nav className="navbar">
            <div className="container navbar-content">
                <div className="navbar-brand">
                    <div className="logo">🌍</div>
                    <div className="brand-text">
                        <h1>AQI Prediction</h1>
                        <span>Real-Time Air Quality Monitoring</span>
                    </div>
                </div>

                <div className="navbar-status">
                    <div className="status-badge online">
                        <span className="status-dot"></span>
                        Live
                    </div>
                    <div className="model-badge">
                        🧬 GA-KELM
                    </div>
                </div>
            </div>
        </nav>
    );
}

export default Navbar;
