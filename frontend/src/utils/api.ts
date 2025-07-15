import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

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
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    
    return Promise.reject(error)
  }
)

// API functions
export const api = {
  // Health check
  health: () => apiClient.get('/health'),
  
  // Ideas
  ideas: {
    list: (params?: any) => apiClient.get('/ideas', { params }),
    get: (id: string) => apiClient.get(`/ideas/${id}`),
    create: (data: any) => apiClient.post('/ideas', data),
    update: (id: string, data: any) => apiClient.put(`/ideas/${id}`, data),
    delete: (id: string) => apiClient.delete(`/ideas/${id}`),
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
}

export default apiClient