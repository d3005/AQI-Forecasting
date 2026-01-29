import React, { createContext, useContext, useState, useEffect } from 'react';
import {
    signInWithPopup,
    signOut,
    onAuthStateChanged
} from 'firebase/auth';
import { ref, set, get, child } from 'firebase/database';
import { auth, googleProvider, database } from '../firebase-config';

// Admin emails - users with these emails can access admin panel
const ADMIN_EMAILS = [
    'dannyjoseph3007@gmail.com',
];

const AuthContext = createContext();

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    // Listen to auth state changes
    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
            if (firebaseUser) {
                const userData = {
                    uid: firebaseUser.uid,
                    email: firebaseUser.email,
                    displayName: firebaseUser.displayName,
                    photoURL: firebaseUser.photoURL,
                    isAdmin: ADMIN_EMAILS.includes(firebaseUser.email),
                    lastLogin: new Date().toISOString()
                };

                // Save user to database
                await saveUserToDatabase(userData);
                setUser(userData);
            } else {
                setUser(null);
            }
            setLoading(false);
        });

        return () => unsubscribe();
    }, []);

    // Save user to Firebase Database
    const saveUserToDatabase = async (userData) => {
        try {
            const userRef = ref(database, `users/${userData.uid}`);
            await set(userRef, {
                email: userData.email,
                displayName: userData.displayName,
                photoURL: userData.photoURL,
                lastLogin: userData.lastLogin,
                createdAt: userData.createdAt || new Date().toISOString()
            });
        } catch (error) {
            console.error('Error saving user:', error);
        }
    };

    // Google Sign In
    const loginWithGoogle = async () => {
        try {
            const result = await signInWithPopup(auth, googleProvider);
            return { success: true, user: result.user };
        } catch (error) {
            console.error('Login error:', error);
            return { success: false, error: error.message };
        }
    };

    // Logout
    const logout = async () => {
        try {
            await signOut(auth);
            return { success: true };
        } catch (error) {
            console.error('Logout error:', error);
            return { success: false, error: error.message };
        }
    };

    // Get all users (admin only)
    const getAllUsers = async () => {
        try {
            const dbRef = ref(database);
            const snapshot = await get(child(dbRef, 'users'));
            if (snapshot.exists()) {
                const users = [];
                snapshot.forEach((child) => {
                    users.push({ uid: child.key, ...child.val() });
                });
                return users;
            }
            return [];
        } catch (error) {
            console.error('Error getting users:', error);
            return [];
        }
    };

    const value = {
        user,
        loading,
        loginWithGoogle,
        logout,
        getAllUsers,
        isAdmin: user?.isAdmin || false
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export default AuthContext;
