import React, { useState } from 'react';
import { Search, MapPin, Plus, X } from 'lucide-react';
import './LocationSearch.css';

/**
 * Location Search & Select Component
 */
export default function LocationSearch({
    locations,
    selectedLocation,
    onSelect,
    onAddLocation,
    isLoading
}) {
    const [isAddingNew, setIsAddingNew] = useState(false);
    const [newLocation, setNewLocation] = useState({
        city: '',
        country: '',
        latitude: '',
        longitude: '',
    });
    const [error, setError] = useState('');

    const handleAddSubmit = async (e) => {
        e.preventDefault();
        setError('');

        // Validate
        if (!newLocation.city || !newLocation.latitude || !newLocation.longitude) {
            setError('City, latitude, and longitude are required');
            return;
        }

        const lat = parseFloat(newLocation.latitude);
        const lng = parseFloat(newLocation.longitude);

        if (isNaN(lat) || lat < -90 || lat > 90) {
            setError('Latitude must be between -90 and 90');
            return;
        }

        if (isNaN(lng) || lng < -180 || lng > 180) {
            setError('Longitude must be between -180 and 180');
            return;
        }

        try {
            await onAddLocation({
                city: newLocation.city,
                country: newLocation.country || null,
                latitude: lat,
                longitude: lng,
            });

            setNewLocation({ city: '', country: '', latitude: '', longitude: '' });
            setIsAddingNew(false);
        } catch (err) {
            setError(err.message || 'Failed to add location');
        }
    };

    return (
        <div className="location-search glass-card">
            <div className="location-header">
                <div className="location-title">
                    <MapPin size={20} />
                    <h3>Locations</h3>
                </div>
                <button
                    className="btn btn-ghost"
                    onClick={() => setIsAddingNew(!isAddingNew)}
                >
                    {isAddingNew ? <X size={18} /> : <Plus size={18} />}
                </button>
            </div>

            {/* Add New Location Form */}
            {isAddingNew && (
                <form className="add-location-form" onSubmit={handleAddSubmit}>
                    <div className="form-row">
                        <input
                            type="text"
                            placeholder="City *"
                            value={newLocation.city}
                            onChange={(e) => setNewLocation({ ...newLocation, city: e.target.value })}
                            className="form-input"
                        />
                        <input
                            type="text"
                            placeholder="Country"
                            value={newLocation.country}
                            onChange={(e) => setNewLocation({ ...newLocation, country: e.target.value })}
                            className="form-input"
                        />
                    </div>
                    <div className="form-row">
                        <input
                            type="number"
                            step="any"
                            placeholder="Latitude *"
                            value={newLocation.latitude}
                            onChange={(e) => setNewLocation({ ...newLocation, latitude: e.target.value })}
                            className="form-input"
                        />
                        <input
                            type="number"
                            step="any"
                            placeholder="Longitude *"
                            value={newLocation.longitude}
                            onChange={(e) => setNewLocation({ ...newLocation, longitude: e.target.value })}
                            className="form-input"
                        />
                    </div>
                    {error && <p className="form-error">{error}</p>}
                    <button type="submit" className="btn btn-primary">
                        Add Location
                    </button>
                </form>
            )}

            {/* Location List */}
            <div className="location-list">
                {isLoading ? (
                    <>
                        {[1, 2, 3].map(i => (
                            <div key={i} className="skeleton location-skeleton"></div>
                        ))}
                    </>
                ) : locations?.length > 0 ? (
                    locations.map(location => (
                        <button
                            key={location.id}
                            className={`location-item ${selectedLocation?.id === location.id ? 'active' : ''}`}
                            onClick={() => onSelect(location)}
                        >
                            <div className="location-info">
                                <span className="location-city">{location.city}</span>
                                {location.country && (
                                    <span className="location-country">{location.country}</span>
                                )}
                            </div>
                            <div className="location-coords">
                                {location.latitude.toFixed(2)}°, {location.longitude.toFixed(2)}°
                            </div>
                        </button>
                    ))
                ) : (
                    <div className="location-empty">
                        <MapPin size={32} />
                        <p>No locations added yet</p>
                        <button
                            className="btn btn-secondary"
                            onClick={() => setIsAddingNew(true)}
                        >
                            Add First Location
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
