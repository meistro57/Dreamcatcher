import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { User, Mail, Calendar, Shield, Edit2, Save, X, Lock } from 'lucide-react'
import { useAuthStore } from '../../stores/authStore'
import { api } from '../../utils/api'

const UserProfile: React.FC = () => {
  const navigate = useNavigate()
  const { user, updateUser, logout } = useAuthStore()
  const [isEditing, setIsEditing] = useState(false)
  const [editData, setEditData] = useState({
    full_name: user?.full_name || '',
    email: user?.email || '',
    username: user?.username || ''
  })
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  })
  const [isChangingPassword, setIsChangingPassword] = useState(false)
  const [passwordStatus, setPasswordStatus] = useState<{ type: 'success' | 'error', message: string } | null>(null)

  if (!user) return null

  const handleEdit = () => {
    setIsEditing(true)
    setEditData({
      full_name: user.full_name,
      email: user.email,
      username: user.username
    })
  }

  const handleSave = async () => {
    try {
      // In a real app, you'd make an API call here
      updateUser(editData)
      setIsEditing(false)
    } catch (error) {
      console.error('Failed to update profile:', error)
    }
  }

  const handleCancel = () => {
    setIsEditing(false)
    setEditData({
      full_name: user.full_name,
      email: user.email,
      username: user.username
    })
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setEditData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handlePasswordInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setPasswordData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setPasswordStatus(null)

    if (!passwordData.current_password || !passwordData.new_password || !passwordData.confirm_password) {
      setPasswordStatus({ type: 'error', message: 'All password fields are required.' })
      return
    }

    if (passwordData.new_password !== passwordData.confirm_password) {
      setPasswordStatus({ type: 'error', message: 'New password confirmation does not match.' })
      return
    }

    setIsChangingPassword(true)
    try {
      await api.auth.changePassword(passwordData)
      setPasswordStatus({
        type: 'success',
        message: 'Password changed. You will be signed out and asked to log in again.'
      })
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: ''
      })
      setTimeout(() => {
        logout()
        navigate('/auth?mode=login&passwordChanged=1', { replace: true })
      }, 1200)
    } catch (error: any) {
      const message = error?.response?.data?.detail || 'Password change failed.'
      setPasswordStatus({ type: 'error', message })
    } finally {
      setIsChangingPassword(false)
    }
  }

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-700 to-primary-600 px-6 py-5 border-b border-dark-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center">
              <User className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">
                {user.full_name}
              </h2>
              <p className="text-blue-100">
                @{user.username}
              </p>
            </div>
          </div>
          
          {!isEditing ? (
            <button
              onClick={handleEdit}
              className="btn btn-secondary !bg-white/15 !border-white/30 !text-white hover:!bg-white/25"
            >
              <Edit2 className="w-4 h-4" />
              <span>Edit</span>
            </button>
          ) : (
            <div className="flex items-center space-x-2">
              <button
                onClick={handleSave}
                className="btn !bg-green-600 hover:!bg-green-700 !text-white !border-green-500"
              >
                <Save className="w-4 h-4" />
                <span>Save</span>
              </button>
              <button
                onClick={handleCancel}
                className="btn !bg-red-600 hover:!bg-red-700 !text-white !border-red-500"
              >
                <X className="w-4 h-4" />
                <span>Cancel</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6 bg-dark-800">
        {/* Basic Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-dark-300 mb-2">
              Full Name
            </label>
            {isEditing ? (
              <input
                type="text"
                name="full_name"
                value={editData.full_name}
                onChange={handleInputChange}
                className="input w-full"
              />
            ) : (
              <div className="flex items-center space-x-2 p-3 rounded-lg bg-dark-700 border border-dark-600">
                <User className="w-4 h-4 text-dark-400" />
                <span className="text-white">{user.full_name}</span>
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-300 mb-2">
              Email
            </label>
            {isEditing ? (
              <input
                type="email"
                name="email"
                value={editData.email}
                onChange={handleInputChange}
                className="input w-full"
              />
            ) : (
              <div className="flex items-center space-x-2 p-3 rounded-lg bg-dark-700 border border-dark-600">
                <Mail className="w-4 h-4 text-dark-400" />
                <span className="text-white">{user.email}</span>
                {user.is_verified && (
                  <span className="badge badge-success">
                    Verified
                  </span>
                )}
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-300 mb-2">
              Username
            </label>
            {isEditing ? (
              <input
                type="text"
                name="username"
                value={editData.username}
                onChange={handleInputChange}
                className="input w-full"
              />
            ) : (
              <div className="flex items-center space-x-2 p-3 rounded-lg bg-dark-700 border border-dark-600">
                <User className="w-4 h-4 text-dark-400" />
                <span className="text-white">@{user.username}</span>
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-300 mb-2">
              Member Since
            </label>
            <div className="flex items-center space-x-2 p-3 rounded-lg bg-dark-700 border border-dark-600">
              <Calendar className="w-4 h-4 text-dark-400" />
              <span className="text-white">
                {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {/* Roles */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-2">
            Roles
          </label>
          <div className="flex items-center space-x-2 p-3 rounded-lg bg-dark-700 border border-dark-600">
            <Shield className="w-4 h-4 text-dark-400" />
            <div className="flex flex-wrap gap-2">
              {user.roles.map((role) => (
                <span
                  key={role}
                  className="badge badge-primary"
                >
                  {role}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Account Status */}
        <div>
          <label className="block text-sm font-medium text-dark-300 mb-2">
            Account Status
          </label>
          <div className="flex flex-wrap gap-2 p-3 rounded-lg bg-dark-700 border border-dark-600">
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
              user.is_active 
                ? 'badge badge-success'
                : 'badge badge-danger'
            }`}>
              {user.is_active ? 'Active' : 'Inactive'}
            </span>
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
              user.is_verified 
                ? 'badge badge-success'
                : 'badge badge-warning'
            }`}>
              {user.is_verified ? 'Verified' : 'Unverified'}
            </span>
          </div>
        </div>

        <div className="pt-4 border-t border-dark-600">
          <div className="flex items-center space-x-2 mb-4">
            <Lock className="w-4 h-4 text-dark-400" />
            <h3 className="text-white font-semibold">Change Password</h3>
          </div>

          <form onSubmit={handleChangePassword} className="space-y-4 max-w-xl">
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Current Password</label>
              <input
                type="password"
                name="current_password"
                value={passwordData.current_password}
                onChange={handlePasswordInputChange}
                className="input w-full"
                autoComplete="current-password"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">New Password</label>
              <input
                type="password"
                name="new_password"
                value={passwordData.new_password}
                onChange={handlePasswordInputChange}
                className="input w-full"
                autoComplete="new-password"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">Confirm New Password</label>
              <input
                type="password"
                name="confirm_password"
                value={passwordData.confirm_password}
                onChange={handlePasswordInputChange}
                className="input w-full"
                autoComplete="new-password"
              />
            </div>

            {passwordStatus && (
              <div className={passwordStatus.type === 'success' ? 'badge badge-success' : 'badge badge-danger'}>
                {passwordStatus.message}
              </div>
            )}

            <button
              type="submit"
              disabled={isChangingPassword}
              className="btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isChangingPassword ? 'Changing Password...' : 'Update Password'}
            </button>
          </form>
        </div>

      </div>
    </div>
  )
}

export default UserProfile
