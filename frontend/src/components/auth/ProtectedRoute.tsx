import React, { useEffect, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import { Loader2 } from 'lucide-react'

interface ProtectedRouteProps {
  children: React.ReactNode
  requiredRole?: string
  requiredPermission?: string
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredRole,
  requiredPermission 
}) => {
  const [isChecking, setIsChecking] = useState(true)
  const location = useLocation()
  const { isAuthenticated, user, checkAuthStatus } = useAuthStore()

  useEffect(() => {
    const checkAuth = async () => {
      if (!isAuthenticated) {
        await checkAuthStatus()
      }
      setIsChecking(false)
    }

    checkAuth()
  }, [isAuthenticated, checkAuthStatus])

  // Show loading spinner while checking authentication
  if (isChecking) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="animate-spin w-8 h-8 text-blue-500 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Checking authentication...</p>
        </div>
      </div>
    )
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/auth?mode=login" state={{ from: location }} replace />
  }

  // Check role requirement
  if (requiredRole && user) {
    const hasRole = user.roles.includes(requiredRole)
    if (!hasRole) {
      return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
          <div className="text-center">
            <div className="text-6xl mb-4">🔒</div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              Access Denied
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              You don't have permission to access this page.
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-500">
              Required role: {requiredRole}
            </p>
          </div>
        </div>
      )
    }
  }

  // Check permission requirement (this would need to be implemented based on your permission system)
  if (requiredPermission && user) {
    // For now, we'll just check if the user has the required role
    // In a real implementation, you'd check specific permissions
    const hasPermission = user.roles.includes('admin') || user.roles.includes('user')
    if (!hasPermission) {
      return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
          <div className="text-center">
            <div className="text-6xl mb-4">🔒</div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              Access Denied
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              You don't have permission to access this page.
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-500">
              Required permission: {requiredPermission}
            </p>
          </div>
        </div>
      )
    }
  }

  return <>{children}</>
}

export default ProtectedRoute