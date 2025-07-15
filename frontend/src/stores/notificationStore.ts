import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  timestamp: string
  read: boolean
  action?: {
    label: string
    onClick: () => void
  }
  dismissible?: boolean
  duration?: number // Auto-dismiss after milliseconds
  source?: string // Which agent/system generated this
}

interface NotificationState {
  notifications: Notification[]
  unreadCount: number
  isNotificationPanelOpen: boolean
  settings: {
    enabled: boolean
    sound: boolean
    desktop: boolean
    types: {
      success: boolean
      error: boolean
      warning: boolean
      info: boolean
    }
  }
  
  // Actions
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void
  markAsRead: (id: string) => void
  markAllAsRead: () => void
  dismissNotification: (id: string) => void
  clearAllNotifications: () => void
  toggleNotificationPanel: () => void
  updateSettings: (settings: Partial<NotificationState['settings']>) => void
  
  // Convenience methods
  success: (title: string, message: string, options?: Partial<Notification>) => void
  error: (title: string, message: string, options?: Partial<Notification>) => void
  warning: (title: string, message: string, options?: Partial<Notification>) => void
  info: (title: string, message: string, options?: Partial<Notification>) => void
}

export const useNotificationStore = create<NotificationState>()(
  persist(
    (set, get) => ({
      notifications: [],
      unreadCount: 0,
      isNotificationPanelOpen: false,
      settings: {
        enabled: true,
        sound: true,
        desktop: true,
        types: {
          success: true,
          error: true,
          warning: true,
          info: true
        }
      },

      addNotification: (notification) => {
        const { settings } = get()
        
        // Check if this notification type is enabled
        if (!settings.enabled || !settings.types[notification.type]) {
          return
        }

        const newNotification: Notification = {
          ...notification,
          id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
          timestamp: new Date().toISOString(),
          read: false,
          dismissible: notification.dismissible ?? true
        }

        set(state => ({
          notifications: [newNotification, ...state.notifications],
          unreadCount: state.unreadCount + 1
        }))

        // Play notification sound if enabled
        if (settings.sound) {
          try {
            const audio = new Audio('/notification.mp3')
            audio.volume = 0.3
            audio.play().catch(() => {
              // Ignore audio play errors (user interaction required)
            })
          } catch (error) {
            // Ignore audio errors
          }
        }

        // Show desktop notification if enabled and permitted
        if (settings.desktop && 'Notification' in window && Notification.permission === 'granted') {
          new Notification(newNotification.title, {
            body: newNotification.message,
            icon: '/Dreamcatcher_logo.png',
            badge: '/Dreamcatcher_logo.png',
            tag: newNotification.id,
            requireInteraction: newNotification.type === 'error'
          })
        }

        // Auto-dismiss after duration
        if (newNotification.duration) {
          setTimeout(() => {
            get().dismissNotification(newNotification.id)
          }, newNotification.duration)
        }
      },

      markAsRead: (id) => {
        set(state => ({
          notifications: state.notifications.map(n => 
            n.id === id ? { ...n, read: true } : n
          ),
          unreadCount: Math.max(0, state.unreadCount - 1)
        }))
      },

      markAllAsRead: () => {
        set(state => ({
          notifications: state.notifications.map(n => ({ ...n, read: true })),
          unreadCount: 0
        }))
      },

      dismissNotification: (id) => {
        set(state => {
          const notification = state.notifications.find(n => n.id === id)
          const unreadCountDecrease = notification && !notification.read ? 1 : 0
          
          return {
            notifications: state.notifications.filter(n => n.id !== id),
            unreadCount: Math.max(0, state.unreadCount - unreadCountDecrease)
          }
        })
      },

      clearAllNotifications: () => {
        set({
          notifications: [],
          unreadCount: 0
        })
      },

      toggleNotificationPanel: () => {
        set(state => ({
          isNotificationPanelOpen: !state.isNotificationPanelOpen
        }))
      },

      updateSettings: (newSettings) => {
        set(state => ({
          settings: { ...state.settings, ...newSettings }
        }))
      },

      // Convenience methods
      success: (title, message, options = {}) => {
        get().addNotification({
          type: 'success',
          title,
          message,
          duration: 5000,
          ...options
        })
      },

      error: (title, message, options = {}) => {
        get().addNotification({
          type: 'error',
          title,
          message,
          duration: 8000,
          ...options
        })
      },

      warning: (title, message, options = {}) => {
        get().addNotification({
          type: 'warning',
          title,
          message,
          duration: 6000,
          ...options
        })
      },

      info: (title, message, options = {}) => {
        get().addNotification({
          type: 'info',
          title,
          message,
          duration: 4000,
          ...options
        })
      }
    }),
    {
      name: 'dreamcatcher-notifications',
      partialize: (state) => ({
        notifications: state.notifications.slice(0, 100), // Keep only latest 100
        settings: state.settings
      })
    }
  )
)

// Request desktop notification permission
export const requestNotificationPermission = async () => {
  if ('Notification' in window && Notification.permission === 'default') {
    try {
      const permission = await Notification.requestPermission()
      return permission === 'granted'
    } catch (error) {
      console.error('Failed to request notification permission:', error)
      return false
    }
  }
  return Notification.permission === 'granted'
}