import { useEffect, useState } from 'react'
import { Wifi, WifiOff, Zap, AlertCircle } from 'lucide-react'
import { useAppStore } from '../stores/appStore'
import { useWebSocketStore } from '../stores/webSocketStore'

const ConnectionStatus = () => {
  const { isOnline } = useAppStore()
  const { isConnected } = useWebSocketStore()
  const [showStatus, setShowStatus] = useState(false)
  
  useEffect(() => {
    // Show status when connection changes
    const timer = setTimeout(() => {
      setShowStatus(false)
    }, 3000)
    
    setShowStatus(true)
    
    return () => clearTimeout(timer)
  }, [isOnline, isConnected])
  
  // Don't show if everything is connected
  if (isOnline && isConnected && !showStatus) {
    return null
  }
  
  const getStatusConfig = () => {
    if (!isOnline) {
      return {
        icon: WifiOff,
        text: 'Offline Mode',
        bgColor: 'bg-yellow-600',
        textColor: 'text-yellow-100'
      }
    }
    
    if (!isConnected) {
      return {
        icon: AlertCircle,
        text: 'Reconnecting...',
        bgColor: 'bg-orange-600',
        textColor: 'text-orange-100'
      }
    }
    
    return {
      icon: Zap,
      text: 'Connected',
      bgColor: 'bg-green-600',
      textColor: 'text-green-100'
    }
  }
  
  const { icon: Icon, text, bgColor, textColor } = getStatusConfig()
  
  return (
    <div className={`
      fixed top-4 left-1/2 transform -translate-x-1/2 z-50
      ${bgColor} ${textColor}
      px-4 py-2 rounded-full
      shadow-lg backdrop-blur-sm
      transition-all duration-300
      ${showStatus ? 'translate-y-0 opacity-100' : '-translate-y-full opacity-0'}
    `}>
      <div className="flex items-center space-x-2">
        <Icon className="w-4 h-4" />
        <span className="text-sm font-medium">{text}</span>
      </div>
    </div>
  )
}

export default ConnectionStatus