import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { 
  Search, 
  Filter, 
  Mic, 
  Type, 
  Moon, 
  Image,
  TrendingUp,
  Clock,
  Tag,
  ExternalLink
} from 'lucide-react'
import { useIdeaStore } from '../stores/ideaStore'
import { formatDistanceToNow } from 'date-fns'

const IdeasPage = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [selectedSource, setSelectedSource] = useState<string>('')
  const [minUrgency, setMinUrgency] = useState<number>(0)
  const [showFilters, setShowFilters] = useState(false)
  
  const { ideas, fetchIdeas, isLoading, error } = useIdeaStore()
  
  useEffect(() => {
    fetchIdeas()
  }, [fetchIdeas])
  
  const handleSearch = () => {
    const filter = {
      search: searchTerm || undefined,
      category: selectedCategory || undefined,
      source_type: selectedSource || undefined,
      min_urgency: minUrgency > 0 ? minUrgency : undefined
    }
    
    fetchIdeas(filter)
  }
  
  const clearFilters = () => {
    setSearchTerm('')
    setSelectedCategory('')
    setSelectedSource('')
    setMinUrgency(0)
    fetchIdeas()
  }
  
  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'voice': return <Mic className="w-4 h-4" />
      case 'text': return <Type className="w-4 h-4" />
      case 'dream': return <Moon className="w-4 h-4" />
      case 'image': return <Image className="w-4 h-4" />
      default: return <Type className="w-4 h-4" />
    }
  }
  
  const getUrgencyColor = (score: number) => {
    if (score >= 80) return 'text-red-400'
    if (score >= 60) return 'text-yellow-400'
    if (score >= 40) return 'text-blue-400'
    return 'text-gray-400'
  }
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-600/20 text-green-300'
      case 'processing': return 'bg-yellow-600/20 text-yellow-300'
      case 'failed': return 'bg-red-600/20 text-red-300'
      default: return 'bg-gray-600/20 text-gray-300'
    }
  }
  
  if (isLoading) {
    return (
      <div className="min-h-screen bg-dark-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-dark-300">Loading ideas...</p>
        </div>
      </div>
    )
  }
  
  return (
    <div className="min-h-screen bg-dark-900 mobile-padding">
      <div className="max-w-6xl mx-auto pt-8 pb-24">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Ideas</h1>
            <p className="text-dark-300">
              {ideas.length} ideas captured • {ideas.filter(i => i.urgency_score > 70).length} high priority
            </p>
          </div>
          
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="btn btn-secondary flex items-center space-x-2"
          >
            <Filter className="w-4 h-4" />
            <span>Filters</span>
          </button>
        </div>
        
        {/* Search and Filters */}
        <div className="card p-6 mb-8">
          <div className="flex space-x-4 mb-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-dark-400" />
                <input
                  type="text"
                  placeholder="Search ideas..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="input pl-10 w-full"
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                />
              </div>
            </div>
            <button onClick={handleSearch} className="btn btn-primary">
              Search
            </button>
          </div>
          
          {showFilters && (
            <div className="border-t border-dark-600 pt-4 animate-slide-down">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">
                    Category
                  </label>
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="input w-full"
                  >
                    <option value="">All categories</option>
                    <option value="creative">Creative</option>
                    <option value="business">Business</option>
                    <option value="personal">Personal</option>
                    <option value="metaphysical">Metaphysical</option>
                    <option value="utility">Utility</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">
                    Source Type
                  </label>
                  <select
                    value={selectedSource}
                    onChange={(e) => setSelectedSource(e.target.value)}
                    className="input w-full"
                  >
                    <option value="">All sources</option>
                    <option value="voice">Voice</option>
                    <option value="text">Text</option>
                    <option value="dream">Dream</option>
                    <option value="image">Image</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">
                    Min Urgency: {minUrgency}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={minUrgency}
                    onChange={(e) => setMinUrgency(Number(e.target.value))}
                    className="w-full"
                  />
                </div>
              </div>
              
              <div className="flex space-x-2">
                <button onClick={handleSearch} className="btn btn-primary">
                  Apply Filters
                </button>
                <button onClick={clearFilters} className="btn btn-secondary">
                  Clear All
                </button>
              </div>
            </div>
          )}
        </div>
        
        {/* Error Message */}
        {error && (
          <div className="bg-red-600/20 border border-red-600/30 text-red-300 p-4 rounded-lg mb-8">
            {error}
          </div>
        )}
        
        {/* Ideas List */}
        <div className="space-y-4">
          {ideas.map((idea) => (
            <div key={idea.id} className="card p-6 hover:border-primary-500 transition-colors">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <div className="flex items-center space-x-2 text-dark-400">
                      {getSourceIcon(idea.source_type)}
                      <span className="text-sm capitalize">{idea.source_type}</span>
                    </div>
                    
                    {idea.category && (
                      <span className="badge badge-secondary capitalize">
                        {idea.category}
                      </span>
                    )}
                    
                    <span className={`badge ${getStatusColor(idea.processing_status)}`}>
                      {idea.processing_status}
                    </span>
                  </div>
                  
                  <p className="text-white text-lg mb-3 line-clamp-3">
                    {idea.content}
                  </p>
                  
                  <div className="flex items-center space-x-4 text-sm text-dark-400">
                    <div className="flex items-center space-x-1">
                      <TrendingUp className="w-4 h-4" />
                      <span className={getUrgencyColor(idea.urgency_score)}>
                        {Math.round(idea.urgency_score)}% urgent
                      </span>
                    </div>
                    
                    <div className="flex items-center space-x-1">
                      <Clock className="w-4 h-4" />
                      <span>{formatDistanceToNow(new Date(idea.created_at), { addSuffix: true })}</span>
                    </div>
                    
                    {idea.tags.length > 0 && (
                      <div className="flex items-center space-x-1">
                        <Tag className="w-4 h-4" />
                        <span>{idea.tags.slice(0, 2).join(', ')}</span>
                        {idea.tags.length > 2 && <span>+{idea.tags.length - 2}</span>}
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Link
                    to={`/ideas/${idea.id}`}
                    className="btn btn-ghost p-2"
                    title="View details"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </Link>
                </div>
              </div>
              
              {/* Expansions Preview */}
              {idea.expansions && idea.expansions.length > 0 && (
                <div className="border-t border-dark-600 pt-4">
                  <div className="text-sm text-dark-400 mb-2">
                    {idea.expansions.length} expansion{idea.expansions.length !== 1 ? 's' : ''}
                  </div>
                  <div className="text-dark-300 text-sm line-clamp-2">
                    {idea.expansions[0].substring(0, 150)}...
                  </div>
                </div>
              )}
              
              {/* Visuals Preview */}
              {idea.visuals && idea.visuals.length > 0 && (
                <div className="border-t border-dark-600 pt-4">
                  <div className="text-sm text-dark-400 mb-2">
                    {idea.visuals.length} visual{idea.visuals.length !== 1 ? 's' : ''}
                  </div>
                  <div className="flex space-x-2">
                    {idea.visuals.slice(0, 3).map((visual, index) => (
                      <div key={index} className="w-12 h-12 bg-dark-700 rounded-lg flex items-center justify-center">
                        <Image className="w-6 h-6 text-dark-400" />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
        
        {/* Empty State */}
        {ideas.length === 0 && !isLoading && (
          <div className="card p-12 text-center">
            <div className="w-16 h-16 bg-dark-700 rounded-full flex items-center justify-center mx-auto mb-4">
              <Search className="w-8 h-8 text-dark-400" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">No ideas found</h3>
            <p className="text-dark-400 mb-6">
              {searchTerm || selectedCategory || selectedSource || minUrgency > 0
                ? 'Try adjusting your search filters'
                : 'Start capturing your ideas to see them here'
              }
            </p>
            <Link to="/" className="btn btn-primary">
              Capture Your First Idea
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}

export default IdeasPage