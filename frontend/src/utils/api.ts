import axios from 'axios'

const resolveApiBaseUrl = (): string => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }

  if (typeof window !== 'undefined') {
    return `${window.location.origin}/api`
  }

  return 'http://localhost:8000/api'
}

const API_BASE_URL = resolveApiBaseUrl()

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
// Auth refresh/logout handling is centralized in authStore.ts
apiClient.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error)
)

// API functions
export const api = {
  // Health check
  health: () => apiClient.get('/health'),
  
  // Authentication
  auth: {
    login: (data: any) => apiClient.post('/auth/login', data),
    register: (data: any) => apiClient.post('/auth/register', data),
    logout: () => apiClient.post('/auth/logout'),
    refresh: (data: any) => apiClient.post('/auth/refresh', data),
    me: () => apiClient.get('/auth/me'),
    changePassword: (data: any) => apiClient.post('/auth/change-password', data),
    searchUsers: (q: string, limit = 10) => apiClient.get('/auth/users/search', { params: { q, limit } }),
    unlockUser: (userId: string) => apiClient.post(`/auth/users/${userId}/unlock`),
    resetUserPassword: (userId: string, newPassword: string) =>
      apiClient.post(`/auth/users/${userId}/reset-password`, { new_password: newPassword }),
  },
  
  // Ideas
  ideas: {
    list: (params?: any) => apiClient.get('/ideas', { params }),
    get: (id: string) => apiClient.get(`/ideas/${id}`),
    create: (data: any) => apiClient.post('/ideas', data),
    update: (id: string, data: any) => apiClient.put(`/ideas/${id}`, data),
    delete: (id: string) => apiClient.delete(`/ideas/${id}`),
    related: (id: string, params?: any) => apiClient.get(`/ideas/${id}/related`, { params }),
    generateEmbedding: (id: string) => apiClient.post(`/ideas/${id}/generate_embedding`),
  },
  
  // Capture
  capture: {
    text: (data: any) => apiClient.post('/capture/text', data),
    voice: (formData: FormData) => apiClient.post('/capture/voice', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
    dream: (formData: FormData) => apiClient.post('/capture/dream', formData),
  },
  
  // Proposals
  proposals: {
    list: (params?: any) => apiClient.get('/proposals', { params }),
    get: (id: string) => apiClient.get(`/proposals/${id}`),
    approve: (id: string, notes?: string) => {
      const formData = new FormData()
      if (notes) formData.append('notes', notes)
      return apiClient.post(`/proposals/${id}/approve`, formData)
    },
  },
  
  // Agents
  agents: {
    status: () => apiClient.get('/agents/status'),
  },
  
  // Stats
  stats: () => apiClient.get('/stats'),
  
  // Semantic Search
  search: {
    semantic: (params: any) => apiClient.get('/search/semantic', { params }),
  },
  
  // Embeddings
  embeddings: {
    stats: () => apiClient.get('/embeddings/stats'),
    batchUpdate: (batchSize?: number) => apiClient.post('/embeddings/batch_update', { batch_size: batchSize }),
    logStats: () => apiClient.get('/logs/embeddings/stats'),
    logBatchUpdate: (batchSize?: number) => apiClient.post('/logs/embeddings/batch_update', null, {
      params: { batch_size: batchSize }
    }),
  },

  logs: {
    list: (params?: any) => apiClient.get('/logs', { params }),
    semanticSearch: (params: any) => apiClient.get('/logs/search/semantic', { params }),
  },

  system: {
    actionsStatus: () => apiClient.get('/system/actions'),
    actionsHistory: (params?: { limit?: number; status?: 'success' | 'failed' }) =>
      apiClient.get('/system/actions/history', { params }),
    runAction: (action: string) => apiClient.post(`/system/actions/${action}`),
  },

  settings: {
    apiKeysStatus: () => apiClient.get('/settings/api-keys/status'),
    updateApiKeys: (data: {
      anthropic_api_key?: string
      openai_api_key?: string
      openrouter_api_key?: string
      persist_to_env?: boolean
    }) => apiClient.post('/settings/api-keys', data),
  },
}

export default apiClient
