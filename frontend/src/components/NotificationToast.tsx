import { useEffect, useState } from 'react'
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react'
import { useWebSocketStore } from '../stores/webSocketStore'

interface Toast {
  id: string
  type: 'success' | 'error' | 'info' | 'warning'
  title: string
  message: string
  duration?: number
}

const NotificationToast = () => {
  const [toasts, setToasts] = useState<Toast[]>([])
  const { lastMessage } = useWebSocketStore()
  
  useEffect(() => {
    if (lastMessage) {
      handleWebSocketMessage(lastMessage)
    }
  }, [lastMessage])
  
  const handleWebSocketMessage = (message: any) => {
    switch (message.type) {
      case 'idea_captured':
        addToast({
          type: 'success',
          title: 'Idea Captured',
          message: `${message.source} idea saved successfully`,
          duration: 3000
        })
        break
        
      case 'proposal_generated':
        addToast({
          type: 'info',
          title: 'Proposal Ready',
          message: message.title,
          duration: 5000
        })
        break
        
      case 'agent_status':
        if (message.status === 'error') {
          addToast({
            type: 'error',
            title: 'Agent Error',
            message: message.message,
            duration: 5000
          })
        }
        break
        
      case 'system_alert':
        addToast({
          type: message.severity || 'info',
          title: 'System Alert',
          message: message.message,
          duration: 4000
        })
        break
    }
  }
  
  const addToast = (toast: Omit<Toast, 'id'>) => {
    const id = Date.now().toString()
    const newToast: Toast = { ...toast, id }
    
    setToasts(prev => [...prev, newToast])
    
    // Auto-remove toast
    setTimeout(() => {
      removeToast(id)
    }, toast.duration || 4000)
  }
  
  const removeToast = (id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id))
  }
  
  const getToastConfig = (type: Toast['type']) => {
    switch (type) {
      case 'success':
        return {
          icon: CheckCircle,
          bgColor: 'bg-green-600',
          textColor: 'text-green-100',
          borderColor: 'border-green-500'
        }
      case 'error':
        return {
          icon: AlertCircle,
          bgColor: 'bg-red-600',
          textColor: 'text-red-100',
          borderColor: 'border-red-500'
        }
      case 'warning':
        return {
          icon: AlertTriangle,
          bgColor: 'bg-yellow-600',
          textColor: 'text-yellow-100',
          borderColor: 'border-yellow-500'
        }
      case 'info':
      default:
        return {
          icon: Info,
          bgColor: 'bg-blue-600',
          textColor: 'text-blue-100',
          borderColor: 'border-blue-500'
        }
    }
  }
  
  if (toasts.length === 0) {
    return null
  }
  
  return (
    <div className="fixed bottom-20 right-4 z-50 space-y-2">
      {toasts.map(toast => {
        const { icon: Icon, bgColor, textColor, borderColor } = getToastConfig(toast.type)
        
        return (
          <div
            key={toast.id}
            className={`
              ${bgColor} ${textColor} border ${borderColor}
              rounded-lg p-4 shadow-xl backdrop-blur-sm
              max-w-sm animate-slide-up
            `}
          >
            <div className="flex items-start space-x-3">
              <Icon className="w-5 h-5 mt-0.5 flex-shrink-0" />
              
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm">{toast.title}</p>
                <p className="text-sm opacity-90 mt-1">{toast.message}</p>
              </div>
              
              <button
                onClick={() => removeToast(toast.id)}
                className="flex-shrink-0 text-current opacity-70 hover:opacity-100 transition-opacity"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default NotificationToast