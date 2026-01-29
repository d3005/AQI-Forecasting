/**
 * API Service for AQI Prediction System
 * Handles all HTTP and WebSocket communications
 */

const API_BASE = import.meta.env.VITE_API_URL || '';
const WS_BASE = import.meta.env.VITE_WS_URL || `ws://${window.location.host}`;

/**
 * Make an API request
 */
async function request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;

    const config = {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
        ...options,
    };

    try {
        const response = await fetch(url, config);

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `HTTP error ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`API Error [${endpoint}]:`, error);
        throw error;
    }
}

/**
 * Location API
 */
export const locationApi = {
    list: () => request('/api/v1/locations'),

    get: (id) => request(`/api/v1/locations/${id}`),

    create: (data) => request('/api/v1/locations', {
        method: 'POST',
        body: JSON.stringify(data),
    }),

    delete: (id) => request(`/api/v1/locations/${id}`, {
        method: 'DELETE',
    }),
};

/**
 * AQI API
 */
export const aqiApi = {
    getCurrent: (locationId) => request(`/api/v1/aqi/current/${locationId}`),

    getHistory: (locationId, hours = 24) =>
        request(`/api/v1/aqi/history/${locationId}?hours=${hours}`),

    fetchFresh: (locationId) => request(`/api/v1/aqi/fetch/${locationId}`),

    getStats: (locationId, hours = 24) =>
        request(`/api/v1/aqi/stats/${locationId}?hours=${hours}`),
};

/**
 * Predictions API
 */
export const predictionsApi = {
    get: (locationId, hoursAhead = 24) =>
        request(`/api/v1/predictions/${locationId}?hours_ahead=${hoursAhead}`),

    generate: (locationId, hoursAhead = 24) =>
        request(`/api/v1/predictions/generate/${locationId}?hours_ahead=${hoursAhead}`, {
            method: 'POST',
        }),

    train: (populationSize = 30, generations = 50) =>
        request(`/api/v1/predictions/train?population_size=${populationSize}&generations=${generations}`, {
            method: 'POST',
        }),

    getModelInfo: () => request('/api/v1/predictions/model/info'),

    getAccuracy: (locationId, hours = 24) =>
        request(`/api/v1/predictions/accuracy/${locationId}?hours=${hours}`),
};

/**
 * Status API
 */
export const statusApi = {
    health: () => request('/health'),
    status: () => request('/api/v1/status'),
};

/**
 * WebSocket connection class
 */
export class AQIWebSocket {
    constructor(locationId, callbacks = {}) {
        this.locationId = locationId;
        this.callbacks = callbacks;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
    }

    connect() {
        const url = `${WS_BASE}/ws/aqi/${this.locationId}`;

        try {
            this.ws = new WebSocket(url);

            this.ws.onopen = () => {
                console.log(`WebSocket connected for location ${this.locationId}`);
                this.reconnectAttempts = 0;
                this.callbacks.onConnect?.();
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);

                    switch (data.type) {
                        case 'update':
                            this.callbacks.onUpdate?.(data);
                            break;
                        case 'ping':
                            this.send({ type: 'pong' });
                            break;
                        case 'pong':
                            // Keep-alive response
                            break;
                        case 'error':
                            this.callbacks.onError?.(new Error(data.message));
                            break;
                        default:
                            console.log('Unknown message type:', data.type);
                    }
                } catch (error) {
                    console.error('WebSocket message parse error:', error);
                }
            };

            this.ws.onclose = (event) => {
                console.log(`WebSocket closed for location ${this.locationId}`, event.code);
                this.callbacks.onDisconnect?.();

                // Attempt reconnection
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    const delay = this.reconnectDelay * this.reconnectAttempts;
                    console.log(`Reconnecting in ${delay}ms...`);
                    setTimeout(() => this.connect(), delay);
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.callbacks.onError?.(error);
            };

        } catch (error) {
            console.error('WebSocket connection failed:', error);
            this.callbacks.onError?.(error);
        }
    }

    send(data) {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }

    requestRefresh() {
        this.send({ type: 'refresh' });
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    get isConnected() {
        return this.ws?.readyState === WebSocket.OPEN;
    }
}

export default {
    location: locationApi,
    aqi: aqiApi,
    predictions: predictionsApi,
    status: statusApi,
    AQIWebSocket,
};
