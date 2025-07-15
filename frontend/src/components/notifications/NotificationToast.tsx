import { useEffect, useState } from 'react'
import { X, CheckCircle, AlertCircle, AlertTriangle, Info } from 'lucide-react'
import { Notification } from '../../stores/notificationStore'

interface NotificationToastProps {
  notification: Notification
  onDismiss: (id: string) => void
}

const NotificationToast = ({ notification, onDismiss }: NotificationToastProps) => {
  const [isVisible, setIsVisible] = useState(true)
  const [isLeaving, setIsLeaving] = useState(false)

  useEffect(() => {
    if (notification.duration) {
      const timer = setTimeout(() => {
        handleDismiss()
      }, notification.duration)
      return () => clearTimeout(timer)
    }
  }, [notification.duration])

  const handleDismiss = () => {
    setIsLeaving(true)
    setTimeout(() => {
      onDismiss(notification.id)
    }, 300)
  }

  const getIcon = () => {
    switch (notification.type) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-400" />
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-400" />
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-yellow-400" />
      case 'info':
        return <Info className="w-5 h-5 text-blue-400" />
      default:
        return <Info className="w-5 h-5 text-blue-400" />
    }
  }

  const getColors = () => {
    switch (notification.type) {
      case 'success':
        return 'bg-green-600/20 border-green-600/30 text-green-300'
      case 'error':
        return 'bg-red-600/20 border-red-600/30 text-red-300'
      case 'warning':
        return 'bg-yellow-600/20 border-yellow-600/30 text-yellow-300'
      case 'info':
        return 'bg-blue-600/20 border-blue-600/30 text-blue-300'
      default:
        return 'bg-blue-600/20 border-blue-600/30 text-blue-300'
    }
  }

  if (!isVisible) return null

  return (
    <div
      className={`flex items-start p-4 mb-3 rounded-lg border ${getColors()} transform transition-all duration-300 ${
        isLeaving ? 'translate-x-full opacity-0' : 'translate-x-0 opacity-100'
      }`}
    >
      <div className="flex-shrink-0 mr-3">
        {getIcon()}
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h4 className="text-sm font-medium text-white mb-1">
              {notification.title}
            </h4>
            <p className="text-sm text-dark-200">
              {notification.message}
            </p>
            
            {notification.source && (
              <p className="text-xs text-dark-400 mt-1">
                From: {notification.source}
              </p>
            )}
            
            {notification.action && (
              <button
                onClick={notification.action.onClick}
                className="mt-2 text-sm text-primary-400 hover:text-primary-300 font-medium"
              >
                {notification.action.label}
              </button>
            )}
          </div>
          
          {notification.dismissible && (
            <button
              onClick={handleDismiss}
              className="ml-2 text-dark-400 hover:text-white transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default NotificationToast