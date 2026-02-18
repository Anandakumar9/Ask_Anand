import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add Interceptor to attach token
api.interceptors.request.use((config) => {
    if (typeof window !== 'undefined') {
        const storage = localStorage.getItem('studypulse-storage');
        if (storage) {
            try {
                const { state } = JSON.parse(storage);
                if (state.token) {
                    config.headers.Authorization = `Bearer ${state.token}`;
                }
            } catch (e) {
                console.error('Error parsing storage', e);
            }
        }
    }
    return config;
});

export const authApi = {
    login: (params: URLSearchParams) => api.post('/auth/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    }),
    register: (data: { email: string; name: string; password: string }) => api.post('/auth/register', data),
    googleAuth: (accessToken: string) => api.post('/auth/google', { access_token: accessToken }),
    forgotPassword: (email: string) => api.post('/auth/forgot-password', { email }),
    resetPassword: (accessToken: string, newPassword: string) =>
        api.post('/auth/reset-password', { access_token: accessToken, new_password: newPassword }),
    getMe: () => api.get('/auth/me'),
    updateProfile: (data: any) => api.patch('/auth/me', data),
};

export const examApi = {
    getExams: () => api.get('/exams/'),
    getExamDetails: (id: number) => api.get(`/exams/${id}`),
    getSubjects: (examId: number) => api.get(`/exams/${examId}/subjects`),
    getTopics: (examId: number, subjectId: number) => api.get(`/exams/${examId}/subjects/${subjectId}/topics`),
};

export const studyApi = {
    startSession: (topicId: number, durationMins: number, previousQuestionIds: number[] = []) =>
        api.post('/study/sessions', {
            topic_id: topicId,
            duration_mins: durationMins,
            previous_question_ids: previousQuestionIds,
        }),
    completeSession: (sessionId: number, actualDurationMins: number) =>
        api.post(`/study/sessions/${sessionId}/complete`, { actual_duration_mins: actualDurationMins }),
};

export const testApi = {
    startTest: (testData: { topic_id: number; session_id?: number; question_count?: number }) =>
        api.post('/mock-test/start', testData),
    submitTest: (testId: number, responses: any, totalTime: number) =>
        api.post(`/mock-test/${testId}/submit`, { responses, total_time_seconds: totalTime }),
    getResults: (testId: number) => api.get(`/mock-test/${testId}/results`),
};

export const profileApi = {
    getStats: () => api.get('/profile/stats'),
    updateProfile: (data: { display_name?: string; avatar_url?: string }) => api.put('/profile/update', data),
};

export const leaderboardApi = {
    getLeaderboard: (limit = 20) => api.get('/leaderboard/', { params: { limit } }),
};

export const dashboardApi = {
    getDashboard: () => api.get('/dashboard/'),
    getWeeklyStats: () => api.get('/dashboard/stats/weekly'),
};

export default api;
