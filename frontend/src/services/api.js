import axios from 'axios';

const API_URL = 'http://localhost:8080';

const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to add JWT token
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('jwtToken');
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            // Token expired or invalid
            localStorage.removeItem('jwtToken');
            localStorage.removeItem('username');
            localStorage.removeItem('userId');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export const api = {
    // Auth is handled separately or can be here. We usually keep login/register separates since they don't need token.
    login: (username, password) => apiClient.post('/auth/login', { username, password }),
    register: (username, password) => apiClient.post('/auth/register', { username, password }),

    // New Step-Based Flow
    uploadResume: (formData) =>
        apiClient.post('/api/upload_resume', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        }),

    confirmSkills: (skills) => apiClient.post('/api/confirm_skills', { skills }),

    analyzeGaps: (skills, target_role) => apiClient.post('/api/recommend', { role: target_role, skills }),

    analyzeRoleGaps: (skills, target_role) => apiClient.post('/api/analyze_role_gaps', { role: target_role, skills }),

    generateLearningPath: (params) => apiClient.post('/api/generate_learning_path', params),

    // Legacy / Other
    recommend: (role, skills, provider, includeYoutube) =>
        apiClient.post('/api/recommend', { role, skills, provider, include_youtube: includeYoutube }),

    roleChat: (role, messages, provider) =>
        apiClient.post('/api/role-chat', { role, messages, provider }),

    // Profile
    getProfile: () => apiClient.get('/api/profile'),
    saveProfile: (role, skills, recommendations) =>
        apiClient.post('/api/save_profile', { role, skills, recommendations }),

    // Starter Project Download URL helper
    getStarterProjectUrl: (skillName) => `${API_URL}/api/starter/${encodeURIComponent(skillName)}`
};

export default api;
