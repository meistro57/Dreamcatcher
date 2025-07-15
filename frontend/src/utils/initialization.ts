import { api } from './api'

export const initializeApp = async () => {
  try {
    // Check API health
    await api.health()
    
    // Initialize IndexedDB for offline storage
    await initializeOfflineStorage()
    
    // Set up notification permissions
    await setupNotifications()
    
    // Initialize wake word detection if supported
    await initializeWakeWord()
    
    console.log('App initialized successfully')
  } catch (error) {
    console.error('App initialization failed:', error)
    throw error
  }
}

const initializeOfflineStorage = async () => {
  if (!('indexedDB' in window)) {
    console.warn('IndexedDB not supported')
    return
  }
  
  try {
    const { openDB } = await import('idb')
    
    const db = await openDB('dreamcatcher', 1, {
      upgrade(db) {
        // Ideas store
        if (!db.objectStoreNames.contains('ideas')) {
          const ideaStore = db.createObjectStore('ideas', { keyPath: 'id' })
          ideaStore.createIndex('created_at', 'created_at')
          ideaStore.createIndex('urgency_score', 'urgency_score')
          ideaStore.createIndex('source_type', 'source_type')
        }
        
        // Proposals store
        if (!db.objectStoreNames.contains('proposals')) {
          const proposalStore = db.createObjectStore('proposals', { keyPath: 'id' })
          proposalStore.createIndex('created_at', 'created_at')
          proposalStore.createIndex('status', 'status')
        }
        
        // Pending sync store
        if (!db.objectStoreNames.contains('pending_sync')) {
          db.createObjectStore('pending_sync', { keyPath: 'id', autoIncrement: true })
        }
        
        // Audio cache store
        if (!db.objectStoreNames.contains('audio_cache')) {
          db.createObjectStore('audio_cache', { keyPath: 'id' })
        }
      }
    })
    
    console.log('Offline storage initialized')
    return db
  } catch (error) {
    console.error('Failed to initialize offline storage:', error)
  }
}

const setupNotifications = async () => {
  if (!('Notification' in window)) {
    console.warn('Notifications not supported')
    return
  }
  
  try {
    const permission = await Notification.requestPermission()
    
    if (permission === 'granted') {
      console.log('Notification permission granted')
    } else {
      console.log('Notification permission denied')
    }
  } catch (error) {
    console.error('Failed to setup notifications:', error)
  }
}

const initializeWakeWord = async () => {
  if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
    console.warn('Speech recognition not supported')
    return
  }
  
  try {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new SpeechRecognition()
    
    recognition.continuous = true
    recognition.interimResults = false
    recognition.lang = 'en-US'
    
    // Store for later use
    window.dreamcatcherSpeechRecognition = recognition
    
    console.log('Wake word detection initialized')
  } catch (error) {
    console.error('Failed to initialize wake word detection:', error)
  }
}

// Utility functions for offline storage
export const offlineStorage = {
  async saveIdea(idea: any) {
    try {
      const { openDB } = await import('idb')
      const db = await openDB('dreamcatcher', 1)
      await db.put('ideas', idea)
    } catch (error) {
      console.error('Failed to save idea offline:', error)
    }
  },
  
  async getIdeas() {
    try {
      const { openDB } = await import('idb')
      const db = await openDB('dreamcatcher', 1)
      return await db.getAll('ideas')
    } catch (error) {
      console.error('Failed to get offline ideas:', error)
      return []
    }
  },
  
  async addPendingSync(data: any) {
    try {
      const { openDB } = await import('idb')
      const db = await openDB('dreamcatcher', 1)
      await db.add('pending_sync', {
        ...data,
        timestamp: new Date().toISOString()
      })
    } catch (error) {
      console.error('Failed to add pending sync:', error)
    }
  },
  
  async getPendingSync() {
    try {
      const { openDB } = await import('idb')
      const db = await openDB('dreamcatcher', 1)
      return await db.getAll('pending_sync')
    } catch (error) {
      console.error('Failed to get pending sync:', error)
      return []
    }
  },
  
  async clearPendingSync() {
    try {
      const { openDB } = await import('idb')
      const db = await openDB('dreamcatcher', 1)
      await db.clear('pending_sync')
    } catch (error) {
      console.error('Failed to clear pending sync:', error)
    }
  }
}

// Notification utilities
export const notifications = {
  show(title: string, options?: NotificationOptions) {
    if (Notification.permission === 'granted') {
      return new Notification(title, {
        icon: '/pwa-192x192.png',
        badge: '/pwa-64x64.png',
        ...options
      })
    }
  },
  
  showIdeaCaptured(content: string) {
    return this.show('Idea Captured', {
      body: content.length > 50 ? content.substring(0, 50) + '...' : content,
      tag: 'idea-captured'
    })
  },
  
  showProposalReady(title: string) {
    return this.show('Proposal Ready', {
      body: title,
      tag: 'proposal-ready'
    })
  }
}

// Declare global types for TypeScript
declare global {
  interface Window {
    dreamcatcherSpeechRecognition?: any
    SpeechRecognition?: any
    webkitSpeechRecognition?: any
  }
}