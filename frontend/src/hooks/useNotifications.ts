import { useEffect } from 'react'
import { useNotificationStore } from '../stores/notificationStore'
import { useWebSocketStore } from '../stores/webSocketStore'
import { useAppStore } from '../stores/appStore'

export const useNotifications = () => {
  const { 
    success, 
    error, 
    warning, 
    info,
    addNotification,
    settings: notificationSettings 
  } = useNotificationStore()
  
  const { lastMessage } = useWebSocketStore()
  const { settings: appSettings } = useAppStore()

  // Handle WebSocket notifications
  useEffect(() => {
    if (!lastMessage || !appSettings.notifications) return

    try {
      const message = JSON.parse(lastMessage)
      
      switch (message.type) {
        case 'idea_created':
          success(
            'New Idea Captured',
            `Your idea has been captured and is being processed by the agents.`,
            {
              source: 'Listener Agent',
              action: {
                label: 'View Idea',
                onClick: () => window.location.href = `/ideas/${message.data.id}`
              }
            }
          )
          break

        case 'idea_expanded':
          info(
            'Idea Expanded',
            `Your idea "${message.data.title}" has been expanded with new perspectives.`,
            {
              source: 'Expander Agent',
              action: {
                label: 'View Expansion',
                onClick: () => window.location.href = `/ideas/${message.data.id}`
              }
            }
          )
          break

        case 'proposal_generated':
          success(
            'Proposal Ready',
            `A new proposal has been generated for your idea: "${message.data.title}"`,
            {
              source: 'Proposer Agent',
              action: {
                label: 'View Proposal',
                onClick: () => window.location.href = `/proposals/${message.data.id}`
              }
            }
          )
          break

        case 'visual_generated':
          info(
            'Visual Generated',
            `A new visual has been created for your idea.`,
            {
              source: 'Visualizer Agent',
              action: {
                label: 'View Visual',
                onClick: () => window.location.href = `/ideas/${message.data.idea_id}`
              }
            }
          )
          break

        case 'agent_error':
          error(
            'Agent Error',
            `${message.data.agent} encountered an error: ${message.data.error}`,
            {
              source: message.data.agent,
              dismissible: true
            }
          )
          break

        case 'system_evolution':
          info(
            'System Evolution',
            `The system has evolved: ${message.data.improvement}`,
            {
              source: 'Meta Agent',
              dismissible: true
            }
          )
          break

        case 'health_warning':
          warning(
            'System Health Warning',
            `System health has dropped to ${message.data.health_score}%. Evolution may be triggered.`,
            {
              source: 'Health Monitor',
              action: {
                label: 'View Status',
                onClick: () => window.location.href = '/stats'
              }
            }
          )
          break

        case 'sync_complete':
          if (message.data.count > 0) {
            success(
              'Sync Complete',
              `${message.data.count} ideas have been synchronized.`,
              {
                source: 'Sync Service',
                duration: 3000
              }
            )
          }
          break

        case 'backup_complete':
          success(
            'Backup Complete',
            'Your ideas have been backed up successfully.',
            {
              source: 'Backup Service',
              duration: 2000
            }
          )
          break

        default:
          // Generic message handling
          if (message.notification) {
            addNotification({
              type: message.notification.type || 'info',
              title: message.notification.title || 'System Update',
              message: message.notification.message || 'A system event occurred',
              source: message.notification.source || 'System'
            })
          }
          break
      }
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error)
    }
  }, [lastMessage, appSettings.notifications])

  // System status notifications
  const notifyIdeaCreated = (idea: any) => {
    success(
      'Idea Captured',
      `Your ${idea.source_type} idea has been captured and is being processed.`,
      {
        source: 'Listener Agent',
        action: {
          label: 'View Idea',
          onClick: () => window.location.href = `/ideas/${idea.id}`
        }
      }
    )
  }

  const notifyError = (title: string, message: string, source?: string) => {
    error(title, message, { source })
  }

  const notifySuccess = (title: string, message: string, source?: string) => {
    success(title, message, { source })
  }

  const notifyWarning = (title: string, message: string, source?: string) => {
    warning(title, message, { source })
  }

  const notifyInfo = (title: string, message: string, source?: string) => {
    info(title, message, { source })
  }

  return {
    notifyIdeaCreated,
    notifyError,
    notifySuccess,
    notifyWarning,
    notifyInfo
  }
}