import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { apiClient } from '../utils/api'

interface User {
  id: string
  email: string
  username: string
  full_name: string
  is_active: boolean
  is_verified: boolean
  created_at: string
  roles: string[]
}

interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  
  // Actions
  login: (email: string, password: string) => Promise<boolean>
  register: (userData: RegisterData) => Promise<boolean>
  logout: () => void
  refreshAccessToken: () => Promise<boolean>
  clearError: () => void
  updateUser: (userData: Partial<User>) => void
  checkAuthStatus: () => Promise<boolean>
}

interface RegisterData {
  email: string
  username: string
  full_name: string
  password: string
  confirm_password: string
}

interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (email_or_username: string, password: string) => {
        set({ isLoading: true, error: null })
        
        try {
          const response = await apiClient.post<LoginResponse>('/auth/login', {
            email_or_username,
            password
          })
          
          const { access_token, refresh_token, user } = response.data
          
          // Update local storage
          localStorage.setItem('auth_token', access_token)
          localStorage.setItem('refresh_token', refresh_token)
          
          set({
            user,
            token: access_token,
            refreshToken: refresh_token,
            isAuthenticated: true,
            isLoading: false,
            error: null
          })
          
          return true
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Login failed'
          set({ 
            isLoading: false, 
            error: errorMessage,
            isAuthenticated: false
          })
          return false
        }
      },

      register: async (userData: RegisterData) => {
        set({ isLoading: true, error: null })
        
        try {
          const response = await apiClient.post<User>('/auth/register', userData)
          
          set({
            isLoading: false,
            error: null
          })
          
          return true
        } catch (error: any) {
          const errorMessage = error.response?.data?.detail || 'Registration failed'
          set({ 
            isLoading: false, 
            error: errorMessage 
          })
          return false
        }
      },

      logout: () => {
        const { token } = get()
        
        // Call logout endpoint if token exists
        if (token) {
          apiClient.post('/auth/logout').catch(console.error)
        }
        
        // Clear local storage
        localStorage.removeItem('auth_token')
        localStorage.removeItem('refresh_token')
        
        set({
          user: null,
          token: null,
          refreshToken: null,
          isAuthenticated: false,
          error: null
        })
      },

      refreshAccessToken: async () => {
        const { refreshToken } = get()
        
        if (!refreshToken) {
          return false
        }
        
        try {
          const response = await apiClient.post<LoginResponse>('/auth/refresh', {
            refresh_token: refreshToken
          })
          
          const { access_token, refresh_token: newRefreshToken, user } = response.data
          
          // Update local storage
          localStorage.setItem('auth_token', access_token)
          localStorage.setItem('refresh_token', newRefreshToken)
          
          set({
            user,
            token: access_token,
            refreshToken: newRefreshToken,
            isAuthenticated: true,
            error: null
          })
          
          return true
        } catch (error) {
          // Refresh failed, logout user
          get().logout()
          return false
        }
      },

      clearError: () => {
        set({ error: null })
      },

      updateUser: (userData: Partial<User>) => {
        set(state => ({
          user: state.user ? { ...state.user, ...userData } : null
        }))
      },

      checkAuthStatus: async () => {
        const { token } = get()
        
        if (!token) {
          return false
        }
        
        try {
          const response = await apiClient.get<User>('/auth/me')
          
          set({
            user: response.data,
            isAuthenticated: true,
            error: null
          })
          
          return true
        } catch (error) {
          // Token is invalid, try to refresh
          const refreshed = await get().refreshAccessToken()
          return refreshed
        }
      }
    }),
    {
      name: 'dreamcatcher-auth',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated
      })
    }
  )
)

// Set up axios interceptor to handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      const authStore = useAuthStore.getState()
      const refreshed = await authStore.refreshAccessToken()
      
      if (refreshed) {
        // Update the authorization header and retry the request
        originalRequest.headers.Authorization = `Bearer ${authStore.token}`
        return apiClient(originalRequest)
      } else {
        // Refresh failed, redirect to login
        authStore.logout()
        window.location.href = '/login'
      }
    }
    
    return Promise.reject(error)
  }
)