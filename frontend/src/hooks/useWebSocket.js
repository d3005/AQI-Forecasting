import { useState, useEffect, useRef, useCallback } from 'react';
import { AQIWebSocket } from '../services/api';

/**
 * Custom hook for WebSocket connection to AQI updates
 * 
 * @param {number} locationId - Location ID to subscribe to
 * @returns {Object} - WebSocket state and data
 */
export function useWebSocket(locationId) {
    const [data, setData] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    const [error, setError] = useState(null);
    const wsRef = useRef(null);

    const connect = useCallback(() => {
        if (!locationId) return;

        // Disconnect existing connection
        if (wsRef.current) {
            wsRef.current.disconnect();
        }

        // Create new connection
        wsRef.current = new AQIWebSocket(locationId, {
            onConnect: () => {
                setIsConnected(true);
                setError(null);
            },
            onDisconnect: () => {
                setIsConnected(false);
            },
            onUpdate: (updateData) => {
                setData(updateData);
            },
            onError: (err) => {
                setError(err);
                setIsConnected(false);
            },
        });

        wsRef.current.connect();
    }, [locationId]);

    const disconnect = useCallback(() => {
        if (wsRef.current) {
            wsRef.current.disconnect();
            wsRef.current = null;
        }
    }, []);

    const refresh = useCallback(() => {
        if (wsRef.current) {
            wsRef.current.requestRefresh();
        }
    }, []);

    useEffect(() => {
        connect();
        return () => disconnect();
    }, [connect, disconnect]);

    return {
        data,
        isConnected,
        error,
        refresh,
        reconnect: connect,
    };
}

export default useWebSocket;
