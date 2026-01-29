import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw, AlertCircle } from 'lucide-react';
import Header from './components/Header';
import AQICard from './components/AQICard';
import PredictionChart from './components/PredictionChart';
import LocationSearch from './components/LocationSearch';
import StatsCard from './components/StatsCard';
import { useWebSocket } from './hooks/useWebSocket';
import { useAQIData } from './hooks/useAQIData';
import { locationApi, predictionsApi } from './services/api';
import './App.css';

/**
 * Main Application Component
 */
export default function App() {
    // Location state
    const [locations, setLocations] = useState([]);
    const [selectedLocation, setSelectedLocation] = useState(null);
    const [locationsLoading, setLocationsLoading] = useState(true);

    // Model info
    const [modelInfo, setModelInfo] = useState(null);

    // Error state
    const [error, setError] = useState(null);

    // WebSocket connection for real-time updates
    const {
        data: wsData,
        isConnected,
        error: wsError,
        refresh: wsRefresh
    } = useWebSocket(selectedLocation?.id);

    // REST API data fetch
    const {
        current,
        history,
        predictions,
        stats,
        isLoading: dataLoading,
        refresh: refreshData
    } = useAQIData(selectedLocation?.id, {
        autoRefresh: !isConnected, // Only auto-refresh if WebSocket is not connected
        refreshInterval: 60000,
        fetchHistory: true,
        fetchPredictions: true,
    });

    // Load locations on mount
    useEffect(() => {
        loadLocations();
        loadModelInfo();
    }, []);

    const loadLocations = async () => {
        try {
            setLocationsLoading(true);
            const response = await locationApi.list();
            setLocations(response.locations || []);

            // Auto-select first location
            if (response.locations?.length > 0 && !selectedLocation) {
                setSelectedLocation(response.locations[0]);
            }
        } catch (err) {
            console.error('Failed to load locations:', err);
            setError('Failed to load locations');
        } finally {
            setLocationsLoading(false);
        }
    };

    const loadModelInfo = async () => {
        try {
            const info = await predictionsApi.getModelInfo();
            setModelInfo(info);
        } catch (err) {
            console.log('No trained model found');
        }
    };

    const handleAddLocation = async (locationData) => {
        try {
            const newLocation = await locationApi.create(locationData);
            setLocations(prev => [...prev, newLocation]);
            setSelectedLocation(newLocation);
        } catch (err) {
            throw err;
        }
    };

    const handleRefresh = useCallback(async () => {
        if (isConnected) {
            wsRefresh();
        } else {
            await refreshData();
        }
    }, [isConnected, wsRefresh, refreshData]);

    // Use WebSocket data if available, otherwise use REST data
    const displayData = wsData?.current || current;
    const displayHistory = history;
    const displayPredictions = wsData?.predictions || predictions;
    const displayStats = stats;

    // Connection status
    const connectionStatus = isConnected ? 'connected' : wsError ? 'error' : 'connecting';

    return (
        <div className="app">
            <Header
                connectionStatus={connectionStatus}
                modelInfo={modelInfo}
            />

            <main className="main-content container">
                {/* Error Banner */}
                {error && (
                    <div className="error-banner">
                        <AlertCircle size={20} />
                        <span>{error}</span>
                        <button onClick={() => setError(null)}>Dismiss</button>
                    </div>
                )}

                <div className="dashboard-grid">
                    {/* Left Sidebar - Locations */}
                    <aside className="sidebar">
                        <LocationSearch
                            locations={locations}
                            selectedLocation={selectedLocation}
                            onSelect={setSelectedLocation}
                            onAddLocation={handleAddLocation}
                            isLoading={locationsLoading}
                        />

                        <StatsCard
                            stats={displayStats}
                            isLoading={dataLoading && !displayStats}
                        />
                    </aside>

                    {/* Main Content */}
                    <section className="main-section">
                        {/* Action Bar */}
                        <div className="action-bar">
                            <h2>
                                {selectedLocation
                                    ? `Air Quality in ${selectedLocation.city}`
                                    : 'Select a Location'}
                            </h2>
                            <button
                                className="btn btn-secondary"
                                onClick={handleRefresh}
                                disabled={!selectedLocation}
                            >
                                <RefreshCw size={16} className={dataLoading ? 'animate-spin' : ''} />
                                Refresh
                            </button>
                        </div>

                        {/* AQI Card */}
                        <AQICard
                            data={displayData}
                            isLoading={dataLoading && !displayData}
                            isLive={isConnected}
                        />

                        {/* Prediction Chart */}
                        <PredictionChart
                            history={displayHistory}
                            predictions={displayPredictions}
                            isLoading={dataLoading && !displayHistory?.length}
                        />
                    </section>
                </div>
            </main>

            {/* Footer */}
            <footer className="app-footer">
                <div className="container">
                    <p>
                        Real-Time AQI Prediction System • Powered by <strong>GA-KELM</strong> Machine Learning
                    </p>
                </div>
            </footer>
        </div>
    );
}
