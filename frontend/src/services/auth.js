import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_KEY || '';
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

let supabase = null;
if (supabaseUrl && supabaseAnonKey) {
    supabase = createClient(supabaseUrl, supabaseAnonKey);
} else {
    console.warn('Supabase credentials not configured. Using fallback local auth.');
}

export const authService = {
    login: async (email, password) => {
        // If Supabase is configured, use it; otherwise fallback to local API
        if (supabase) {
            try {
                const { data, error } = await supabase.auth.signInWithPassword({
                    email,
                    password,
                });

                if (error) {
                    throw new Error(error.message || 'Login failed');
                }

                if (data.session && data.session.access_token) {
                    localStorage.setItem('jwtToken', data.session.access_token);
                    localStorage.setItem('username', data.user?.email || email);
                    localStorage.setItem('userId', data.user?.id || '');

                    // Sync profile with backend
                    try {
                        await fetch(`${API_URL}/api/sync_profile`, {
                            method: 'POST',
                            headers: {
                                'Authorization': `Bearer ${data.session.access_token}`,
                                'Content-Type': 'application/json'
                            }
                        });
                    } catch (err) {
                        console.warn('Profile sync failed:', err);
                    }

                    return {
                        access_token: data.session.access_token,
                        username: data.user?.email || email,
                        user: data.user
                    };
                }
                throw new Error('No session received');
            } catch (error) {
                throw error.message || 'Login failed';
            }
        } else {
            // Fallback to local API auth
            try {
                const response = await fetch(`${API_URL}/auth/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                const data = await response.json();
                if (response.ok && data.access_token) {
                    localStorage.setItem('jwtToken', data.access_token);
                    localStorage.setItem('username', data.email || email);

                    // Sync profile with backend
                    try {
                        await fetch(`${API_URL}/api/sync_profile`, {
                            method: 'POST',
                            headers: {
                                'Authorization': `Bearer ${data.access_token}`,
                                'Content-Type': 'application/json'
                            }
                        });
                    } catch (err) {
                        console.warn('Profile sync failed:', err);
                    }

                    return data;
                }
                throw new Error(data.error || 'Login failed');
            } catch (error) {
                throw error.message || 'Login failed';
            }
        }
    },

    register: async (email, password) => {
        // If Supabase is configured, use it; otherwise fallback to local API
        if (supabase) {
            try {
                const { data, error } = await supabase.auth.signUp({
                    email,
                    password,
                });

                if (error) {
                    throw new Error(error.message || 'Registration failed');
                }

                // If email confirmation is required, user might not have session immediately
                if (data.session && data.session.access_token) {
                    localStorage.setItem('jwtToken', data.session.access_token);
                    localStorage.setItem('username', data.user?.email || email);
                    localStorage.setItem('userId', data.user?.id || '');

                    // Sync profile with backend
                    try {
                        await fetch(`${API_URL}/api/sync_profile`, {
                            method: 'POST',
                            headers: {
                                'Authorization': `Bearer ${data.session.access_token}`,
                                'Content-Type': 'application/json'
                            }
                        });
                    } catch (err) {
                        console.warn('Profile sync failed:', err);
                    }
                }

                return {
                    message: 'Registration successful',
                    user: data.user,
                    session: data.session
                };
            } catch (error) {
                throw error.message || 'Registration failed';
            }
        } else {
            // Fallback to local API auth
            try {
                const response = await fetch(`${API_URL}/auth/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                const data = await response.json();
                if (response.ok) {
                    // For local registration, user needs to login separately
                    // No token returned from registration endpoint
                    return data;
                }
                throw new Error(data.error || 'Registration failed');
            } catch (error) {
                throw error.message || 'Registration failed';
            }
        }
    },

    logout: async () => {
        if (supabase) {
            await supabase.auth.signOut();
        }
        localStorage.removeItem('jwtToken');
        localStorage.removeItem('username');
        localStorage.removeItem('userId');
        window.location.href = '/login';
    },

    isAuthenticated: () => {
        return !!localStorage.getItem('jwtToken');
    },

    getCurrentUser: () => {
        return localStorage.getItem('username');
    },

    getUserId: () => {
        return localStorage.getItem('userId');
    }
};
