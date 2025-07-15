import { Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'

// Store imports
import { useAppStore } from './stores/appStore'
import { useWebSocketStore } from './stores/webSocketStore'

// Component imports
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import IdeasPage from './pages/IdeasPage'
import IdeaDetailPage from './pages/IdeaDetailPage'
import ProposalsPage from './pages/ProposalsPage'
import StatsPage from './pages/StatsPage'
import SettingsPage from './pages/SettingsPage'
import NotFoundPage from './pages/NotFoundPage'

// Utility imports
import { initializeApp } from './utils/initialization'

function App() {
  const { isInitialized, initializeStore } = useAppStore()
  const { connect: connectWebSocket } = useWebSocketStore()

  useEffect(() => {
    // Initialize the app
    const init = async () => {
      try {
        await initializeApp()
        initializeStore()
        
        // Connect to WebSocket for real-time updates
        connectWebSocket()
      } catch (error) {
        console.error('Failed to initialize app:', error)
      }
    }

    init()
  }, [initializeStore, connectWebSocket])

  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-dark-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin-slow w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-dark-300">Initializing Dreamcatcher...</p>
        </div>
      </div>
    )
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/ideas" element={<IdeasPage />} />
        <Route path="/ideas/:id" element={<IdeaDetailPage />} />
        <Route path="/proposals" element={<ProposalsPage />} />
        <Route path="/stats" element={<StatsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Layout>
  )
}

export default App