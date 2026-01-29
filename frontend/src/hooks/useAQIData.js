import { useState, useEffect, useCallback } from 'react';
import { aqiApi, predictionsApi } from '../services/api';

/**
 * Custom hook for fetching AQI data
 * 
 * @param {number} locationId - Location ID
 * @param {Object} options - Hook options
 * @returns {Object} - AQI data and state
 */
export function useAQIData(locationId, options = {}) {
    const {
        autoRefresh = false,
        refreshInterval = 60000,
        fetchHistory = true,
        historyHours = 24,
        fetchPredictions = true,
        predictionHours = 24,
    } = options;

    const [current, setCurrent] = useState(null);
    const [history, setHistory] = useState([]);
    const [predictions, setPredictions] = useState([]);
    const [stats, setStats] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchData = useCallback(async () => {
        if (!locationId) return;

        setIsLoading(true);
        setError(null);

        try {
            // Fetch all data in parallel
            const promises = [
                aqiApi.getCurrent(locationId),
                aqiApi.getStats(locationId, historyHours),
            ];

            if (fetchHistory) {
                promises.push(aqiApi.getHistory(locationId, historyHours));
            }

            if (fetchPredictions) {
                promises.push(predictionsApi.get(locationId, predictionHours));
            }

            const results = await Promise.allSettled(promises);

            // Process results
            if (results[0].status === 'fulfilled') {
                setCurrent(results[0].value);
            }

            if (results[1].status === 'fulfilled') {
                setStats(results[1].value);
            }

            if (fetchHistory && results[2]?.status === 'fulfilled') {
                setHistory(results[2].value.readings || []);
            }

            if (fetchPredictions) {
                const predIndex = fetchHistory ? 3 : 2;
                if (results[predIndex]?.status === 'fulfilled') {
                    setPredictions(results[predIndex].value.predictions || []);
                }
            }

            // Check for any errors
            const errors = results.filter(r => r.status === 'rejected');
            if (errors.length > 0) {
                console.warn('Some API calls failed:', errors);
            }

        } catch (err) {
            console.error('Error fetching AQI data:', err);
            setError(err);
        } finally {
            setIsLoading(false);
        }
    }, [locationId, fetchHistory, historyHours, fetchPredictions, predictionHours]);

    const refreshCurrent = useCallback(async () => {
        if (!locationId) return;

        try {
            const freshData = await aqiApi.fetchFresh(locationId);
            setCurrent(freshData);
            return freshData;
        } catch (err) {
            console.error('Error refreshing AQI:', err);
            throw err;
        }
    }, [locationId]);

    // Initial fetch
    useEffect(() => {
        fetchData();
    }, [fetchData]);

    // Auto refresh
    useEffect(() => {
        if (!autoRefresh || !locationId) return;

        const interval = setInterval(fetchData, refreshInterval);
        return () => clearInterval(interval);
    }, [autoRefresh, refreshInterval, locationId, fetchData]);

    return {
        current,
        history,
        predictions,
        stats,
        isLoading,
        error,
        refresh: fetchData,
        refreshCurrent,
    };
}

export default useAQIData;
