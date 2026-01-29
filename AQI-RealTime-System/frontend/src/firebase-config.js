// Firebase configuration for AQI Dashboard
import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';
import { getDatabase } from 'firebase/database';

// Your web app's Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyCXkkReqSheWMuDgr5x5UOM_VgH0ExyLWI",
    authDomain: "aqi-forecasting-5dc8c.firebaseapp.com",
    databaseURL: "https://aqi-forecasting-5dc8c-default-rtdb.firebaseio.com",
    projectId: "aqi-forecasting-5dc8c",
    storageBucket: "aqi-forecasting-5dc8c.firebasestorage.app",
    messagingSenderId: "1036093859182",
    appId: "1:1036093859182:web:f1672c0cfb5afcb4428d7f",
    measurementId: "G-KZNH7BLPK0"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Auth
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();

// Database
export const database = getDatabase(app);

export default app;
