import api from './api';

export const authService = {
    login: async (username, password) => {
        try {
            const response = await api.login(username, password);
            if (response.data.access_token) {
                localStorage.setItem('token', response.data.access_token);
                localStorage.setItem('username', response.data.username);
                return response.data;
            }
            throw new Error('No token received');
        } catch (error) {
            throw error.response?.data?.error || 'Login failed';
        }
    },

    register: async (username, password) => {
        try {
            const response = await api.register(username, password);
            return response.data;
        } catch (error) {
            throw error.response?.data?.error || 'Registration failed';
        }
    },

    logout: () => {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        // Optional: redirect or reload
        window.location.href = '/login';
    },

    isAuthenticated: () => {
        return !!localStorage.getItem('token');
    },

    getCurrentUser: () => {
        return localStorage.getItem('username');
    }
};
