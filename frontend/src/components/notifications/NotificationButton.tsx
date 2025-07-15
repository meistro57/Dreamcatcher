import { Bell } from 'lucide-react'
import { useNotificationStore } from '../../stores/notificationStore'

const NotificationButton = () => {
  const { 
    unreadCount, 
    toggleNotificationPanel, 
    isNotificationPanelOpen 
  } = useNotificationStore()

  return (
    <button
      onClick={toggleNotificationPanel}
      className={`relative p-2 rounded-lg transition-colors ${
        isNotificationPanelOpen 
          ? 'bg-primary-600 text-white' 
          : 'text-dark-400 hover:text-white hover:bg-dark-800'
      }`}
      title="Notifications"
    >
      <Bell className="w-5 h-5" />
      {unreadCount > 0 && (
        <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-medium">
          {unreadCount > 99 ? '99+' : unreadCount}
        </span>
      )}
    </button>
  )
}

export default NotificationButton