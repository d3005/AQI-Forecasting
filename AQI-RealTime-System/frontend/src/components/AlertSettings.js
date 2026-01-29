import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getAlertPreferences, saveAlertPreferences, sendTestAlert } from '../services/alertService';
import './AlertSettings.css';

function AlertSettings({ onClose }) {
    const { user } = useAuth();
    const [preferences, setPreferences] = useState({
        enabled: false,
        threshold: 150,
    });
    const [testStatus, setTestStatus] = useState(null);
    const [sending, setSending] = useState(false);

    useEffect(() => {
        const prefs = getAlertPreferences();
        setPreferences(prefs);
    }, []);

    const handleToggle = () => {
        const newPrefs = { ...preferences, enabled: !preferences.enabled };
        setPreferences(newPrefs);
        saveAlertPreferences(newPrefs);
    };

    const handleThresholdChange = (value) => {
        const newPrefs = { ...preferences, threshold: parseInt(value, 10) };
        setPreferences(newPrefs);
        saveAlertPreferences(newPrefs);
    };

    const handleTestAlert = async () => {
        if (!user?.email) {
            setTestStatus({ success: false, message: 'No email found. Please login with Google.' });
            return;
        }

        setSending(true);
        setTestStatus(null);

        const result = await sendTestAlert(user.email, user.displayName);

        if (result.success) {
            setTestStatus({ success: true, message: 'Test email sent! Check your inbox.' });
        } else {
            setTestStatus({ success: false, message: `Failed: ${result.error}` });
        }

        setSending(false);
    };

    const thresholdOptions = [
        { value: 50, label: 'Good (50+)', color: '#00e400' },
        { value: 100, label: 'Moderate (100+)', color: '#ffff00' },
        { value: 150, label: 'Unhealthy for Sensitive (150+)', color: '#ff7e00' },
        { value: 200, label: 'Unhealthy (200+)', color: '#ff0000' },
        { value: 300, label: 'Very Unhealthy (300+)', color: '#8f3f97' },
    ];

    return (
        <div className="alert-settings-overlay" onClick={onClose}>
            <div className="alert-settings-modal" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>Alert Settings</h2>
                    <button className="close-btn" onClick={onClose}>×</button>
                </div>

                <div className="modal-content">
                    <div className="setting-row">
                        <div className="setting-info">
                            <h3>Email Alerts</h3>
                            <p>Get notified when AQI exceeds your threshold</p>
                        </div>
                        <label className="toggle-switch">
                            <input
                                type="checkbox"
                                checked={preferences.enabled}
                                onChange={handleToggle}
                            />
                            <span className="slider"></span>
                        </label>
                    </div>

                    <div className="setting-row">
                        <div className="setting-info">
                            <h3>Alert Email</h3>
                            <p>{user?.email || 'Not logged in'}</p>
                        </div>
                    </div>

                    <div className="setting-section">
                        <h3>Alert Threshold</h3>
                        <p className="setting-desc">Send alert when AQI exceeds:</p>
                        <div className="threshold-options">
                            {thresholdOptions.map((opt) => (
                                <label
                                    key={opt.value}
                                    className={`threshold-option ${preferences.threshold === opt.value ? 'selected' : ''}`}
                                    style={{ borderColor: preferences.threshold === opt.value ? opt.color : 'transparent' }}
                                >
                                    <input
                                        type="radio"
                                        name="threshold"
                                        value={opt.value}
                                        checked={preferences.threshold === opt.value}
                                        onChange={(e) => handleThresholdChange(e.target.value)}
                                    />
                                    <span className="dot" style={{ background: opt.color }}></span>
                                    <span className="label">{opt.label}</span>
                                </label>
                            ))}
                        </div>
                    </div>

                    <div className="test-section">
                        <button
                            className="test-btn"
                            onClick={handleTestAlert}
                            disabled={sending || !preferences.enabled}
                        >
                            {sending ? 'Sending...' : 'Send Test Alert'}
                        </button>
                        {testStatus && (
                            <p className={`test-status ${testStatus.success ? 'success' : 'error'}`}>
                                {testStatus.message}
                            </p>
                        )}
                    </div>
                </div>

                <div className="modal-footer">
                    <p>Alerts sent max once per hour per location</p>
                </div>
            </div>
        </div>
    );
}

export default AlertSettings;
