import { useState } from 'react'
import { 
  Bell, 
  X, 
  CheckCircle, 
  AlertCircle, 
  AlertTriangle, 
  Info, 
  Trash2, 
  MarkAsUnread,
  Settings,
  Filter
} from 'lucide-react'
import { useNotificationStore } from '../../stores/notificationStore'
import { formatDistanceToNow } from 'date-fns'

const NotificationPanel = () => {
  const {
    notifications,
    unreadCount,
    isNotificationPanelOpen,
    toggleNotificationPanel,
    markAsRead,
    markAllAsRead,
    dismissNotification,
    clearAllNotifications
  } = useNotificationStore()

  const [filter, setFilter] = useState<'all' | 'unread' | 'success' | 'error' | 'warning' | 'info'>('all')

  const filteredNotifications = notifications.filter(notification => {
    if (filter === 'all') return true
    if (filter === 'unread') return !notification.read
    return notification.type === filter
  })

  const getIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-400" />
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-400" />
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-400" />
      case 'info':
        return <Info className="w-4 h-4 text-blue-400" />
      default:
        return <Info className="w-4 h-4 text-blue-400" />
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'success':
        return 'text-green-400'
      case 'error':
        return 'text-red-400'
      case 'warning':
        return 'text-yellow-400'
      case 'info':
        return 'text-blue-400'
      default:
        return 'text-blue-400'
    }
  }

  if (!isNotificationPanelOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-end bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-md h-full bg-dark-800 border-l border-dark-700 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-dark-700">
          <div className="flex items-center space-x-2">
            <Bell className="w-5 h-5 text-primary-400" />
            <h2 className="text-lg font-semibold text-white">Notifications</h2>
            {unreadCount > 0 && (
              <span className="bg-primary-600 text-white text-xs px-2 py-1 rounded-full">
                {unreadCount}
              </span>
            )}
          </div>
          <button
            onClick={toggleNotificationPanel}
            className="text-dark-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center space-x-1 p-4 border-b border-dark-700">
          <Filter className="w-4 h-4 text-dark-400 mr-2" />
          {['all', 'unread', 'success', 'error', 'warning', 'info'].map((filterType) => (
            <button
              key={filterType}
              onClick={() => setFilter(filterType as any)}
              className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                filter === filterType
                  ? 'bg-primary-600 text-white'
                  : 'text-dark-400 hover:text-white hover:bg-dark-700'
              }`}
            >
              {filterType === 'all' ? 'All' : filterType.charAt(0).toUpperCase() + filterType.slice(1)}
            </button>
          ))}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between p-4 border-b border-dark-700">
          <div className="flex items-center space-x-2">
            <button
              onClick={markAllAsRead}
              disabled={unreadCount === 0}
              className="text-sm text-primary-400 hover:text-primary-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Mark all read
            </button>
            <span className="text-dark-600">•</span>
            <button
              onClick={clearAllNotifications}
              disabled={notifications.length === 0}
              className="text-sm text-red-400 hover:text-red-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Clear all
            </button>
          </div>
          <div className="text-sm text-dark-400">
            {filteredNotifications.length} of {notifications.length}
          </div>
        </div>

        {/* Notifications List */}
        <div className="flex-1 overflow-y-auto">
          {filteredNotifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64">
              <Bell className="w-12 h-12 text-dark-600 mb-4" />
              <p className="text-dark-400 text-center">
                {filter === 'all' 
                  ? 'No notifications yet'
                  : `No ${filter} notifications`
                }
              </p>
            </div>
          ) : (
            <div className="space-y-1">
              {filteredNotifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-4 border-l-4 hover:bg-dark-700 transition-colors cursor-pointer ${
                    notification.read 
                      ? 'border-dark-600 bg-dark-800' 
                      : 'border-primary-500 bg-primary-600/5'
                  }`}
                  onClick={() => markAsRead(notification.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3 flex-1">
                      {getIcon(notification.type)}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <h4 className={`text-sm font-medium ${
                            notification.read ? 'text-dark-200' : 'text-white'
                          }`}>
                            {notification.title}
                          </h4>
                          {!notification.read && (
                            <div className="w-2 h-2 bg-primary-500 rounded-full ml-2" />
                          )}
                        </div>
                        <p className={`text-sm mt-1 ${
                          notification.read ? 'text-dark-400' : 'text-dark-200'
                        }`}>
                          {notification.message}
                        </p>
                        <div className="flex items-center justify-between mt-2">
                          <div className="flex items-center space-x-2 text-xs text-dark-500">
                            <span className={getTypeColor(notification.type)}>
                              {notification.type.toUpperCase()}
                            </span>
                            <span>•</span>
                            <span>
                              {formatDistanceToNow(new Date(notification.timestamp), { addSuffix: true })}
                            </span>
                            {notification.source && (
                              <>
                                <span>•</span>
                                <span>{notification.source}</span>
                              </>
                            )}
                          </div>
                          {notification.dismissible && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                dismissNotification(notification.id)
                              }}
                              className="text-dark-500 hover:text-red-400 transition-colors"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          )}
                        </div>
                        {notification.action && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              notification.action!.onClick()
                            }}
                            className="mt-2 text-sm text-primary-400 hover:text-primary-300 font-medium"
                          >
                            {notification.action.label}
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default NotificationPanel