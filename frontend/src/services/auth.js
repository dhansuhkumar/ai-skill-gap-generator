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

// ─── Token Refresh ────────────────────────────────────────────────────────────
// Supabase JWTs expire after 1 hour. We refresh 5 min before that (every 55 min).
const REFRESH_INTERVAL_MS = 55 * 60 * 1000; // 55 minutes
let _refreshTimer = null;

const _syncProfile = async (token) => {
    try {
        await fetch(`${API_URL}/api/sync_profile`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
    } catch (err) {
        console.warn('Profile sync failed:', err);
    }
};

export const refreshSession = async () => {
    if (!supabase) return null;
    try {
        const { data, error } = await supabase.auth.refreshSession();
        if (error || !data?.session) {
            console.warn('Token refresh failed — logging out:', error?.message);
            authService.logout();
            return null;
        }
        const { access_token, refresh_token } = data.session;
        localStorage.setItem('jwtToken', access_token);
        if (data.user?.email) localStorage.setItem('username', data.user.email);
        if (data.user?.id) localStorage.setItem('userId', data.user.id);
        console.info('Supabase token refreshed successfully');
        return access_token;
    } catch (err) {
        console.error('Unexpected error during token refresh:', err);
        return null;
    }
};

const startAutoRefresh = () => {
    stopAutoRefresh(); // clear any existing timer first
    _refreshTimer = setInterval(async () => {
        const token = localStorage.getItem('jwtToken');
        if (token) {
            await refreshSession();
        } else {
            stopAutoRefresh();
        }
    }, REFRESH_INTERVAL_MS);
};

const stopAutoRefresh = () => {
    if (_refreshTimer) {
        clearInterval(_refreshTimer);
        _refreshTimer = null;
    }
};
// ─────────────────────────────────────────────────────────────────────────────

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

                    // Start auto-refresh timer
                    startAutoRefresh();

                    // Sync profile with backend
                    await _syncProfile(data.session.access_token);

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

                    startAutoRefresh();
                    await _syncProfile(data.access_token);

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

                    startAutoRefresh();
                    await _syncProfile(data.session.access_token);
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
                    return data;
                }
                throw new Error(data.error || 'Registration failed');
            } catch (error) {
                throw error.message || 'Registration failed';
            }
        }
    },

    logout: async () => {
        stopAutoRefresh();
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

