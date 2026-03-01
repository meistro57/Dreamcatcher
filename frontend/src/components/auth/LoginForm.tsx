import React, { useState } from 'react'
import { Eye, EyeOff, Mail, Lock, LogIn, Loader2 } from 'lucide-react'
import { useAuthStore } from '../../stores/authStore'

interface LoginFormProps {
  onSuccess?: () => void
  onSwitchToRegister?: () => void
}

const LoginForm: React.FC<LoginFormProps> = ({ onSuccess, onSwitchToRegister }) => {
  const [formData, setFormData] = useState({
    email_or_username: '',
    password: ''
  })
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  
  const { login, isLoading, error, clearError } = useAuthStore()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()
    
    const success = await login(formData.email_or_username, formData.password)
    
    if (success) {
      onSuccess?.()
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    
    if (error) {
      clearError()
    }
  }

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="card p-8">
        <div className="text-center mb-8">
          <div className="w-16 h-16 gradient-primary rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg shadow-primary-700/30">
            <LogIn className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-white">
            Welcome Back
          </h2>
          <p className="text-dark-300 mt-2">
            Sign in to your Dreamcatcher account
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-900/20 border border-red-700 rounded-md p-4">
              <div className="flex">
                <div className="text-sm text-red-300">
                  {error}
                </div>
              </div>
            </div>
          )}

          <div>
            <label htmlFor="email_or_username" className="block text-sm font-medium text-dark-200 mb-2">
              Email or Username
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Mail className="h-5 w-5 text-dark-400" />
              </div>
              <input
                id="email_or_username"
                name="email_or_username"
                type="text"
                autoComplete="username"
                required
                value={formData.email_or_username}
                onChange={handleInputChange}
                className="input block w-full pl-10 pr-3 py-2"
                placeholder="Enter your email or username"
              />
            </div>
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-dark-200 mb-2">
              Password
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="h-5 w-5 text-dark-400" />
              </div>
              <input
                id="password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                required
                value={formData.password}
                onChange={handleInputChange}
                className="input block w-full pl-10 pr-10 py-2"
                placeholder="Enter your password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
              >
                {showPassword ? (
                  <EyeOff className="h-5 w-5 text-dark-400 hover:text-dark-200" />
                ) : (
                  <Eye className="h-5 w-5 text-dark-400 hover:text-dark-200" />
                )}
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <input
                id="remember_me"
                name="remember_me"
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-dark-500 rounded bg-dark-700"
              />
              <label htmlFor="remember_me" className="ml-2 block text-sm text-dark-200">
                Remember me
              </label>
            </div>

            <div className="text-sm">
              <a href="#" className="font-medium text-primary-400 hover:text-primary-300">
                Forgot your password?
              </a>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="btn btn-primary w-full flex justify-center items-center py-2 px-4 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <Loader2 className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" />
                Signing in...
              </>
            ) : (
              <>
                <LogIn className="-ml-1 mr-3 h-5 w-5" />
                Sign in
              </>
            )}
          </button>

          {onSwitchToRegister && (
            <div className="text-center">
              <p className="text-sm text-dark-300">
                Don't have an account?{' '}
                <button
                  type="button"
                  onClick={onSwitchToRegister}
                  className="font-medium text-primary-400 hover:text-primary-300"
                >
                  Sign up
                </button>
              </p>
            </div>
          )}
        </form>
      </div>
    </div>
  )
}

export default LoginForm
