import React, { useState, useEffect, createContext, useContext } from 'react';
import { Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import './App.css';

// Auth
import { AuthProvider, useAuth } from './contexts/AuthContext';

// Pages
import HomePage from './pages/HomePage';
import CurrentAQI from './pages/CurrentAQI';
import Prediction from './pages/Prediction';
import LoginPage from './pages/LoginPage';
import AdminPage from './pages/AdminPage';

// Components
import AlertSettings from './components/AlertSettings';

// Create Location Context
export const LocationContext = createContext();

export const useLocationData = () => useContext(LocationContext);

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
    const { user, loading } = useAuth();

    if (loading) {
        return (
            <div className="loading-screen">
                <div className="loader"></div>
                <p>Loading...</p>
            </div>
        );
    }

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    return children;
};

// Main App Content (needs auth context)
function AppContent() {
    const { user, logout, isAdmin } = useAuth();
    const [userLocation, setUserLocation] = useState(null);
    const [locationName, setLocationName] = useState('Detecting location...');
    const [locationError, setLocationError] = useState(null);
    const [isLoadingLocation, setIsLoadingLocation] = useState(true);
    const [showUserMenu, setShowUserMenu] = useState(false);
    const [showAlertSettings, setShowAlertSettings] = useState(false);
    const location = useLocation();

    // Request user's location on mount or when user logs in
    useEffect(() => {
        if (user && !userLocation) {
            requestLocation();
        }
    }, [user]); // eslint-disable-line react-hooks/exhaustive-deps

    const requestLocation = () => {
        setIsLoadingLocation(true);
        setLocationError(null);
        setLocationName('Detecting location...');

        if (!navigator.geolocation) {
            setLocationError('Geolocation is not supported by your browser');
            setIsLoadingLocation(false);
            setUserLocation({ lat: 15.5057, lon: 80.0499 });
            setLocationName('Ongole (Default)');
            return;
        }

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const { latitude, longitude } = position.coords;
                console.log('Location detected:', latitude, longitude);
                setUserLocation({ lat: latitude, lon: longitude });

                try {
                    const response = await fetch(
                        `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${latitude}&longitude=${longitude}&localityLanguage=en`
                    );
                    const data = await response.json();
                    const city = data.city || data.locality || data.principalSubdivision || 'Your Location';
                    console.log('City detected:', city);
                    setLocationName(city);
                } catch (err) {
                    console.error('Geocoding error:', err);
                    setLocationName('Your Location');
                }

                setIsLoadingLocation(false);
            },
            (error) => {
                console.error('Location error:', error.message);
                setLocationError('Location access denied. Using default location.');
                setUserLocation({ lat: 15.5057, lon: 80.0499 });
                setLocationName('Ongole (Default)');
                setIsLoadingLocation(false);
            },
            {
                enableHighAccuracy: true,
                timeout: 15000,
                maximumAge: 0 // Don't use cached position
            }
        );
    };

    const handleLogout = async () => {
        await logout();
        setShowUserMenu(false);
    };

    const contextValue = {
        userLocation,
        locationName,
        locationError,
        isLoadingLocation,
        requestLocation,
        API_URL
    };

    // Show login page for unauthenticated users
    if (location.pathname === '/login') {
        return (
            <Routes>
                <Route path="/login" element={<LoginPage />} />
            </Routes>
        );
    }

    return (
        <LocationContext.Provider value={contextValue}>
            <div className="app">
                {/* Navigation */}
                <nav className="navbar">
                    <div className="nav-container">
                        <Link to="/" className="nav-brand">
                            <span className="brand-icon">🌍</span>
                            <span className="brand-text">AQI Forecast</span>
                        </Link>

                        <div className="nav-links">
                            <Link
                                to="/"
                                className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
                            >
                                Home
                            </Link>
                            <Link
                                to="/current"
                                className={`nav-link ${location.pathname === '/current' ? 'active' : ''}`}
                            >
                                Current AQI
                            </Link>
                            <Link
                                to="/prediction"
                                className={`nav-link ${location.pathname === '/prediction' ? 'active' : ''}`}
                            >
                                Prediction
                            </Link>
                            {isAdmin && (
                                <Link
                                    to="/admin"
                                    className={`nav-link admin-link ${location.pathname === '/admin' ? 'active' : ''}`}
                                >
                                    Admin
                                </Link>
                            )}
                        </div>

                        {/* User Profile */}
                        {user && (
                            <div className="user-profile" onClick={() => setShowUserMenu(!showUserMenu)}>
                                {user.photoURL ? (
                                    <img src={user.photoURL} alt="" className="user-avatar" />
                                ) : (
                                    <div className="user-avatar-placeholder">
                                        {user.displayName?.[0] || user.email?.[0] || 'U'}
                                    </div>
                                )}
                                <span className="user-name">{user.displayName?.split(' ')[0] || 'User'}</span>

                                {showUserMenu && (
                                    <div className="user-menu">
                                        <div className="menu-header">
                                            <span className="menu-email">{user.email}</span>
                                        </div>
                                        <button className="menu-item" onClick={() => { setShowAlertSettings(true); setShowUserMenu(false); }}>
                                            🔔 Alert Settings
                                        </button>
                                        {isAdmin && (
                                            <Link to="/admin" className="menu-item" onClick={() => setShowUserMenu(false)}>
                                                Admin Panel
                                            </Link>
                                        )}
                                        <button className="menu-item logout" onClick={handleLogout}>
                                            Logout
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </nav>

                {/* Alert Settings Modal */}
                {showAlertSettings && (
                    <AlertSettings onClose={() => setShowAlertSettings(false)} />
                )}

                {/* Location Error Banner */}
                {locationError && (
                    <div className="location-error">
                        ⚠️ {locationError}
                        <button onClick={requestLocation}>Try Again</button>
                    </div>
                )}

                {/* Page Routes */}
                <main className="main-content-app">
                    <Routes>
                        <Route path="/" element={
                            <ProtectedRoute><HomePage /></ProtectedRoute>
                        } />
                        <Route path="/current" element={
                            <ProtectedRoute><CurrentAQI /></ProtectedRoute>
                        } />
                        <Route path="/prediction" element={
                            <ProtectedRoute><Prediction /></ProtectedRoute>
                        } />
                        <Route path="/admin" element={
                            <ProtectedRoute><AdminPage /></ProtectedRoute>
                        } />
                        <Route path="/login" element={<LoginPage />} />
                        <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>
                </main>

                {/* Footer */}
                {location.pathname !== '/' && location.pathname !== '/login' && (
                    <footer className="footer">
                        <p>Powered by <strong>GA-KELM</strong> Machine Learning | Real-Time AQI Prediction System</p>
                    </footer>
                )}
            </div>
        </LocationContext.Provider>
    );
}

// Main App with Auth Provider
function App() {
    return (
        <AuthProvider>
            <AppContent />
        </AuthProvider>
    );
}

export default App;
