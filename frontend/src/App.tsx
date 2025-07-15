import { Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'

// Store imports
import { useAppStore } from './stores/appStore'
import { useWebSocketStore } from './stores/webSocketStore'
import { useAuthStore } from './stores/authStore'

// Component imports
import Layout from './components/Layout'
import ProtectedRoute from './components/auth/ProtectedRoute'
import HomePage from './pages/HomePage'
import IdeasPage from './pages/IdeasPage'
import IdeaDetailPage from './pages/IdeaDetailPage'
import ProposalsPage from './pages/ProposalsPage'
import StatsPage from './pages/StatsPage'
import SettingsPage from './pages/SettingsPage'
import AuthPage from './pages/AuthPage'
import NotFoundPage from './pages/NotFoundPage'

// Utility imports
import { initializeApp } from './utils/initialization'

function App() {
  const { isInitialized, initializeStore } = useAppStore()
  const { connect: connectWebSocket } = useWebSocketStore()
  const { checkAuthStatus } = useAuthStore()

  useEffect(() => {
    // Initialize the app
    const init = async () => {
      try {
        await initializeApp()
        initializeStore()
        
        // Check authentication status
        await checkAuthStatus()
        
        // Connect to WebSocket for real-time updates
        connectWebSocket()
      } catch (error) {
        console.error('Failed to initialize app:', error)
      }
    }

    init()
  }, [initializeStore, connectWebSocket, checkAuthStatus])

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
    <Routes>
      <Route path="/auth" element={<AuthPage />} />
      <Route path="/" element={
        <ProtectedRoute>
          <Layout>
            <HomePage />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/ideas" element={
        <ProtectedRoute>
          <Layout>
            <IdeasPage />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/ideas/:id" element={
        <ProtectedRoute>
          <Layout>
            <IdeaDetailPage />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/proposals" element={
        <ProtectedRoute>
          <Layout>
            <ProposalsPage />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/stats" element={
        <ProtectedRoute>
          <Layout>
            <StatsPage />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="/settings" element={
        <ProtectedRoute>
          <Layout>
            <SettingsPage />
          </Layout>
        </ProtectedRoute>
      } />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

export default App