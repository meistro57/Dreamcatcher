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
  RefreshCw
} from 'lucide-react'
import { useAppStore } from '../stores/appStore'

const SettingsPage = () => {
  const { settings, updateSettings } = useAppStore()
  const [isSaving, setIsSaving] = useState(false)
  
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
  
  return (
    <div className="min-h-screen bg-dark-900 mobile-padding">
      <div className="max-w-4xl mx-auto pt-8 pb-24">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Settings</h1>
            <p className="text-dark-300">
              Configure your Dreamcatcher experience
            </p>
          </div>
          
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
              className="btn btn-primary flex items-center space-x-2"
            >
              <Save className="w-4 h-4" />
              <span>{isSaving ? 'Saving...' : 'Save'}</span>
            </button>
          </div>
        </div>
        
        {/* Voice Capture Settings */}
        <div className="card p-8 mb-8">
          <div className="flex items-center space-x-3 mb-6">
            <Mic className="w-6 h-6 text-primary-500" />
            <h2 className="text-xl font-semibold text-white">Voice Capture</h2>
          </div>
          
          <div className="space-y-6">
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
          </div>
        </div>
        
        {/* Notifications Settings */}
        <div className="card p-8 mb-8">
          <div className="flex items-center space-x-3 mb-6">
            <Bell className="w-6 h-6 text-primary-500" />
            <h2 className="text-xl font-semibold text-white">Notifications</h2>
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
                onClick={() => updateSettings({ notifications: !settings.notifications })}
                className={`w-12 h-6 rounded-full transition-colors ${
                  settings.notifications ? 'bg-primary-600' : 'bg-dark-600'
                }`}
              >
                <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                  settings.notifications ? 'translate-x-6' : 'translate-x-0.5'
                }`} />
              </button>
            </div>
          </div>
        </div>
        
        {/* Offline Settings */}
        <div className="card p-8 mb-8">
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
        
        {/* System Information */}
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
    </div>
  )
}

export default SettingsPage