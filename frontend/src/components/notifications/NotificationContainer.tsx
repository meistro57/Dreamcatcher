import { useNotificationStore } from '../../stores/notificationStore'
import NotificationToast from './NotificationToast'

const NotificationContainer = () => {
  const { notifications, dismissNotification } = useNotificationStore()

  // Show only the most recent 5 notifications as toasts
  const recentNotifications = notifications.slice(0, 5)

  return (
    <div className="fixed top-4 right-4 z-50 w-80 max-w-sm">
      {recentNotifications.map((notification) => (
        <NotificationToast
          key={notification.id}
          notification={notification}
          onDismiss={dismissNotification}
        />
      ))}
    </div>
  )
}

export default NotificationContainer