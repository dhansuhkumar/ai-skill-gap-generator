import React, { useEffect, useState } from 'react';
import Navbar from '../components/Navbar';
import api from '../services/api';
import { User, Shield, BookOpen } from 'lucide-react';

const Profile = () => {
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchProfile();
    }, []);

    const fetchProfile = async () => {
        try {
            const response = await api.getProfile();
            setProfile(response.data);
        } catch (err) {
            setError('Failed to load profile. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    if (loading) return (
        <>
            <Navbar />
            <div className="container" style={{ paddingTop: '6rem', textAlign: 'center' }}>
                <p>Loading profile...</p>
            </div>
        </>
    );

    return (
        <>
            <Navbar />
            <div className="container" style={{ paddingTop: 'calc(var(--header-height) + 2rem)' }}>
                <h1 style={{ marginBottom: '2rem' }}>User Profile</h1>

                {error && <div className="error-message">{error}</div>}

                {profile && (
                    <div style={{ display: 'grid', gap: '2rem' }}>
                        <div className="glass-panel" style={{ padding: '2rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
                                <div style={{ padding: '1.5rem', background: 'var(--color-primary)', borderRadius: '50%' }}>
                                    <User size={48} color="white" />
                                </div>
                                <div>
                                    <h2 style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>{profile.username || 'User'}</h2>
                                    <p>Member since {new Date().getFullYear()}</p>
                                </div>
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
                                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: '1rem' }}>
                                    <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <Shield size={18} /> Target Role
                                    </h3>
                                    <p style={{ fontSize: '1.2rem', fontWeight: 500, color: 'var(--color-primary)' }}>
                                        {profile.role || 'Not set'}
                                    </p>
                                </div>

                                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '1.5rem', borderRadius: '1rem' }}>
                                    <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <BookOpen size={18} /> Skills
                                    </h3>
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                                        {profile.skills && profile.skills.length > 0 ? (
                                            profile.skills.map((skill, idx) => (
                                                <span key={idx} style={{ background: 'rgba(255,255,255,0.1)', padding: '2px 8px', borderRadius: '12px', fontSize: '0.9rem' }}>
                                                    {skill}
                                                </span>
                                            ))
                                        ) : (
                                            <span style={{ color: 'var(--color-text-muted)' }}>No skills saved</span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </>
    );
};

export default Profile;
