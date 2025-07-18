import { useState } from 'react'
import { 
  Settings, 
  Mic, 
  Bell, 
  Moon, 
  Wifi,
  Database,
  Zap,
  Save,
  RefreshCw,
  User
} from 'lucide-react'
import { useAppStore } from '../stores/appStore'
import { useAuthStore } from '../stores/authStore'
import { useNotificationStore, requestNotificationPermission } from '../stores/notificationStore'
import UserProfile from '../components/user/UserProfile'

const SettingsPage = () => {
  const { settings, updateSettings } = useAppStore()
  const { user } = useAuthStore()
  const { 
    settings: notificationSettings, 
    updateSettings: updateNotificationSettings,
    clearAllNotifications,
    notifications
  } = useNotificationStore()
  const [isSaving, setIsSaving] = useState(false)
  const [activeTab, setActiveTab] = useState<'profile' | 'voice' | 'notifications' | 'offline' | 'system'>('profile')
  
  const handleSave = async () => {
    setIsSaving(true)
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    setIsSaving(false)
    
    // Show success message
    alert('Settings saved successfully!')
  }
  
  const handleReset = () => {
    if (confirm('Are you sure you want to reset all settings to default?')) {
      updateSettings({
        autoCapture: false,
        voiceWakeWord: 'hey dreamcatcher',
        defaultUrgency: 'normal',
        notifications: true,
        offlineMode: true,
        compressionLevel: 0.8
      })
    }
  }
  
  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'voice', label: 'Voice', icon: Mic },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'offline', label: 'Offline', icon: Wifi },
    { id: 'system', label: 'System', icon: Database }
  ]

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Settings</h1>
            <p className="text-gray-600 dark:text-gray-400">
              Configure your Dreamcatcher experience
            </p>
          </div>
          
          {activeTab !== 'profile' && (
            <div className="flex space-x-2">
              <button
                onClick={handleReset}
                className="flex items-center space-x-2 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Reset</span>
              </button>
              
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Save className="w-4 h-4" />
                <span>{isSaving ? 'Saving...' : 'Save'}</span>
              </button>
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="mb-8">
          <nav className="flex space-x-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors ${
                    activeTab === tab.id
                      ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="font-medium">{tab.label}</span>
                </button>
              )
            })}
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'profile' && (
          <UserProfile />
        )}
        
        {activeTab === 'voice' && (
          <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg p-8">
            <div className="flex items-center space-x-3 mb-6">
              <Mic className="w-6 h-6 text-blue-500" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Voice Capture</h2>
            </div>
          
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-gray-900 dark:text-white font-medium mb-1">Auto-capture</h3>
                  <p className="text-gray-600 dark:text-gray-400 text-sm">
                    Automatically start recording when wake word is detected
                  </p>
                </div>
                <button
                  onClick={() => updateSettings({ autoCapture: !settings.autoCapture })}
                  className={`w-12 h-6 rounded-full transition-colors ${
                    settings.autoCapture ? 'bg-blue-600' : 'bg-gray-300 dark:bg-gray-600'
                  }`}
                >
                  <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                    settings.autoCapture ? 'translate-x-6' : 'translate-x-0.5'
                  }`} />
                </button>
              </div>
            
            <div>
              <label className="block text-white font-medium mb-2">
                Wake Word
              </label>
              <input
                type="text"
                value={settings.voiceWakeWord}
                onChange={(e) => updateSettings({ voiceWakeWord: e.target.value })}
                className="input w-full max-w-md"
                placeholder="hey dreamcatcher"
              />
              <p className="text-dark-400 text-sm mt-1">
                Phrase to trigger voice recording
              </p>
            </div>
            
            <div>
              <label className="block text-white font-medium mb-2">
                Default Urgency
              </label>
              <select
                value={settings.defaultUrgency}
                onChange={(e) => updateSettings({ defaultUrgency: e.target.value })}
                className="input w-full max-w-md"
              >
                <option value="low">Low</option>
                <option value="normal">Normal</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
              <p className="text-dark-400 text-sm mt-1">
                Default urgency level for new ideas
              </p>
            </div>
          </div>
        </div>
        )}
        
        {activeTab === 'notifications' && (
          <div className="space-y-8">
            {/* Notification Settings */}
            <div className="card p-8">
              <div className="flex items-center space-x-3 mb-6">
                <Bell className="w-6 h-6 text-primary-500" />
                <h2 className="text-xl font-semibold text-white">Notification Settings</h2>
              </div>
              
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-white font-medium mb-1">Enable Notifications</h3>
                    <p className="text-dark-400 text-sm">
                      Receive notifications for new proposals and system updates
                    </p>
                  </div>
                  <button
                    onClick={() => updateNotificationSettings({ enabled: !notificationSettings.enabled })}
                    className={`w-12 h-6 rounded-full transition-colors ${
                      notificationSettings.enabled ? 'bg-primary-600' : 'bg-dark-600'
                    }`}
                  >
                    <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                      notificationSettings.enabled ? 'translate-x-6' : 'translate-x-0.5'
                    }`} />
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-white font-medium mb-1">Sound Notifications</h3>
                    <p className="text-dark-400 text-sm">
                      Play a sound when new notifications arrive
                    </p>
                  </div>
                  <button
                    onClick={() => updateNotificationSettings({ sound: !notificationSettings.sound })}
                    className={`w-12 h-6 rounded-full transition-colors ${
                      notificationSettings.sound ? 'bg-primary-600' : 'bg-dark-600'
                    }`}
                  >
                    <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                      notificationSettings.sound ? 'translate-x-6' : 'translate-x-0.5'
                    }`} />
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-white font-medium mb-1">Desktop Notifications</h3>
                    <p className="text-dark-400 text-sm">
                      Show desktop notifications even when the app is not active
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={async () => {
                        if (notificationSettings.desktop) {
                          updateNotificationSettings({ desktop: false })
                        } else {
                          const granted = await requestNotificationPermission()
                          if (granted) {
                            updateNotificationSettings({ desktop: true })
                          }
                        }
                      }}
                      className={`w-12 h-6 rounded-full transition-colors ${
                        notificationSettings.desktop ? 'bg-primary-600' : 'bg-dark-600'
                      }`}
                    >
                      <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                        notificationSettings.desktop ? 'translate-x-6' : 'translate-x-0.5'
                      }`} />
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Notification Types */}
            <div className="card p-8">
              <h3 className="text-xl font-semibold text-white mb-6">Notification Types</h3>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-4 h-4 bg-green-500 rounded-full"></div>
                    <div>
                      <h4 className="text-white font-medium">Success Notifications</h4>
                      <p className="text-dark-400 text-sm">Ideas captured, proposals generated, sync complete</p>
                    </div>
                  </div>
                  <button
                    onClick={() => updateNotificationSettings({ 
                      types: { ...notificationSettings.types, success: !notificationSettings.types.success }
                    })}
                    className={`w-12 h-6 rounded-full transition-colors ${
                      notificationSettings.types.success ? 'bg-green-600' : 'bg-dark-600'
                    }`}
                  >
                    <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                      notificationSettings.types.success ? 'translate-x-6' : 'translate-x-0.5'
                    }`} />
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-4 h-4 bg-red-500 rounded-full"></div>
                    <div>
                      <h4 className="text-white font-medium">Error Notifications</h4>
                      <p className="text-dark-400 text-sm">Agent errors, system failures, sync issues</p>
                    </div>
                  </div>
                  <button
                    onClick={() => updateNotificationSettings({ 
                      types: { ...notificationSettings.types, error: !notificationSettings.types.error }
                    })}
                    className={`w-12 h-6 rounded-full transition-colors ${
                      notificationSettings.types.error ? 'bg-red-600' : 'bg-dark-600'
                    }`}
                  >
                    <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                      notificationSettings.types.error ? 'translate-x-6' : 'translate-x-0.5'
                    }`} />
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-4 h-4 bg-yellow-500 rounded-full"></div>
                    <div>
                      <h4 className="text-white font-medium">Warning Notifications</h4>
                      <p className="text-dark-400 text-sm">System health warnings, capacity limits</p>
                    </div>
                  </div>
                  <button
                    onClick={() => updateNotificationSettings({ 
                      types: { ...notificationSettings.types, warning: !notificationSettings.types.warning }
                    })}
                    className={`w-12 h-6 rounded-full transition-colors ${
                      notificationSettings.types.warning ? 'bg-yellow-600' : 'bg-dark-600'
                    }`}
                  >
                    <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                      notificationSettings.types.warning ? 'translate-x-6' : 'translate-x-0.5'
                    }`} />
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-4 h-4 bg-blue-500 rounded-full"></div>
                    <div>
                      <h4 className="text-white font-medium">Info Notifications</h4>
                      <p className="text-dark-400 text-sm">Idea expansions, visual generation, system evolution</p>
                    </div>
                  </div>
                  <button
                    onClick={() => updateNotificationSettings({ 
                      types: { ...notificationSettings.types, info: !notificationSettings.types.info }
                    })}
                    className={`w-12 h-6 rounded-full transition-colors ${
                      notificationSettings.types.info ? 'bg-blue-600' : 'bg-dark-600'
                    }`}
                  >
                    <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                      notificationSettings.types.info ? 'translate-x-6' : 'translate-x-0.5'
                    }`} />
                  </button>
                </div>
              </div>
            </div>

            {/* Notification History */}
            <div className="card p-8">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-white">Notification History</h3>
                <button
                  onClick={clearAllNotifications}
                  className="btn btn-danger btn-sm"
                >
                  Clear All
                </button>
              </div>
              
              <div className="text-sm text-dark-400 mb-4">
                {notifications.length} total notifications
              </div>
              
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {notifications.slice(0, 10).map((notification) => (
                  <div key={notification.id} className="p-3 bg-dark-700 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <div className={`w-2 h-2 rounded-full ${
                          notification.type === 'success' ? 'bg-green-500' :
                          notification.type === 'error' ? 'bg-red-500' :
                          notification.type === 'warning' ? 'bg-yellow-500' :
                          'bg-blue-500'
                        }`} />
                        <span className="text-white font-medium">{notification.title}</span>
                      </div>
                      <span className="text-dark-400 text-xs">
                        {new Date(notification.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-dark-300 text-sm mt-1">{notification.message}</p>
                  </div>
                ))}
                {notifications.length === 0 && (
                  <div className="text-center py-8 text-dark-400">
                    No notifications yet
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
        
        {activeTab === 'offline' && (
          <div className="card p-8">
            <div className="flex items-center space-x-3 mb-6">
              <Wifi className="w-6 h-6 text-primary-500" />
              <h2 className="text-xl font-semibold text-white">Offline Mode</h2>
            </div>
            
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-white font-medium mb-1">Enable Offline Mode</h3>
                  <p className="text-dark-400 text-sm">
                    Continue capturing ideas when internet is unavailable
                  </p>
                </div>
                <button
                  onClick={() => updateSettings({ offlineMode: !settings.offlineMode })}
                  className={`w-12 h-6 rounded-full transition-colors ${
                    settings.offlineMode ? 'bg-primary-600' : 'bg-dark-600'
                  }`}
                >
                  <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                    settings.offlineMode ? 'translate-x-6' : 'translate-x-0.5'
                  }`} />
                </button>
              </div>
              
              <div>
                <label className="block text-white font-medium mb-2">
                  Compression Level: {Math.round(settings.compressionLevel * 100)}%
                </label>
                <input
                  type="range"
                  min="0.1"
                  max="1"
                  step="0.1"
                  value={settings.compressionLevel}
                  onChange={(e) => updateSettings({ compressionLevel: Number(e.target.value) })}
                  className="w-full max-w-md"
                />
                <p className="text-dark-400 text-sm mt-1">
                  Audio compression level for offline storage
                </p>
              </div>
            </div>
          </div>
        )}
        
        {activeTab === 'system' && (
          <div className="card p-8">
            <div className="flex items-center space-x-3 mb-6">
              <Database className="w-6 h-6 text-primary-500" />
              <h2 className="text-xl font-semibold text-white">System Information</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-white font-medium mb-3">Storage</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-dark-300">Ideas cached</span>
                    <span className="text-white">127</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-dark-300">Audio files</span>
                    <span className="text-white">45</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-dark-300">Storage used</span>
                    <span className="text-white">24.5 MB</span>
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className="text-white font-medium mb-3">Performance</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-dark-300">Sync status</span>
                    <span className="text-green-400">Connected</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-dark-300">Last sync</span>
                    <span className="text-white">2 minutes ago</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-dark-300">Pending sync</span>
                    <span className="text-white">0 items</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="mt-6 pt-6 border-t border-dark-600">
              <button className="btn btn-secondary mr-4">
                Clear Cache
              </button>
              <button className="btn btn-secondary mr-4">
                Export Data
              </button>
              <button className="btn btn-danger">
                Reset All Data
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default SettingsPage