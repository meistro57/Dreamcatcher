import React, { useState, useEffect } from 'react'
import { Brain, Database, RefreshCw, Zap, Activity, TrendingUp } from 'lucide-react'
import { api } from '../../utils/api'
import { useNotificationStore } from '../../stores/notificationStore'

interface EmbeddingStatsProps {
  className?: string
}

interface EmbeddingStats {
  total_ideas: number
  ideas_with_embeddings: number
  coverage_percentage: number
  model_stats: Record<string, number>
  current_model: string
  embedding_dimension: number
}

const EmbeddingStats: React.FC<EmbeddingStatsProps> = ({ className = '' }) => {
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState<EmbeddingStats | null>(null)
  const [batchUpdating, setBatchUpdating] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  
  const { addNotification } = useNotificationStore()

  const fetchStats = async () => {
    setLoading(true)
    try {
      const response = await api.embeddings.stats()
      
      if (response.data.success) {
        setStats(response.data.stats)
        setLastUpdated(new Date())
      } else {
        addNotification({
          type: 'error',
          message: 'Failed to load embedding statistics',
          duration: 5000
        })
      }
    } catch (error) {
      console.error('Error fetching embedding stats:', error)
      addNotification({
        type: 'error',
        message: 'Failed to load embedding statistics',
        duration: 5000
      })
    } finally {
      setLoading(false)
    }
  }

  const handleBatchUpdate = async () => {
    setBatchUpdating(true)
    try {
      const response = await api.embeddings.batchUpdate(50)
      
      if (response.data.success) {
        addNotification({
          type: 'success',
          message: `Updated ${response.data.updated_count} embeddings`,
          duration: 5000
        })
        
        // Refresh stats
        await fetchStats()
      } else {
        addNotification({
          type: 'error',
          message: 'Failed to update embeddings',
          duration: 5000
        })
      }
    } catch (error) {
      console.error('Error updating embeddings:', error)
      addNotification({
        type: 'error',
        message: 'Failed to update embeddings',
        duration: 5000
      })
    } finally {
      setBatchUpdating(false)
    }
  }

  useEffect(() => {
    fetchStats()
  }, [])

  const getCoverageColor = (percentage: number) => {
    if (percentage >= 80) return 'text-green-600'
    if (percentage >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getCoverageBarColor = (percentage: number) => {
    if (percentage >= 80) return 'bg-green-500'
    if (percentage >= 60) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  return (
    <div className={`embedding-stats ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <Brain className="h-6 w-6 text-purple-600" />
          <h3 className="text-xl font-semibold text-gray-900">
            Embedding Statistics
          </h3>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={fetchStats}
            disabled={loading}
            className="flex items-center space-x-1 px-3 py-1 text-sm text-gray-600 hover:text-purple-600 transition-colors"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          
          <button
            onClick={handleBatchUpdate}
            disabled={batchUpdating || !stats}
            className="flex items-center space-x-1 px-3 py-1 text-sm bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors disabled:opacity-50"
          >
            <Zap className={`h-4 w-4 ${batchUpdating ? 'animate-pulse' : ''}`} />
            <span>{batchUpdating ? 'Updating...' : 'Update Embeddings'}</span>
          </button>
        </div>
      </div>

      {stats ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Coverage Overview */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-lg font-medium text-gray-900">Coverage</h4>
              <Activity className="h-5 w-5 text-gray-400" />
            </div>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Total Ideas</span>
                <span className="text-lg font-semibold text-gray-900">
                  {stats.total_ideas.toLocaleString()}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">With Embeddings</span>
                <span className="text-lg font-semibold text-gray-900">
                  {stats.ideas_with_embeddings.toLocaleString()}
                </span>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Coverage</span>
                  <span className={`text-lg font-semibold ${getCoverageColor(stats.coverage_percentage)}`}>
                    {stats.coverage_percentage.toFixed(1)}%
                  </span>
                </div>
                
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-300 ${getCoverageBarColor(stats.coverage_percentage)}`}
                    style={{ width: `${stats.coverage_percentage}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Model Information */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-lg font-medium text-gray-900">Model Info</h4>
              <Database className="h-5 w-5 text-gray-400" />
            </div>
            
            <div className="space-y-3">
              <div>
                <span className="text-sm text-gray-600">Current Model</span>
                <div className="font-mono text-sm text-gray-900 bg-gray-100 px-2 py-1 rounded mt-1">
                  {stats.current_model}
                </div>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Dimensions</span>
                <span className="text-lg font-semibold text-gray-900">
                  {stats.embedding_dimension}
                </span>
              </div>
              
              <div className="pt-2 border-t border-gray-200">
                <span className="text-sm text-gray-600">Model Performance</span>
                <div className="text-xs text-gray-500 mt-1">
                  Balanced speed and accuracy
                </div>
              </div>
            </div>
          </div>

          {/* Model Usage Statistics */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-lg font-medium text-gray-900">Usage</h4>
              <TrendingUp className="h-5 w-5 text-gray-400" />
            </div>
            
            <div className="space-y-3">
              {Object.entries(stats.model_stats).map(([model, count]) => (
                <div key={model} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 font-mono">
                    {model}
                  </span>
                  <span className="text-sm font-medium text-gray-900">
                    {count.toLocaleString()}
                  </span>
                </div>
              ))}
              
              {Object.keys(stats.model_stats).length === 0 && (
                <div className="text-center text-gray-500 text-sm">
                  No embeddings generated yet
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <RefreshCw className={`h-8 w-8 text-gray-400 mx-auto mb-4 ${loading ? 'animate-spin' : ''}`} />
            <p className="text-gray-500">
              {loading ? 'Loading statistics...' : 'Failed to load statistics'}
            </p>
          </div>
        </div>
      )}

      {/* Last Updated */}
      {lastUpdated && (
        <div className="mt-6 text-center text-sm text-gray-500">
          Last updated: {lastUpdated.toLocaleString()}
        </div>
      )}

      {/* Quick Actions */}
      <div className="mt-6 p-4 bg-purple-50 rounded-lg">
        <h4 className="text-sm font-medium text-purple-900 mb-2">
          Quick Actions
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="text-sm text-purple-800">
            <strong>Batch Update:</strong> Generate embeddings for ideas that don't have them
          </div>
          <div className="text-sm text-purple-800">
            <strong>Coverage:</strong> Higher coverage means better semantic search results
          </div>
        </div>
      </div>
    </div>
  )
}

export default EmbeddingStats