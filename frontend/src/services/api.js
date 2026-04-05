import axios from 'axios';
import { authService } from './auth';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

const apiClient = axios.create({
    baseURL: API_URL,
    withCredentials: true,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

apiClient.interceptors.request.use(
    (config) => {
        config.headers['X-Session-ID'] = authService.getSessionId();
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        return Promise.reject(error);
    }
);

export const api = {
    uploadResume: (formData) =>
        apiClient.post('/api/upload_resume', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        }),

    confirmSkills: (skills) => apiClient.post('/api/confirm_skills', { skills }),

    analyzeGaps: (skills, target_role) => apiClient.post('/api/recommend', { role: target_role, skills }),

    analyzeRoleGaps: (skills, target_role) => apiClient.post('/api/analyze_role_gaps', { role: target_role, skills }, { timeout: 25000 }),

    generateLearningPath: (params) => apiClient.post('/api/generate_learning_path', params, { timeout: 60000 }),

    recommend: (role, skills, provider, includeYoutube) =>
        apiClient.post('/api/recommend', { role, skills, provider, include_youtube: includeYoutube }),

    roleChat: (role, messages, provider) =>
        apiClient.post('/api/role-chat', { role, messages, provider }),

    getProfile: () => apiClient.get('/api/profile'),
    saveProfile: (role, skills, recommendations) =>
        apiClient.post('/api/save_profile', { role, skills, recommendations }),

    getSavedLearningPath: () => apiClient.get('/api/get_saved_learning_path'),
    saveLearningPath: (data) => apiClient.post('/api/save_learning_path', data),

    getDashboardData: (data) => apiClient.post('/api/get_dashboard_data', data),
    saveLearningProgress: (data) => apiClient.post('/api/save_learning_progress', data),

    updateTaskProgress: (data) => apiClient.post('/api/update_task_progress', data),
    getTaskProgress: (pathId) => apiClient.get('/api/get_task_progress', { params: { path_id: pathId } }),

    analyzeGitHub: (username) => apiClient.post('/api/analyze-github', { github_username: username }),

    getStarterProjectUrl: (skillName) => `${API_URL}/api/starter/${encodeURIComponent(skillName)}`,

    getJobMatches: (skills, role, experienceLevel = 'neutral') => 
        apiClient.post('/api/job_matches', { skills, role, experience_level: experienceLevel }),
};

export default api;
