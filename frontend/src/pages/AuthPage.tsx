import React, { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import LoginForm from '../components/auth/LoginForm'
import RegisterForm from '../components/auth/RegisterForm'

const AuthPage: React.FC = () => {
  const [searchParams] = useSearchParams()
  const [mode, setMode] = useState<'login' | 'register'>(
    searchParams.get('mode') === 'register' ? 'register' : 'login'
  )
  const [showSuccess, setShowSuccess] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')
  
  const navigate = useNavigate()
  const { isAuthenticated, hasHydrated, checkAuthStatus } = useAuthStore()

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/')
    }
  }, [isAuthenticated, navigate])

  useEffect(() => {
    if (!hasHydrated) return

    // Check if user is already authenticated
    checkAuthStatus()
  }, [hasHydrated, checkAuthStatus])

  useEffect(() => {
    if (searchParams.get('passwordChanged') === '1') {
      setSuccessMessage('Password changed successfully. Please sign in with your new password.')
      setShowSuccess(true)
      setMode('login')
    }
  }, [searchParams])

  const handleLoginSuccess = () => {
    navigate('/')
  }

  const handleRegisterSuccess = () => {
    setSuccessMessage('Account created successfully! Please sign in.')
    setShowSuccess(true)
    setMode('login')
    
    // Auto-hide success message after 5 seconds
    setTimeout(() => {
      setShowSuccess(false)
    }, 5000)
  }

  const handleSwitchMode = () => {
    setMode(mode === 'login' ? 'register' : 'login')
    setShowSuccess(false)
  }

  return (
    <div className="relative min-h-screen bg-dark-900 flex items-center justify-center p-4 overflow-hidden">
      <div className="absolute inset-0 pointer-events-none bg-gradient-to-br from-primary-600/10 via-dark-900 to-dark-900"></div>
      
      <div className="relative z-10 w-full max-w-md pointer-events-auto">
        {showSuccess && (
          <div className="mb-6 bg-green-900/20 border border-green-700 rounded-md p-4">
            <div className="flex">
              <div className="text-sm text-green-300">
                {successMessage}
              </div>
            </div>
          </div>
        )}

        {mode === 'login' ? (
          <LoginForm
            onSuccess={handleLoginSuccess}
            onSwitchToRegister={handleSwitchMode}
          />
        ) : (
          <RegisterForm
            onSuccess={handleRegisterSuccess}
            onSwitchToLogin={handleSwitchMode}
          />
        )}
      </div>

      {/* Background decoration */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-44 h-44 bg-primary-500/20 rounded-full blur-3xl"></div>
        <div className="absolute bottom-1/4 right-1/4 w-56 h-56 bg-primary-700/20 rounded-full blur-3xl"></div>
        <div className="absolute top-3/4 left-1/2 w-32 h-32 bg-dark-600/40 rounded-full blur-2xl"></div>
      </div>
    </div>
  )
}

export default AuthPage
