import React, { useState, useEffect } from 'react'
import { Search, Sparkles, Target, Clock, Star, AlertCircle, RefreshCw } from 'lucide-react'
import { api } from '../../utils/api'
import { useNotificationStore } from '../../stores/notificationStore'

interface SemanticSearchProps {
  onResults?: (results: any[]) => void
  className?: string
}

interface SearchResult {
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

const SemanticSearch: React.FC<SemanticSearchProps> = ({ onResults, className = '' }) => {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<SearchResult[]>([])
  const [threshold, setThreshold] = useState(0.5)
  const [limit, setLimit] = useState(10)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [searchType, setSearchType] = useState<'semantic' | 'regular'>('semantic')
  
  const { addNotification } = useNotificationStore()

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    try {
      const response = await api.search.semantic({
        query: query.trim(),
        limit,
        threshold
      })

      if (response.data.success) {
        setResults(response.data.results)
        onResults?.(response.data.results)
        
        addNotification({
          type: 'success',
          message: `Found ${response.data.results.length} semantically similar ideas`,
          duration: 3000
        })
      } else {
        addNotification({
          type: 'error',
          message: 'Search failed. Please try again.',
          duration: 5000
        })
      }
    } catch (error) {
      console.error('Search error:', error)
      addNotification({
        type: 'error',
        message: 'Search failed. Please try again.',
        duration: 5000
      })
    } finally {
      setLoading(false)
    }
  }

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
    <div className={`semantic-search ${className}`}>
      {/* Search Form */}
      <form onSubmit={handleSearch} className="space-y-4">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Sparkles className="h-5 w-5 text-purple-500" />
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search ideas by meaning and context..."
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
          >
            {loading ? (
              <RefreshCw className="h-5 w-5 text-gray-400 animate-spin" />
            ) : (
              <Search className="h-5 w-5 text-gray-400 hover:text-purple-500 transition-colors" />
            )}
          </button>
        </div>

        {/* Advanced Options */}
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-sm text-gray-600 hover:text-purple-600 transition-colors"
          >
            {showAdvanced ? 'Hide' : 'Show'} Advanced Options
          </button>
          
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <Sparkles className="h-4 w-4" />
            <span>Semantic Search</span>
          </div>
        </div>

        {showAdvanced && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Similarity Threshold
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
                {threshold} (Higher = more similar)
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
                <option value={5}>5 results</option>
                <option value={10}>10 results</option>
                <option value={20}>20 results</option>
                <option value={50}>50 results</option>
              </select>
            </div>
          </div>
        )}
      </form>

      {/* Results */}
      {results.length > 0 && (
        <div className="mt-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">
              Search Results ({results.length})
            </h3>
            <div className="text-sm text-gray-500">
              Sorted by semantic similarity
            </div>
          </div>

          <div className="space-y-3">
            {results.map((result) => (
              <div
                key={result.id}
                className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(result.category)}`}>
                        {result.category}
                      </span>
                      
                      {result.is_favorite && (
                        <Star className="h-4 w-4 text-yellow-500 fill-current" />
                      )}
                      
                      <span className="text-xs text-gray-500">
                        <Clock className="h-3 w-3 inline mr-1" />
                        {formatDate(result.created_at)}
                      </span>
                    </div>

                    <p className="text-gray-900 text-sm mb-2">
                      {result.content_processed || result.content_transcribed || result.content_raw}
                    </p>

                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <div className="flex items-center space-x-1">
                        <Target className="h-3 w-3" />
                        <span>Urgency: {result.urgency_score.toFixed(1)}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Sparkles className="h-3 w-3" />
                        <span>Novelty: {result.novelty_score.toFixed(1)}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <AlertCircle className="h-3 w-3" />
                        <span>Viability: {result.viability_score.toFixed(1)}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-col items-end space-y-1">
                    <div className={`text-sm font-medium ${getSimilarityColor(result.similarity_score)}`}>
                      {(result.similarity_score * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-500">
                      similarity
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && results.length === 0 && query && (
        <div className="mt-6 text-center py-8">
          <Sparkles className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No similar ideas found
          </h3>
          <p className="text-gray-500 mb-4">
            Try adjusting your search terms or lowering the similarity threshold
          </p>
          <button
            onClick={() => setShowAdvanced(true)}
            className="text-purple-600 hover:text-purple-700 transition-colors"
          >
            Adjust search settings
          </button>
        </div>
      )}
    </div>
  )
}

export default SemanticSearch