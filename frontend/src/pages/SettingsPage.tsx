import { useEffect, useState } from 'react'
import { 
  Mic, 
  MicOff,
  Bell, 
  Wifi,
  Database,
  Zap,
  Save,
  RefreshCw,
  User,
  Search,
  Bot,
  KeyRound
} from 'lucide-react'
import { useAppStore } from '../stores/appStore'
import { useAuthStore } from '../stores/authStore'
import { useNotificationStore, requestNotificationPermission } from '../stores/notificationStore'
import UserProfile from '../components/user/UserProfile'
import { api } from '../utils/api'

const SettingsPage = () => {
  const { settings, updateSettings } = useAppStore()
  const { user } = useAuthStore()
  const voiceCaptureEnabled = settings.voiceCaptureEnabled !== false
  const isAdmin = Boolean(user?.roles?.includes('admin'))
  const { 
    settings: notificationSettings, 
    updateSettings: updateNotificationSettings,
    clearAllNotifications,
    notifications
  } = useNotificationStore()
  const [isSaving, setIsSaving] = useState(false)
  const [activeTab, setActiveTab] = useState<'profile' | 'voice' | 'notifications' | 'offline' | 'system'>('profile')
  const [agentsLoading, setAgentsLoading] = useState(false)
  const [agentsError, setAgentsError] = useState<string | null>(null)
  const [agents, setAgents] = useState<any[]>([])
  const [logStatsLoading, setLogStatsLoading] = useState(false)
  const [logStatsError, setLogStatsError] = useState<string | null>(null)
  const [logStats, setLogStats] = useState<any | null>(null)
  const [logQuery, setLogQuery] = useState('')
  const [logThreshold, setLogThreshold] = useState(0.4)
  const [logLimit, setLogLimit] = useState(20)
  const [logSearchLoading, setLogSearchLoading] = useState(false)
  const [logSearchError, setLogSearchError] = useState<string | null>(null)
  const [logSearchResults, setLogSearchResults] = useState<any[]>([])
  const [logBackfillLoading, setLogBackfillLoading] = useState(false)
  const [recentLogsLoading, setRecentLogsLoading] = useState(false)
  const [recentLogsError, setRecentLogsError] = useState<string | null>(null)
  const [recentLogs, setRecentLogs] = useState<any[]>([])
  const [expandedLogIds, setExpandedLogIds] = useState<Record<string, boolean>>({})
  const [logsHours, setLogsHours] = useState(24)
  const [logsLimit, setLogsLimit] = useState(50)
  const [logsStatus, setLogsStatus] = useState('')
  const [systemActionsLoading, setSystemActionsLoading] = useState(false)
  const [systemActionsError, setSystemActionsError] = useState<string | null>(null)
  const [systemActionsEnabled, setSystemActionsEnabled] = useState(false)
  const [systemActions, setSystemActions] = useState<string[]>([])
  const [runningAction, setRunningAction] = useState<string | null>(null)
  const [actionOutput, setActionOutput] = useState<string>('')
  const [apiKeysLoading, setApiKeysLoading] = useState(false)
  const [apiKeysSaving, setApiKeysSaving] = useState(false)
  const [apiKeysError, setApiKeysError] = useState<string | null>(null)
  const [apiKeysSuccess, setApiKeysSuccess] = useState<string | null>(null)
  const [apiKeyStatus, setApiKeyStatus] = useState<{
    anthropic_configured: boolean
    openai_configured: boolean
    openrouter_configured: boolean
    ai_available: boolean
  } | null>(null)
  const [apiKeyForm, setApiKeyForm] = useState({
    anthropic_api_key: '',
    openai_api_key: '',
    openrouter_api_key: ''
  })
  const [persistApiKeys, setPersistApiKeys] = useState(false)
  const [adminRecoveryLoading, setAdminRecoveryLoading] = useState(false)
  const [adminRecoveryStatus, setAdminRecoveryStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null)
  const [adminUserSearch, setAdminUserSearch] = useState('')
  const [adminSearchResults, setAdminSearchResults] = useState<Array<{ id: string; username: string; email: string; full_name: string }>>([])
  const [adminResetPassword, setAdminResetPassword] = useState('')
  
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
        voiceCaptureEnabled: true,
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

  const loadAgents = async () => {
    setAgentsLoading(true)
    setAgentsError(null)
    try {
      const response = await api.agents.status()
      setAgents(Array.isArray(response.data) ? response.data : [])
    } catch (error: any) {
      setAgentsError(error?.response?.data?.detail || 'Failed to load agents')
    } finally {
      setAgentsLoading(false)
    }
  }

  const loadLogStats = async () => {
    setLogStatsLoading(true)
    setLogStatsError(null)
    try {
      const response = await api.embeddings.logStats()
      setLogStats(response.data?.stats || null)
    } catch (error: any) {
      setLogStatsError(error?.response?.data?.detail || 'Failed to load log embedding stats')
    } finally {
      setLogStatsLoading(false)
    }
  }

  const runLogSearch = async () => {
    if (!logQuery.trim()) {
      setLogSearchError('Enter a search query first')
      return
    }

    setLogSearchLoading(true)
    setLogSearchError(null)
    try {
      const response = await api.logs.semanticSearch({
        query: logQuery,
        threshold: logThreshold,
        limit: logLimit,
      })
      setLogSearchResults(response.data?.results || [])
    } catch (error: any) {
      setLogSearchError(error?.response?.data?.detail || 'Semantic log search failed')
    } finally {
      setLogSearchLoading(false)
    }
  }

  const runLogBackfill = async () => {
    setLogBackfillLoading(true)
    setLogStatsError(null)
    try {
      await api.embeddings.logBatchUpdate(200)
      await loadLogStats()
    } catch (error: any) {
      setLogStatsError(error?.response?.data?.detail || 'Failed to backfill log embeddings')
    } finally {
      setLogBackfillLoading(false)
    }
  }

  const loadRecentLogs = async () => {
    setRecentLogsLoading(true)
    setRecentLogsError(null)
    try {
      const response = await api.logs.list({
        hours: logsHours,
        limit: logsLimit,
        status: logsStatus || undefined,
      })
      setRecentLogs(Array.isArray(response.data?.logs) ? response.data.logs : [])
    } catch (error: any) {
      setRecentLogsError(error?.response?.data?.detail || 'Failed to load logs')
    } finally {
      setRecentLogsLoading(false)
    }
  }

  const toggleLogExpanded = (logId: string) => {
    setExpandedLogIds((prev) => ({
      ...prev,
      [logId]: !prev[logId],
    }))
  }

  const formatJsonForDisplay = (value: any) => {
    if (value == null) return ''
    try {
      return JSON.stringify(value, null, 2)
    } catch {
      return String(value)
    }
  }

  const loadSystemActions = async () => {
    setSystemActionsLoading(true)
    setSystemActionsError(null)
    try {
      const response = await api.system.actionsStatus()
      setSystemActionsEnabled(Boolean(response.data?.enabled))
      setSystemActions(Array.isArray(response.data?.actions) ? response.data.actions : [])
      setActionOutput(response.data?.message || '')
    } catch (error: any) {
      setSystemActionsError(error?.response?.data?.detail || 'Failed to load system actions')
    } finally {
      setSystemActionsLoading(false)
    }
  }

  const loadApiKeyStatus = async () => {
    setApiKeysLoading(true)
    setApiKeysError(null)
    try {
      const response = await api.settings.apiKeysStatus()
      setApiKeyStatus(response.data || null)
    } catch (error: any) {
      setApiKeysError(error?.response?.data?.detail || 'Failed to load API key status')
    } finally {
      setApiKeysLoading(false)
    }
  }

  const saveApiKeys = async () => {
    setApiKeysError(null)
    setApiKeysSuccess(null)

    const payload: Record<string, string> = {}
    if (apiKeyForm.anthropic_api_key.trim()) payload.anthropic_api_key = apiKeyForm.anthropic_api_key.trim()
    if (apiKeyForm.openai_api_key.trim()) payload.openai_api_key = apiKeyForm.openai_api_key.trim()
    if (apiKeyForm.openrouter_api_key.trim()) payload.openrouter_api_key = apiKeyForm.openrouter_api_key.trim()

    if (!Object.keys(payload).length) {
      setApiKeysError('Enter at least one API key to update.')
      return
    }

    setApiKeysSaving(true)
    try {
      const response = await api.settings.updateApiKeys({
        ...payload,
        persist_to_env: persistApiKeys
      })
      const updated = Array.isArray(response.data?.updated) ? response.data.updated.join(', ') : 'keys'
      const persisted = response.data?.persisted_to_env ? ' and persisted to .env' : ''
      setApiKeysSuccess(`Updated runtime keys: ${updated}${persisted}`)
      setApiKeyForm({
        anthropic_api_key: '',
        openai_api_key: '',
        openrouter_api_key: ''
      })
      await loadApiKeyStatus()
    } catch (error: any) {
      setApiKeysError(error?.response?.data?.detail || 'Failed to update API keys')
    } finally {
      setApiKeysSaving(false)
    }
  }

  const runSystemAction = async (action: string) => {
    setRunningAction(action)
    setSystemActionsError(null)
    setActionOutput('')
    try {
      const response = await api.system.runAction(action)
      const steps = Array.isArray(response.data?.steps) ? response.data.steps : []
      const output = steps.map((step: any, index: number) => {
        const stdout = step.stdout ? `stdout:\n${step.stdout}` : 'stdout: <empty>'
        const stderr = step.stderr ? `stderr:\n${step.stderr}` : 'stderr: <empty>'
        return `Step ${index + 1}: ${step.command}\nexit=${step.return_code}\n${stdout}\n${stderr}`
      }).join('\n\n')
      setActionOutput(output || 'Action completed')
      await loadAgents()
      await loadLogStats()
    } catch (error: any) {
      const detail = error?.response?.data?.detail
      if (detail && typeof detail === 'object' && Array.isArray(detail.steps)) {
        const output = detail.steps.map((step: any, index: number) => {
          return `Step ${index + 1}: ${step.command}\nexit=${step.return_code}\n${step.stderr || step.stdout || ''}`
        }).join('\n\n')
        setActionOutput(output)
        setSystemActionsError('Action failed')
      } else {
        setSystemActionsError(detail || 'Failed to run system action')
      }
    } finally {
      setRunningAction(null)
    }
  }

  const searchUsersForRecovery = async () => {
    setAdminRecoveryStatus(null)
    if (!adminUserSearch.trim()) {
      setAdminSearchResults([])
      return
    }
    setAdminRecoveryLoading(true)
    try {
      const response = await api.auth.searchUsers(adminUserSearch.trim(), 20)
      setAdminSearchResults(Array.isArray(response.data) ? response.data : [])
    } catch (error: any) {
      setAdminRecoveryStatus({ type: 'error', message: error?.response?.data?.detail || 'User search failed' })
    } finally {
      setAdminRecoveryLoading(false)
    }
  }

  const unlockRecoveredUser = async (targetUserId: string) => {
    setAdminRecoveryStatus(null)
    setAdminRecoveryLoading(true)
    try {
      await api.auth.unlockUser(targetUserId)
      setAdminRecoveryStatus({ type: 'success', message: 'User unlocked successfully.' })
    } catch (error: any) {
      setAdminRecoveryStatus({ type: 'error', message: error?.response?.data?.detail || 'Failed to unlock user.' })
    } finally {
      setAdminRecoveryLoading(false)
    }
  }

  const resetRecoveredUserPassword = async (targetUserId: string) => {
    setAdminRecoveryStatus(null)
    if (!adminResetPassword.trim()) {
      setAdminRecoveryStatus({ type: 'error', message: 'Enter a new password first.' })
      return
    }
    setAdminRecoveryLoading(true)
    try {
      await api.auth.resetUserPassword(targetUserId, adminResetPassword.trim())
      setAdminRecoveryStatus({ type: 'success', message: 'User password reset successfully.' })
      setAdminResetPassword('')
    } catch (error: any) {
      setAdminRecoveryStatus({ type: 'error', message: error?.response?.data?.detail || 'Failed to reset password.' })
    } finally {
      setAdminRecoveryLoading(false)
    }
  }

  useEffect(() => {
    if (activeTab !== 'system') return
    void loadAgents()
    void loadLogStats()
    void loadSystemActions()
    void loadRecentLogs()
    void loadApiKeyStatus()
  }, [activeTab])

  return (
    <div className="min-h-screen bg-dark-900 mobile-padding">
      <div className="max-w-6xl mx-auto pt-8 pb-24">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Settings</h1>
            <p className="text-dark-300">
              Configure your Dreamcatcher experience
            </p>
          </div>
          
          {activeTab !== 'profile' && (
            <div className="flex space-x-2">
              <button
                onClick={handleReset}
                className="btn btn-secondary flex items-center space-x-2"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Reset</span>
              </button>
              
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="btn btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Save className="w-4 h-4" />
                <span>{isSaving ? 'Saving...' : 'Save'}</span>
              </button>
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="mb-8">
          <nav className="flex flex-wrap gap-2 card p-2">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors ${
                    activeTab === tab.id
                      ? 'bg-primary-600 text-white shadow-sm'
                      : 'text-dark-300 hover:text-white hover:bg-dark-700'
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
          <div className="card p-8">
            <div className="flex items-center space-x-3 mb-6">
              <Mic className="w-6 h-6 text-primary-500" />
              <h2 className="text-xl font-semibold text-white">Voice Capture</h2>
            </div>
          
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-white font-medium mb-1">Enable Voice Input</h3>
                  <p className="text-dark-400 text-sm">
                    Hard disable all microphone capture when turned off
                  </p>
                </div>
                <button
                  onClick={() => updateSettings({ voiceCaptureEnabled: !voiceCaptureEnabled })}
                  className={`w-12 h-6 rounded-full transition-colors ${
                    voiceCaptureEnabled ? 'bg-primary-600' : 'bg-dark-600'
                  }`}
                >
                  <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                    voiceCaptureEnabled ? 'translate-x-6' : 'translate-x-0.5'
                  }`} />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-white font-medium mb-1">Auto-capture</h3>
                  <p className="text-dark-400 text-sm">
                    Automatically start recording when wake word is detected
                  </p>
                </div>
                <button
                  onClick={() => updateSettings({ autoCapture: !settings.autoCapture })}
                  className={`w-12 h-6 rounded-full transition-colors ${
                    settings.autoCapture ? 'bg-primary-600' : 'bg-dark-600'
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

            <div className="pt-4 border-t border-dark-600">
              <h3 className="text-white font-medium mb-2">Voice Processing Notes</h3>
              <ul className="text-dark-300 text-sm space-y-1">
                <li>Microphone permissions are required for voice capture.</li>
                <li>Wake word runs in-browser and may vary by device/browser support.</li>
                <li>Use Offline Mode to retain captures when network drops.</li>
              </ul>
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
          <div className="space-y-6">
            {isAdmin && (
              <div className="card p-8">
                <div className="flex items-center space-x-3 mb-6">
                  <User className="w-6 h-6 text-primary-500" />
                  <h2 className="text-xl font-semibold text-white">User Access Recovery</h2>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
                  <input
                    type="text"
                    value={adminUserSearch}
                    onChange={(e) => setAdminUserSearch(e.target.value)}
                    placeholder="Search username or email"
                    className="input md:col-span-2"
                  />
                  <button onClick={searchUsersForRecovery} disabled={adminRecoveryLoading} className="btn btn-secondary disabled:opacity-50">
                    {adminRecoveryLoading ? 'Searching...' : 'Search Users'}
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
                  <input
                    type="password"
                    value={adminResetPassword}
                    onChange={(e) => setAdminResetPassword(e.target.value)}
                    placeholder="New password for selected user"
                    className="input md:col-span-2"
                  />
                  <p className="text-dark-400 text-xs self-center">
                    Reset revokes existing sessions for that user.
                  </p>
                </div>

                {adminRecoveryStatus && (
                  <div className={`mb-3 ${adminRecoveryStatus.type === 'success' ? 'badge badge-success' : 'badge badge-danger'}`}>
                    {adminRecoveryStatus.message}
                  </div>
                )}

                <div className="space-y-2">
                  {adminSearchResults.map((result) => (
                    <div key={result.id} className="flex flex-col md:flex-row md:items-center md:justify-between gap-2 p-3 rounded-lg bg-dark-700 border border-dark-600">
                      <div>
                        <p className="text-white text-sm font-medium">{result.full_name}</p>
                        <p className="text-dark-300 text-xs">@{result.username} · {result.email}</p>
                      </div>
                      <div className="flex gap-2">
                        <button onClick={() => unlockRecoveredUser(result.id)} disabled={adminRecoveryLoading} className="btn btn-secondary disabled:opacity-50">
                          Unlock
                        </button>
                        <button onClick={() => resetRecoveredUserPassword(result.id)} disabled={adminRecoveryLoading} className="btn btn-primary disabled:opacity-50">
                          Reset Password
                        </button>
                      </div>
                    </div>
                  ))}
                  {!adminSearchResults.length && (
                    <p className="text-dark-400 text-sm">No users loaded.</p>
                  )}
                </div>
              </div>
            )}

            <div className="card p-8">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-3">
                  <KeyRound className="w-6 h-6 text-primary-500" />
                  <h2 className="text-xl font-semibold text-white">API Keys</h2>
                </div>
                <button onClick={loadApiKeyStatus} className="btn btn-secondary flex items-center space-x-2">
                  <RefreshCw className="w-4 h-4" />
                  <span>Refresh</span>
                </button>
              </div>

              <p className="text-dark-300 text-sm mb-4">
                Keys entered here are applied to the running backend process and are not persisted after restart.
              </p>

              {apiKeysError && (
                <div className="mb-4 text-sm text-red-300 bg-red-900/20 border border-red-700 rounded-md px-3 py-2">
                  {apiKeysError}
                </div>
              )}

              {apiKeysSuccess && (
                <div className="mb-4 text-sm text-green-300 bg-green-900/20 border border-green-700 rounded-md px-3 py-2">
                  {apiKeysSuccess}
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-4">
                <div className="rounded-lg border border-dark-600 bg-dark-800/70 p-4">
                  <p className="text-dark-300 text-sm">Anthropic</p>
                  <p className={`text-sm font-medium ${apiKeyStatus?.anthropic_configured ? 'text-green-300' : 'text-yellow-300'}`}>
                    {apiKeysLoading ? 'Checking...' : (apiKeyStatus?.anthropic_configured ? 'Configured' : 'Missing')}
                  </p>
                </div>
                <div className="rounded-lg border border-dark-600 bg-dark-800/70 p-4">
                  <p className="text-dark-300 text-sm">OpenAI</p>
                  <p className={`text-sm font-medium ${apiKeyStatus?.openai_configured ? 'text-green-300' : 'text-yellow-300'}`}>
                    {apiKeysLoading ? 'Checking...' : (apiKeyStatus?.openai_configured ? 'Configured' : 'Missing')}
                  </p>
                </div>
                <div className="rounded-lg border border-dark-600 bg-dark-800/70 p-4">
                  <p className="text-dark-300 text-sm">OpenRouter</p>
                  <p className={`text-sm font-medium ${apiKeyStatus?.openrouter_configured ? 'text-green-300' : 'text-yellow-300'}`}>
                    {apiKeysLoading ? 'Checking...' : (apiKeyStatus?.openrouter_configured ? 'Configured' : 'Missing')}
                  </p>
                </div>
                <div className="rounded-lg border border-dark-600 bg-dark-800/70 p-4">
                  <p className="text-dark-300 text-sm">AI Availability</p>
                  <p className={`text-sm font-medium ${apiKeyStatus?.ai_available ? 'text-green-300' : 'text-red-300'}`}>
                    {apiKeysLoading ? 'Checking...' : (apiKeyStatus?.ai_available ? 'Available' : 'Unavailable')}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                <div>
                  <label className="block text-white font-medium mb-2">Anthropic API Key</label>
                  <input
                    type="password"
                    value={apiKeyForm.anthropic_api_key}
                    onChange={(e) => setApiKeyForm((prev) => ({ ...prev, anthropic_api_key: e.target.value }))}
                    className="input w-full"
                    placeholder="sk-ant-..."
                  />
                </div>
                <div>
                  <label className="block text-white font-medium mb-2">OpenAI API Key</label>
                  <input
                    type="password"
                    value={apiKeyForm.openai_api_key}
                    onChange={(e) => setApiKeyForm((prev) => ({ ...prev, openai_api_key: e.target.value }))}
                    className="input w-full"
                    placeholder="sk-..."
                  />
                </div>
                <div>
                  <label className="block text-white font-medium mb-2">OpenRouter API Key</label>
                  <input
                    type="password"
                    value={apiKeyForm.openrouter_api_key}
                    onChange={(e) => setApiKeyForm((prev) => ({ ...prev, openrouter_api_key: e.target.value }))}
                    className="input w-full"
                    placeholder="sk-or-..."
                  />
                </div>
              </div>

              <div className="flex items-center justify-between mb-4 p-3 rounded-lg border border-dark-600 bg-dark-800/40">
                <div>
                  <p className="text-white font-medium text-sm">Persist to .env</p>
                  <p className="text-dark-300 text-xs">
                    {apiKeyStatus?.can_persist_to_env
                      ? 'Save keys to local .env so they survive backend restarts.'
                      : 'Requires system actions permission.'}
                  </p>
                </div>
                <button
                  onClick={() => setPersistApiKeys((prev) => !prev)}
                  disabled={!apiKeyStatus?.can_persist_to_env}
                  className={`w-12 h-6 rounded-full transition-colors disabled:opacity-50 ${
                    persistApiKeys ? 'bg-primary-600' : 'bg-dark-600'
                  }`}
                >
                  <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                    persistApiKeys ? 'translate-x-6' : 'translate-x-0.5'
                  }`} />
                </button>
              </div>

              <button onClick={saveApiKeys} disabled={apiKeysSaving} className="btn btn-primary disabled:opacity-50">
                {apiKeysSaving ? 'Updating...' : 'Update Runtime API Keys'}
              </button>
            </div>

            <div className="card p-8">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-3">
                  <Zap className="w-6 h-6 text-primary-500" />
                  <h2 className="text-xl font-semibold text-white">System Actions</h2>
                </div>
                <button onClick={loadSystemActions} className="btn btn-secondary flex items-center space-x-2">
                  <RefreshCw className="w-4 h-4" />
                  <span>Refresh</span>
                </button>
              </div>

              {systemActionsError && (
                <div className="mb-4 text-sm text-red-300 bg-red-900/20 border border-red-700 rounded-md px-3 py-2">
                  {systemActionsError}
                </div>
              )}

              {!systemActionsEnabled && !systemActionsLoading && (
                <p className="text-dark-300 text-sm mb-4">
                  System actions are disabled. Set <code>ENABLE_SYSTEM_ACTIONS=true</code> and include your username in <code>SYSTEM_ACTION_USERS</code>.
                </p>
              )}

              {systemActionsLoading ? (
                <p className="text-dark-300">Loading actions...</p>
              ) : (
                <div className="flex flex-wrap gap-2 mb-4">
                  {systemActions.map((action) => (
                    <button
                      key={action}
                      onClick={() => runSystemAction(action)}
                      disabled={runningAction !== null}
                      className="btn btn-secondary disabled:opacity-50"
                    >
                      {runningAction === action ? `Running ${action}...` : action.replaceAll('_', ' ')}
                    </button>
                  ))}
                </div>
              )}

              <div>
                <label className="block text-white font-medium mb-2">Action Output</label>
                <pre className="bg-dark-800 border border-dark-600 rounded-lg p-3 text-xs text-dark-200 overflow-auto max-h-64 whitespace-pre-wrap">
                  {actionOutput || 'No action run yet.'}
                </pre>
              </div>
            </div>

            <div className="card p-8">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-3">
                  <Bot className="w-6 h-6 text-primary-500" />
                  <h2 className="text-xl font-semibold text-white">Active Agents</h2>
                </div>
                <button onClick={loadAgents} className="btn btn-secondary flex items-center space-x-2">
                  <RefreshCw className="w-4 h-4" />
                  <span>Refresh</span>
                </button>
              </div>

              {agentsError && (
                <div className="mb-4 text-sm text-red-300 bg-red-900/20 border border-red-700 rounded-md px-3 py-2">
                  {agentsError}
                </div>
              )}

              {agentsLoading ? (
                <p className="text-dark-300">Loading agents...</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {agents.map((agent) => (
                    <div key={agent.agent_id} className="rounded-lg border border-dark-600 bg-dark-800/70 p-4">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-white font-medium">{agent.name}</p>
                        <span className={`text-xs px-2 py-1 rounded ${
                          agent.is_active ? 'bg-green-700/40 text-green-300' : 'bg-dark-700 text-dark-300'
                        }`}>
                          {agent.is_active ? 'active' : 'inactive'}
                        </span>
                      </div>
                      <p className="text-dark-300 text-sm mb-1">ID: {agent.agent_id}</p>
                      <p className="text-dark-300 text-sm">Version: {agent.version}</p>
                      <p className="text-dark-300 text-sm">Queue depth: {agent.queue_depth ?? 0}</p>
                      {agent.last_error && (
                        <p className="text-red-300 text-xs mt-2 break-words">
                          Last error: {agent.last_error}
                        </p>
                      )}
                      {agent.last_error_at && (
                        <p className="text-dark-400 text-xs mt-1">
                          Error time: {new Date(agent.last_error_at).toLocaleString()}
                        </p>
                      )}
                    </div>
                  ))}
                  {!agents.length && (
                    <p className="text-dark-300">No agents registered.</p>
                  )}
                </div>
              )}
            </div>

            <div className="card p-8">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-3">
                  <Search className="w-6 h-6 text-primary-500" />
                  <h2 className="text-xl font-semibold text-white">Semantic Log Search</h2>
                </div>
                <button
                  onClick={runLogBackfill}
                  disabled={logBackfillLoading}
                  className="btn btn-secondary disabled:opacity-50"
                >
                  {logBackfillLoading ? 'Indexing...' : 'Backfill Embeddings'}
                </button>
              </div>

              {logStatsError && (
                <div className="mb-4 text-sm text-red-300 bg-red-900/20 border border-red-700 rounded-md px-3 py-2">
                  {logStatsError}
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6">
                <div className="rounded-lg border border-dark-600 bg-dark-800/70 p-4">
                  <p className="text-dark-300 text-sm">Total Logs</p>
                  <p className="text-white text-xl font-semibold">{logStatsLoading ? '...' : (logStats?.total_logs ?? 0)}</p>
                </div>
                <div className="rounded-lg border border-dark-600 bg-dark-800/70 p-4">
                  <p className="text-dark-300 text-sm">Embedded Logs</p>
                  <p className="text-white text-xl font-semibold">{logStatsLoading ? '...' : (logStats?.logs_with_embeddings ?? 0)}</p>
                </div>
                <div className="rounded-lg border border-dark-600 bg-dark-800/70 p-4">
                  <p className="text-dark-300 text-sm">Coverage</p>
                  <p className="text-white text-xl font-semibold">
                    {logStatsLoading ? '...' : `${Number(logStats?.coverage_percentage ?? 0).toFixed(1)}%`}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-4">
                <div className="md:col-span-2">
                  <label className="block text-white font-medium mb-2">Query</label>
                  <input
                    type="text"
                    value={logQuery}
                    onChange={(e) => setLogQuery(e.target.value)}
                    className="input w-full"
                    placeholder="e.g. websocket parse error"
                  />
                </div>
                <div>
                  <label className="block text-white font-medium mb-2">Threshold</label>
                  <input
                    type="number"
                    min={0}
                    max={1}
                    step={0.05}
                    value={logThreshold}
                    onChange={(e) => setLogThreshold(Number(e.target.value))}
                    className="input w-full"
                  />
                </div>
                <div>
                  <label className="block text-white font-medium mb-2">Limit</label>
                  <input
                    type="number"
                    min={1}
                    max={100}
                    step={1}
                    value={logLimit}
                    onChange={(e) => setLogLimit(Number(e.target.value))}
                    className="input w-full"
                  />
                </div>
              </div>

              <div className="mb-4">
                <button onClick={runLogSearch} disabled={logSearchLoading} className="btn btn-primary disabled:opacity-50">
                  {logSearchLoading ? 'Searching...' : 'Search Logs'}
                </button>
              </div>

              {logSearchError && (
                <div className="mb-4 text-sm text-red-300 bg-red-900/20 border border-red-700 rounded-md px-3 py-2">
                  {logSearchError}
                </div>
              )}

              <div className="space-y-3 max-h-96 overflow-y-auto">
                {logSearchResults.map((result) => (
                  <div key={result.id} className="rounded-lg border border-dark-600 bg-dark-800/60 p-4">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-white font-medium">{result.agent_id} · {result.action}</p>
                      <span className="text-primary-300 text-sm">{Number(result.similarity_score ?? 0).toFixed(3)}</span>
                    </div>
                    <p className="text-dark-300 text-sm mb-1">Status: {result.status}</p>
                    {result.error_message && (
                      <p className="text-red-300 text-sm">Error: {result.error_message}</p>
                    )}
                    <p className="text-dark-400 text-xs mt-2">{result.started_at ? new Date(result.started_at).toLocaleString() : 'No timestamp'}</p>
                  </div>
                ))}
                {!logSearchLoading && !logSearchResults.length && (
                  <div className="text-dark-300 text-sm">No semantic matches yet.</div>
                )}
              </div>
            </div>

            <div className="card p-8">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-3">
                  <Database className="w-6 h-6 text-primary-500" />
                  <h2 className="text-xl font-semibold text-white">Log Viewer</h2>
                </div>
                <button onClick={loadRecentLogs} className="btn btn-secondary flex items-center space-x-2">
                  <RefreshCw className="w-4 h-4" />
                  <span>Refresh Logs</span>
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                <div>
                  <label className="block text-white font-medium mb-2">Hours</label>
                  <input
                    type="number"
                    min={1}
                    max={168}
                    value={logsHours}
                    onChange={(e) => setLogsHours(Number(e.target.value))}
                    className="input w-full"
                  />
                </div>
                <div>
                  <label className="block text-white font-medium mb-2">Limit</label>
                  <input
                    type="number"
                    min={1}
                    max={500}
                    value={logsLimit}
                    onChange={(e) => setLogsLimit(Number(e.target.value))}
                    className="input w-full"
                  />
                </div>
                <div>
                  <label className="block text-white font-medium mb-2">Status</label>
                  <select
                    value={logsStatus}
                    onChange={(e) => setLogsStatus(e.target.value)}
                    className="input w-full"
                  >
                    <option value="">All</option>
                    <option value="started">started</option>
                    <option value="completed">completed</option>
                    <option value="failed">failed</option>
                  </select>
                </div>
              </div>

              <div className="mb-4">
                <button onClick={loadRecentLogs} className="btn btn-primary" disabled={recentLogsLoading}>
                  {recentLogsLoading ? 'Loading...' : 'Load Logs'}
                </button>
              </div>

              {recentLogsError && (
                <div className="mb-4 text-sm text-red-300 bg-red-900/20 border border-red-700 rounded-md px-3 py-2">
                  {recentLogsError}
                </div>
              )}

              <div className="space-y-3 max-h-96 overflow-y-auto">
                {recentLogs.map((log) => (
                  <div key={log.id} className="rounded-lg border border-dark-600 bg-dark-800/60 p-4">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-white font-medium">{log.agent_id} · {log.action}</p>
                      <span className={`text-xs px-2 py-1 rounded ${
                        log.status === 'failed'
                          ? 'bg-red-700/30 text-red-300'
                          : log.status === 'completed'
                            ? 'bg-green-700/30 text-green-300'
                          : 'bg-yellow-700/30 text-yellow-200'
                      }`}>{log.status}</span>
                    </div>
                    <p className="text-dark-300 text-sm">{log.started_at ? new Date(log.started_at).toLocaleString() : 'No start time'}</p>
                    {log.error_message && (
                      <p className="text-red-300 text-sm mt-2">Error: {log.error_message}</p>
                    )}
                    {log.processing_time != null && (
                      <p className="text-dark-400 text-xs mt-1">Processing time: {Number(log.processing_time).toFixed(2)}s</p>
                    )}
                    <div className="mt-3">
                      <button
                        onClick={() => toggleLogExpanded(log.id)}
                        className="text-xs text-primary-300 hover:text-primary-200 underline"
                      >
                        {expandedLogIds[log.id] ? 'Hide payload' : 'Show payload'}
                      </button>
                    </div>
                    {expandedLogIds[log.id] && (
                      <div className="mt-3 grid grid-cols-1 gap-3">
                        <div>
                          <p className="text-dark-300 text-xs mb-1">input_data</p>
                          <pre className="bg-dark-900 border border-dark-700 rounded p-2 text-xs text-dark-200 overflow-auto max-h-40 whitespace-pre-wrap">
                            {formatJsonForDisplay(log.input_data) || '<empty>'}
                          </pre>
                        </div>
                        <div>
                          <p className="text-dark-300 text-xs mb-1">output_data</p>
                          <pre className="bg-dark-900 border border-dark-700 rounded p-2 text-xs text-dark-200 overflow-auto max-h-40 whitespace-pre-wrap">
                            {formatJsonForDisplay(log.output_data) || '<empty>'}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                {!recentLogsLoading && !recentLogs.length && (
                  <div className="text-dark-300 text-sm">No logs found for this filter.</div>
                )}
              </div>
            </div>

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
          </div>
        )}
      </div>
    </div>
  )
}

export default SettingsPage
