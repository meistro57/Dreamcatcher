import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AppState {
  isInitialized: boolean
  isDarkMode: boolean
  isOnline: boolean
  lastSync: string | null
  settings: {
    autoCapture: boolean
    voiceWakeWord: string
    defaultUrgency: string
    notifications: boolean
    offlineMode: boolean
    compressionLevel: number
  }
  
  // Actions
  initializeStore: () => void
  setOnlineStatus: (status: boolean) => void
  updateSettings: (settings: Partial<AppState['settings']>) => void
  setLastSync: (timestamp: string) => void
  toggleDarkMode: () => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      isInitialized: false,
      isDarkMode: true,
      isOnline: navigator.onLine,
      lastSync: null,
      settings: {
        autoCapture: false,
        voiceWakeWord: 'hey dreamcatcher',
        defaultUrgency: 'normal',
        notifications: true,
        offlineMode: true,
        compressionLevel: 0.8
      },

      initializeStore: () => {
        set({ isInitialized: true })
        
        // Set up online/offline listeners
        const handleOnline = () => set({ isOnline: true })
        const handleOffline = () => set({ isOnline: false })
        
        window.addEventListener('online', handleOnline)
        window.addEventListener('offline', handleOffline)
        
        // Cleanup function would be stored in a ref in real implementation
        return () => {
          window.removeEventListener('online', handleOnline)
          window.removeEventListener('offline', handleOffline)
        }
      },

      setOnlineStatus: (status: boolean) => {
        set({ isOnline: status })
      },

      updateSettings: (newSettings: Partial<AppState['settings']>) => {
        set(state => ({
          settings: { ...state.settings, ...newSettings }
        }))
      },

      setLastSync: (timestamp: string) => {
        set({ lastSync: timestamp })
      },

      toggleDarkMode: () => {
        set(state => ({ isDarkMode: !state.isDarkMode }))
      }
    }),
    {
      name: 'dreamcatcher-app',
      partialize: (state) => ({
        settings: state.settings,
        isDarkMode: state.isDarkMode,
        lastSync: state.lastSync
      })
    }
  )
)