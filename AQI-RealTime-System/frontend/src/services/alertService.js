// Email Alert Service using EmailJS
import emailjs from '@emailjs/browser';

// EmailJS Configuration
const EMAILJS_SERVICE_ID = 'service_yfmjx33';
const EMAILJS_TEMPLATE_ID = 'template_jme47e2';
const EMAILJS_PUBLIC_KEY = '-2IqAe8bnT8xi5PGN';

// Alert cooldown (prevent spam) - 1 hour
const ALERT_COOLDOWN_MS = 60 * 60 * 1000;

// Get last alert time from localStorage
const getLastAlertTime = (location) => {
    const key = `lastAlert_${location}`;
    const stored = localStorage.getItem(key);
    return stored ? parseInt(stored, 10) : 0;
};

// Set last alert time
const setLastAlertTime = (location) => {
    const key = `lastAlert_${location}`;
    localStorage.setItem(key, Date.now().toString());
};

// Check if alert can be sent (cooldown passed)
const canSendAlert = (location) => {
    const lastTime = getLastAlertTime(location);
    return Date.now() - lastTime > ALERT_COOLDOWN_MS;
};

// Get user's alert preferences from localStorage
export const getAlertPreferences = () => {
    const stored = localStorage.getItem('alertPreferences');
    if (stored) {
        return JSON.parse(stored);
    }
    return {
        enabled: false,
        threshold: 150, // Default: Unhealthy
    };
};

// Save alert preferences
export const saveAlertPreferences = (prefs) => {
    localStorage.setItem('alertPreferences', JSON.stringify(prefs));
};

// Get AQI category
const getAQICategory = (aqi) => {
    if (aqi <= 50) return 'Good';
    if (aqi <= 100) return 'Moderate';
    if (aqi <= 150) return 'Unhealthy for Sensitive Groups';
    if (aqi <= 200) return 'Unhealthy';
    if (aqi <= 300) return 'Very Unhealthy';
    return 'Hazardous';
};

// Get health recommendations
const getHealthRecommendations = (aqi) => {
    if (aqi <= 100) return 'Air quality is acceptable. Enjoy outdoor activities.';
    if (aqi <= 150) return 'Sensitive individuals should reduce prolonged outdoor exertion.';
    if (aqi <= 200) return 'Everyone may experience health effects. Limit outdoor activity.';
    if (aqi <= 300) return 'Health alert! Everyone may experience serious effects. Avoid outdoor activity.';
    return 'Emergency! Serious health effects for everyone. Stay indoors!';
};

// Send email alert
export const sendAQIAlert = async (userEmail, userName, aqi, location) => {
    // Check if alerts are enabled
    const prefs = getAlertPreferences();
    if (!prefs.enabled) {
        console.log('[Alert] Alerts are disabled');
        return { success: false, reason: 'disabled' };
    }

    // Check if AQI exceeds threshold
    if (aqi < prefs.threshold) {
        console.log(`[Alert] AQI ${aqi} is below threshold ${prefs.threshold}`);
        return { success: false, reason: 'below_threshold' };
    }

    // Check cooldown
    if (!canSendAlert(location)) {
        console.log('[Alert] Cooldown active, skipping alert');
        return { success: false, reason: 'cooldown' };
    }

    // Prepare email parameters
    const templateParams = {
        email: userEmail,
        user_name: userName || 'User',
        aqi: String(aqi),
        location: location,
        category: getAQICategory(aqi),
        recommendations: getHealthRecommendations(aqi),
        threshold: String(prefs.threshold),
        dashboard_url: window.location.origin,
    };

    try {
        console.log('[Alert] Sending email alert to:', userEmail);
        console.log('[Alert] Template params:', templateParams);

        const response = await emailjs.send(
            EMAILJS_SERVICE_ID,
            EMAILJS_TEMPLATE_ID,
            templateParams,
            EMAILJS_PUBLIC_KEY
        );

        console.log('[Alert] Email sent successfully:', response);
        setLastAlertTime(location);

        return { success: true, response };
    } catch (error) {
        console.error('[Alert] Failed to send email:', error);
        return { success: false, error: error?.text || error?.message || 'Unknown error' };
    }
};

// Send test alert (ignores cooldown)
export const sendTestAlert = async (userEmail, userName) => {
    const templateParams = {
        email: userEmail,
        to_email: userEmail,
        to_name: userName || 'User',
        user_name: userName || 'User',
        aqi: '175',
        location: 'Test Location',
        category: 'Unhealthy',
        recommendations: 'This is a test alert. Your alert system is working correctly!',
        threshold: '150',
        dashboard_url: window.location.origin,
        reply_to: userEmail,
    };

    try {
        console.log('[Alert] Sending test email to:', userEmail);
        console.log('[Alert] Template params:', templateParams);

        const response = await emailjs.send(
            EMAILJS_SERVICE_ID,
            EMAILJS_TEMPLATE_ID,
            templateParams,
            EMAILJS_PUBLIC_KEY
        );

        console.log('[Alert] Test email sent:', response);
        return { success: true, response };
    } catch (error) {
        console.error('[Alert] Test email failed:', error);
        // Get more detailed error message
        const errorMessage = error?.text || error?.message || JSON.stringify(error) || 'Unknown error';
        return { success: false, error: errorMessage };
    }
};

export default {
    sendAQIAlert,
    sendTestAlert,
    getAlertPreferences,
    saveAlertPreferences,
};
