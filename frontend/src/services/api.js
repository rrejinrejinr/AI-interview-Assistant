import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({ baseURL: API_BASE_URL });

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error)
);

// Auth
export const registerApi = (name, email, password) =>
  apiClient.post('/auth/register', { name, email, password }).then(r => r.data);
export const verifyOtpApi = (email, otp) =>
  apiClient.post('/auth/verify-otp', { email, otp }).then(r => r.data);
export const loginApi = (email, password) =>
  apiClient.post('/auth/login', { email, password }).then(r => r.data);
export const getMeApi = () => apiClient.get('/auth/me').then(r => r.data);

// Core
export const checkHealthApi = () => apiClient.get('/health').then(r => r.data);
export const getLlmStatusApi = () => apiClient.get('/llm/status').then(r => r.data);
export const uploadResumeApi = (file) => {
  const formData = new FormData();
  formData.append('resume', file);
  return apiClient.post('/resume/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }).then(r => r.data);
};
export const getUserResumesApi = () => apiClient.get('/resumes').then(r => r.data);
export const getActiveResumeDetailsApi = () => apiClient.get('/resume/active').then(r => r.data);
export const getResumeDetailsApi = (resume_id) => {
  if (!resume_id || resume_id === 'active') {
    return apiClient.get('/resume/active').then(r => r.data);
  }
  return apiClient.get(`/resume/${resume_id}`).then(r => r.data);
};
export const analyzeAtsApi = (resume_id, job_title, job_description) =>
  apiClient.post('/ats/analyze', { resume_id, job_title, job_description }).then(r => r.data);
export const getAtsHistoryApi = () => apiClient.get('/ats/history').then(r => r.data);
export const getAtsResultApi = (result_id) => apiClient.get(`/ats/${result_id}`).then(r => r.data);

// Dedicated Resume Practice (10, 20, 30 Questions & Question Sources)
export const startPracticeApi = (resume_id, question_count, difficulty, practice_type, job_description, question_source = "resume_based") =>
  apiClient.post('/practice/start', { resume_id, question_count, difficulty, practice_type, job_description, question_source }).then(r => r.data);
export const getPracticeSessionApi = (session_id) =>
  apiClient.get(`/practice/${session_id}`).then(r => r.data);
export const submitPracticeAnswerApi = (session_id, question_id, user_answer) =>
  apiClient.post(`/practice/${session_id}/answer`, { question_id, user_answer }).then(r => r.data);
export const completePracticeApi = (session_id) =>
  apiClient.post(`/practice/${session_id}/complete`).then(r => r.data);
export const exitPracticeApi = (session_id) =>
  apiClient.post(`/practice/${session_id}/exit`).then(r => r.data);
export const getPracticeSessionsApi = () =>
  apiClient.get('/practice/sessions').then(r => r.data);
export const getPracticeReportApi = (session_id) =>
  apiClient.get(`/practice/${session_id}/report`).then(r => r.data);

// Dedicated 30-Question Resume Mock Interview (Pre-flight Camera Photo, Fullscreen, Face Presence Monitoring)
export const startMockInterviewApi = (resume_id, difficulty = "Medium", job_description = null) =>
  apiClient.post('/mock-interview/start', { resume_id, difficulty, job_description }).then(r => r.data);
export const verifyMockInterviewPhotoApi = (session_id) =>
  apiClient.post(`/mock-interview/${session_id}/verify-photo`).then(r => r.data);
export const getMockInterviewSessionsApi = () =>
  apiClient.get('/mock-interview/sessions').then(r => r.data);
export const getMockInterviewSessionApi = (session_id) =>
  apiClient.get(`/mock-interview/${session_id}`).then(r => r.data);
export const submitMockAnswerApi = (session_id, question_id, user_answer) =>
  apiClient.post(`/mock-interview/${session_id}/answer`, { question_id, user_answer }).then(r => r.data);
export const exitMockInterviewApi = (session_id) =>
  apiClient.post(`/mock-interview/${session_id}/exit`).then(r => r.data);
export const rejectMockInterviewApi = (session_id, reason) =>
  apiClient.post(`/mock-interview/${session_id}/reject`, { reason }).then(r => r.data);
export const completeMockInterviewApi = (session_id) =>
  apiClient.post(`/mock-interview/${session_id}/complete`).then(r => r.data);
export const getMockInterviewReportApi = (session_id) =>
  apiClient.get(`/mock-interview/${session_id}/report`).then(r => r.data);

// Dedicated AI One-to-One HR Interview (Conversational Voice / Text)
export const startAiInterviewApi = (resume_id) =>
  apiClient.post('/ai-interview/start', { resume_id }).then(r => r.data);
export const getAiInterviewSessionsApi = () =>
  apiClient.get('/ai-interview/sessions').then(r => r.data);
export const getAiInterviewSessionApi = (session_id) =>
  apiClient.get(`/ai-interview/${session_id}`).then(r => r.data);
export const sendAiInterviewMessageApi = (session_id, message) =>
  apiClient.post(`/ai-interview/${session_id}/message`, { message }).then(r => r.data);
export const completeAiInterviewApi = (session_id) =>
  apiClient.post(`/ai-interview/${session_id}/complete`).then(r => r.data);
export const getAiInterviewReportApi = (session_id) =>
  apiClient.get(`/ai-interview/${session_id}/report`).then(r => r.data);

// Legacy Mock Interview (Phase 6)
export const startInterviewApi = (resume_id, job_description, interview_type, difficulty, num_questions) =>
  apiClient.post('/interview/start', { resume_id, job_description, interview_type, difficulty, num_questions }).then(r => r.data);
export const getInterviewSessionApi = (session_id) =>
  apiClient.get(`/interview/${session_id}`).then(r => r.data);
export const submitAnswerApi = (session_id, question_id, user_answer) =>
  apiClient.post(`/interview/${session_id}/answer`, { question_id, user_answer }).then(r => r.data);
export const completeInterviewApi = (session_id) =>
  apiClient.post(`/interview/${session_id}/complete`).then(r => r.data);
export const getInterviewSessionsApi = () =>
  apiClient.get('/interview/sessions').then(r => r.data);
export const getInterviewReportApi = (session_id) =>
  apiClient.get(`/interview/${session_id}/report`).then(r => r.data);

// Phase 8 Dynamic LLM & Follow-Up Endpoints
export const getDynamicQuestionApi = (resume_id, interview_type, difficulty, job_description, previous_qa) =>
  apiClient.post('/llm/interview/question', { resume_id, interview_type, difficulty, job_description, previous_qa }).then(r => r.data);
export const getFollowupQuestionApi = (resume_id, previous_question, previous_answer) =>
  apiClient.post('/llm/interview/followup', { resume_id, previous_question, previous_answer }).then(r => r.data);
export const getLlmFeedbackApi = (resume_id, question, answer) =>
  apiClient.post('/llm/interview/feedback', { resume_id, question, answer }).then(r => r.data);

// Recommendations & AI Tech Bot (RAG)
export const analyzeRecommendationsApi = (resume_id, job_description_id, job_description_text) =>
  apiClient.post('/recommendations/analyze', { resume_id, job_description_id, job_description_text }).then(r => r.data);
export const getRecommendationsApi = (resume_id) =>
  apiClient.get('/recommendations', { params: { resume_id } }).then(r => r.data);
export const getRoadmapApi = (resume_id) =>
  apiClient.get('/recommendations/roadmap', { params: { resume_id } }).then(r => r.data);
export const analyzeResumeImprovementsApi = (resume_id, target_role) =>
  apiClient.post('/resume/analyze', { resume_id, target_role }).then(r => r.data);
export const queryRagApi = (query, resume_id, history = []) =>
  apiClient.post('/rag/query', { query, resume_id, history }).then(r => r.data);

// Help & Support
export const submitSupportTicketApi = (name, email, category, subject, description) => {
  const payload = { name, category, subject, description };
  // Only include email if non-empty — Pydantic EmailStr rejects "" but accepts null/None
  if (email && email.trim()) payload.email = email.trim();
  return apiClient.post('/support/ticket', payload).then(r => r.data);
};
export const getSupportTicketsApi = () =>
  apiClient.get('/support/tickets').then(r => r.data);
export const querySupportChatApi = (query) =>
  apiClient.post('/support/chat', { query }).then(r => r.data);

// Active Resume Centralization
export const setActiveResumeApi = (resume_id) =>
  apiClient.post('/user/active-resume', { resume_id }).then(r => r.data);
export const getActiveResumeApi = () =>
  apiClient.get('/user/active-resume').then(r => r.data);

// Resume Builder
export const generateResumePdfApi = (resumeData) =>
  apiClient.post('/resume-builder/generate', resumeData).then(r => r.data);
export const getBuiltResumesHistoryApi = () =>
  apiClient.get('/resume-builder/history').then(r => r.data);
export const resendResumeEmailApi = (resume_id) =>
  apiClient.post(`/resume-builder/${resume_id}/resend-email`).then(r => r.data);
export const fetchResumePdfBlobApi = (resume_id) =>
  apiClient.get(`/resume-builder/download/${resume_id}`, { responseType: 'blob' }).then(r => r.data);
export const getResumeDownloadUrl = (resume_id) =>
  `${API_BASE_URL}/resume-builder/download/${resume_id}`;

// User Profile Management
export const getUserProfileApi = () =>
  apiClient.get('/user/profile').then(r => r.data);
export const updateUserProfileApi = (profileData) =>
  apiClient.put('/user/profile', profileData).then(r => r.data);
export const uploadProfilePhotoApi = (photo) =>
  apiClient.post('/user/profile/photo', { photo }).then(r => r.data);
export const deleteProfilePhotoApi = () =>
  apiClient.delete('/user/profile/photo').then(r => r.data);

// Topic-Based DSA Problem Solving
export const getDsaJudge0StatusApi = () =>
  apiClient.get('/dsa/judge0-status').then(r => r.data);
export const getDsaTopicsApi = () =>
  apiClient.get('/dsa/topics').then(r => r.data);
export const getDsaProblemsApi = (params = {}) =>
  apiClient.get('/dsa/problems', { params }).then(r => r.data);
export const getDsaProblemDetailApi = (problemRef) =>
  apiClient.get(`/dsa/problems/${problemRef}`).then(r => r.data);
export const updateDsaProblemStatusApi = (problemRef, status, notes = null) =>
  apiClient.post(`/dsa/problems/${problemRef}/status`, { status, notes }).then(r => r.data);
export const getDsaProgressApi = () =>
  apiClient.get('/dsa/progress').then(r => r.data);
export const executeDsaCodeApi = (problemRef, code, language, stdin = "") =>
  apiClient.post(`/dsa/problems/${problemRef}/execute`, { code, language, stdin }).then(r => r.data);
export const submitDsaCodeApi = (problemRef, code, language) =>
  apiClient.post(`/dsa/problems/${problemRef}/submit`, { code, language }).then(r => r.data);



