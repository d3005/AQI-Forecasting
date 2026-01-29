import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Navigate } from 'react-router-dom';
import './AdminPage.css';

function AdminPage() {
    const { user, isAdmin, getAllUsers, loading } = useAuth();
    const [users, setUsers] = useState([]);
    const [loadingUsers, setLoadingUsers] = useState(true);

    useEffect(() => {
        const fetchUsers = async () => {
            if (isAdmin) {
                const allUsers = await getAllUsers();
                setUsers(allUsers);
            }
            setLoadingUsers(false);
        };

        if (!loading) {
            fetchUsers();
        }
    }, [isAdmin, loading, getAllUsers]);

    // Not logged in
    if (!loading && !user) {
        return <Navigate to="/login" replace />;
    }

    // Not admin
    if (!loading && !isAdmin) {
        return (
            <div className="admin-page">
                <div className="access-denied">
                    <h2>Access Denied</h2>
                    <p>You don't have permission to access this page.</p>
                    <a href="/" className="back-btn">Go to Dashboard</a>
                </div>
            </div>
        );
    }

    if (loading || loadingUsers) {
        return (
            <div className="admin-page">
                <div className="loading-container">
                    <div className="loader"></div>
                    <p>Loading users...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="admin-page">
            <header className="admin-header">
                <div className="header-content">
                    <h1>Admin Panel</h1>
                    <p>Manage users and view activity</p>
                </div>
                <a href="/" className="back-link">← Back to Dashboard</a>
            </header>

            <main className="admin-content">
                <section className="users-section">
                    <div className="section-header">
                        <h2>Registered Users</h2>
                        <span className="user-count">{users.length} users</span>
                    </div>

                    <div className="users-table-container">
                        <table className="users-table">
                            <thead>
                                <tr>
                                    <th>User</th>
                                    <th>Email</th>
                                    <th>Last Login</th>
                                    <th>Created</th>
                                </tr>
                            </thead>
                            <tbody>
                                {users.map((u) => (
                                    <tr key={u.uid}>
                                        <td>
                                            <div className="user-info">
                                                {u.photoURL ? (
                                                    <img src={u.photoURL} alt="" className="user-avatar" />
                                                ) : (
                                                    <div className="user-avatar-placeholder">
                                                        {u.displayName?.[0] || u.email?.[0] || '?'}
                                                    </div>
                                                )}
                                                <span className="user-name">{u.displayName || 'N/A'}</span>
                                            </div>
                                        </td>
                                        <td>{u.email}</td>
                                        <td>{u.lastLogin ? new Date(u.lastLogin).toLocaleString() : 'N/A'}</td>
                                        <td>{u.createdAt ? new Date(u.createdAt).toLocaleDateString() : 'N/A'}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {users.length === 0 && (
                        <div className="no-users">
                            <p>No users registered yet.</p>
                        </div>
                    )}
                </section>
            </main>
        </div>
    );
}

export default AdminPage;
