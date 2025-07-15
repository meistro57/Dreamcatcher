import React, { useState, useEffect } from 'react'
import { Link2, Sparkles, Target, Clock, Star, AlertCircle, RefreshCw } from 'lucide-react'
import { api } from '../../utils/api'
import { useNotificationStore } from '../../stores/notificationStore'

interface RelatedIdeasProps {
  ideaId: string
  className?: string
}

interface RelatedIdea {
  id: string
  content_processed: string
  content_transcribed: string
  content_raw: string
  category: string
  urgency_score: number
  novelty_score: number
  viability_score: number
  created_at: string
  is_favorite: boolean
  is_archived: boolean
  similarity_score: number
}

const RelatedIdeas: React.FC<RelatedIdeasProps> = ({ ideaId, className = '' }) => {
  const [loading, setLoading] = useState(false)
  const [relatedIdeas, setRelatedIdeas] = useState<RelatedIdea[]>([])
  const [threshold, setThreshold] = useState(0.6)
  const [limit, setLimit] = useState(5)
  const [showSettings, setShowSettings] = useState(false)
  
  const { addNotification } = useNotificationStore()

  const fetchRelatedIdeas = async () => {
    setLoading(true)
    try {
      const response = await api.ideas.related(ideaId, { threshold, limit })
      
      if (response.data.success) {
        setRelatedIdeas(response.data.related_ideas)
        
        if (response.data.related_ideas.length === 0) {
          addNotification({
            type: 'info',
            message: 'No related ideas found. Try lowering the similarity threshold.',
            duration: 3000
          })
        }
      } else {
        addNotification({
          type: 'error',
          message: 'Failed to load related ideas',
          duration: 5000
        })
      }
    } catch (error) {
      console.error('Error fetching related ideas:', error)
      addNotification({
        type: 'error',
        message: 'Failed to load related ideas',
        duration: 5000
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (ideaId) {
      fetchRelatedIdeas()
    }
  }, [ideaId, threshold, limit])

  const getCategoryColor = (category: string) => {
    const colors = {
      'creative': 'bg-purple-100 text-purple-800',
      'business': 'bg-blue-100 text-blue-800',
      'personal': 'bg-green-100 text-green-800',
      'technical': 'bg-orange-100 text-orange-800',
      'metaphysical': 'bg-pink-100 text-pink-800',
      'utility': 'bg-gray-100 text-gray-800'
    }
    return colors[category as keyof typeof colors] || 'bg-gray-100 text-gray-800'
  }

  const getSimilarityColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600'
    if (score >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  return (
    <div className={`related-ideas ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Link2 className="h-5 w-5 text-purple-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            Related Ideas
          </h3>
          {loading && <RefreshCw className="h-4 w-4 text-gray-400 animate-spin" />}
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="text-sm text-gray-600 hover:text-purple-600 transition-colors"
          >
            Settings
          </button>
          
          <button
            onClick={fetchRelatedIdeas}
            disabled={loading}
            className="text-sm text-purple-600 hover:text-purple-700 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="mb-4 p-4 bg-gray-50 rounded-lg">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Similarity Threshold: {threshold}
              </label>
              <input
                type="range"
                min="0.1"
                max="1"
                step="0.1"
                value={threshold}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
                className="w-full"
              />
              <span className="text-xs text-gray-500">
                Higher = more similar
              </span>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Results
              </label>
              <select
                value={limit}
                onChange={(e) => setLimit(parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                <option value={3}>3 results</option>
                <option value={5}>5 results</option>
                <option value={10}>10 results</option>
                <option value={15}>15 results</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Related Ideas List */}
      {relatedIdeas.length > 0 ? (
        <div className="space-y-3">
          {relatedIdeas.map((idea) => (
            <div
              key={idea.id}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => {
                // Navigate to idea or open in modal
                console.log('Navigate to idea:', idea.id)
              }}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(idea.category)}`}>
                      {idea.category}
                    </span>
                    
                    {idea.is_favorite && (
                      <Star className="h-4 w-4 text-yellow-500 fill-current" />
                    )}
                    
                    <span className="text-xs text-gray-500">
                      <Clock className="h-3 w-3 inline mr-1" />
                      {formatDate(idea.created_at)}
                    </span>
                  </div>

                  <p className="text-gray-900 text-sm mb-2 line-clamp-3">
                    {idea.content_processed || idea.content_transcribed || idea.content_raw}
                  </p>

                  <div className="flex items-center space-x-4 text-xs text-gray-500">
                    <div className="flex items-center space-x-1">
                      <Target className="h-3 w-3" />
                      <span>Urgency: {idea.urgency_score.toFixed(1)}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Sparkles className="h-3 w-3" />
                      <span>Novelty: {idea.novelty_score.toFixed(1)}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <AlertCircle className="h-3 w-3" />
                      <span>Viability: {idea.viability_score.toFixed(1)}</span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col items-end space-y-1">
                  <div className={`text-sm font-medium ${getSimilarityColor(idea.similarity_score)}`}>
                    {(idea.similarity_score * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-gray-500">
                    similarity
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8">
          {loading ? (
            <div className="flex items-center justify-center">
              <RefreshCw className="h-6 w-6 text-gray-400 animate-spin mr-2" />
              <span className="text-gray-500">Finding related ideas...</span>
            </div>
          ) : (
            <div>
              <Link2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h4 className="text-lg font-medium text-gray-900 mb-2">
                No related ideas found
              </h4>
              <p className="text-gray-500 mb-4">
                Try lowering the similarity threshold or add more ideas with embeddings
              </p>
              <button
                onClick={() => setShowSettings(true)}
                className="text-purple-600 hover:text-purple-700 transition-colors"
              >
                Adjust settings
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default RelatedIdeas