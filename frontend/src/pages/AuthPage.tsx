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
  const { isAuthenticated, checkAuthStatus } = useAuthStore()

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/')
    }
  }, [isAuthenticated, navigate])

  useEffect(() => {
    // Check if user is already authenticated
    checkAuthStatus()
  }, [checkAuthStatus])

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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-gradient-to-br from-blue-400/20 to-purple-600/20 dark:from-blue-600/10 dark:to-purple-800/10"></div>
      
      <div className="relative z-10 w-full max-w-md">
        {showSuccess && (
          <div className="mb-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md p-4">
            <div className="flex">
              <div className="text-sm text-green-600 dark:text-green-400">
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
        <div className="absolute top-1/4 left-1/4 w-32 h-32 bg-blue-300/30 rounded-full blur-xl"></div>
        <div className="absolute bottom-1/4 right-1/4 w-48 h-48 bg-purple-300/30 rounded-full blur-xl"></div>
        <div className="absolute top-3/4 left-1/2 w-24 h-24 bg-indigo-300/30 rounded-full blur-xl"></div>
      </div>
    </div>
  )
}

export default AuthPage