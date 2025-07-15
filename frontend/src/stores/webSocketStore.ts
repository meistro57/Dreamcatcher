import { create } from 'zustand'

interface WebSocketMessage {
  type: string
  data?: any
  timestamp: string
}

interface WebSocketState {
  isConnected: boolean
  lastMessage: WebSocketMessage | null
  reconnectAttempts: number
  socket: WebSocket | null
  
  // Actions
  connect: () => void
  disconnect: () => void
  sendMessage: (message: any) => void
  onMessage: (callback: (message: WebSocketMessage) => void) => void
}

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/ws'
const MAX_RECONNECT_ATTEMPTS = 5
const RECONNECT_DELAY = 3000

export const useWebSocketStore = create<WebSocketState>((set, get) => ({
  isConnected: false,
  lastMessage: null,
  reconnectAttempts: 0,
  socket: null,

  connect: () => {
    const { socket, reconnectAttempts } = get()
    
    if (socket?.readyState === WebSocket.OPEN) {
      return
    }

    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      console.error('Max WebSocket reconnection attempts reached')
      return
    }

    try {
      const ws = new WebSocket(WS_URL)
      
      ws.onopen = () => {
        console.log('WebSocket connected')
        set({ 
          isConnected: true, 
          socket: ws,
          reconnectAttempts: 0
        })
      }

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          set({ lastMessage: message })
          
          // Trigger any registered callbacks
          const callbacks = get().messageCallbacks || []
          callbacks.forEach(callback => callback(message))
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.onclose = () => {
        console.log('WebSocket disconnected')
        set({ isConnected: false, socket: null })
        
        // Attempt to reconnect
        const currentAttempts = get().reconnectAttempts
        if (currentAttempts < MAX_RECONNECT_ATTEMPTS) {
          setTimeout(() => {
            set({ reconnectAttempts: currentAttempts + 1 })
            get().connect()
          }, RECONNECT_DELAY)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        set({ isConnected: false })
      }

      set({ socket: ws })
      
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      set({ isConnected: false })
    }
  },

  disconnect: () => {
    const { socket } = get()
    if (socket) {
      socket.close()
      set({ socket: null, isConnected: false })
    }
  },

  sendMessage: (message: any) => {
    const { socket, isConnected } = get()
    if (socket && isConnected) {
      socket.send(JSON.stringify(message))
    } else {
      console.warn('Cannot send message: WebSocket not connected')
    }
  },

  onMessage: (callback: (message: WebSocketMessage) => void) => {
    // Store callback for message handling
    // In a real implementation, you'd manage these callbacks properly
    const state = get() as any
    if (!state.messageCallbacks) {
      state.messageCallbacks = []
    }
    state.messageCallbacks.push(callback)
  }
}))

// Custom hook for WebSocket messages
export const useWebSocketMessage = (messageType: string, callback: (data: any) => void) => {
  const { lastMessage } = useWebSocketStore()
  
  if (lastMessage && lastMessage.type === messageType) {
    callback(lastMessage.data)
  }
}