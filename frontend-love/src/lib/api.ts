import type { 
  ResumeUploadResponse, 
  SkillGapAnalysisRequest, 
  SkillGapAnalysisResponse 
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL;
console.log("API BASE URL:", API_BASE_URL);


function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('access_token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

function getAuthHeadersForFormData(): HeadersInit {
  const token = localStorage.getItem('access_token');
  const headers: HeadersInit = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function handleAuthError(response: Response): Promise<void> {
  if (response.status === 401) {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = '/login';
    throw new Error('Session expired. Please log in again.');
  }
}

export const api = {
  async uploadResume(file: File): Promise<ResumeUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/api/upload_resume`, {
      method: 'POST',
      headers: getAuthHeadersForFormData(),
      body: formData,
    });

    await handleAuthError(response);

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || 'Failed to upload resume');
    }

    return response.json();
  },

  async getRecommendations(request: SkillGapAnalysisRequest): Promise<SkillGapAnalysisResponse> {
    const response = await fetch(`${API_BASE_URL}/api/recommend`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    });

    await handleAuthError(response);

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || 'Failed to get recommendations');
    }

    return response.json();
  },
};
