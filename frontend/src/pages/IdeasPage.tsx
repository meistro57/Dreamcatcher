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
  ExternalLink,
  SortAsc,
  SortDesc,
  Grid,
  List,
  CheckSquare,
  Square,
  Trash2,
  Archive,
  Star,
  Eye,
  MoreHorizontal,
  Calendar,
  Zap,
  Sparkles,
  Target,
  Settings,
  X,
  Plus
} from 'lucide-react'
import { useIdeaStore } from '../stores/ideaStore'
import { useNotificationStore } from '../stores/notificationStore'
import { formatDistanceToNow } from 'date-fns'

type SortOption = 'created_at' | 'urgency_score' | 'novelty_score' | 'title' | 'category'
type ViewMode = 'list' | 'grid'

const IdeasPage = () => {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [selectedSource, setSelectedSource] = useState<string>('')
  const [minUrgency, setMinUrgency] = useState<number>(0)
  const [maxUrgency, setMaxUrgency] = useState<number>(100)
  const [minNovelty, setMinNovelty] = useState<number>(0)
  const [selectedStatus, setSelectedStatus] = useState<string>('')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [dateRange, setDateRange] = useState<{start: string, end: string}>({start: '', end: ''})
  const [sortBy, setSortBy] = useState<SortOption>('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [showFilters, setShowFilters] = useState(false)
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false)
  const [selectedIdeas, setSelectedIdeas] = useState<Set<string>>(new Set())
  const [showBulkActions, setShowBulkActions] = useState(false)
  
  const { ideas, fetchIdeas, isLoading, error, deleteIdea, updateIdea } = useIdeaStore()
  const { success, error: notifyError } = useNotificationStore()
  
  useEffect(() => {
    fetchIdeas()
  }, [fetchIdeas])
  
  // Get all available tags from ideas
  const availableTags = [...new Set(ideas.flatMap(idea => idea.tags))]
  
  // Filter and sort ideas locally
  const filteredAndSortedIdeas = ideas
    .filter(idea => {
      // Search term filter
      if (searchTerm && !idea.content.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false
      }
      
      // Category filter
      if (selectedCategory && idea.category !== selectedCategory) {
        return false
      }
      
      // Source type filter
      if (selectedSource && idea.source_type !== selectedSource) {
        return false
      }
      
      // Status filter
      if (selectedStatus && idea.processing_status !== selectedStatus) {
        return false
      }
      
      // Urgency range filter
      if (idea.urgency_score < minUrgency || idea.urgency_score > maxUrgency) {
        return false
      }
      
      // Novelty filter
      if (idea.novelty_score < minNovelty) {
        return false
      }
      
      // Tags filter
      if (selectedTags.length > 0 && !selectedTags.some(tag => idea.tags.includes(tag))) {
        return false
      }
      
      // Date range filter
      if (dateRange.start && new Date(idea.created_at) < new Date(dateRange.start)) {
        return false
      }
      if (dateRange.end && new Date(idea.created_at) > new Date(dateRange.end)) {
        return false
      }
      
      return true
    })
    .sort((a, b) => {
      let aVal: any, bVal: any
      
      switch (sortBy) {
        case 'created_at':
          aVal = new Date(a.created_at).getTime()
          bVal = new Date(b.created_at).getTime()
          break
        case 'urgency_score':
          aVal = a.urgency_score
          bVal = b.urgency_score
          break
        case 'novelty_score':
          aVal = a.novelty_score
          bVal = b.novelty_score
          break
        case 'title':
          aVal = a.content.toLowerCase()
          bVal = b.content.toLowerCase()
          break
        case 'category':
          aVal = a.category || ''
          bVal = b.category || ''
          break
        default:
          aVal = new Date(a.created_at).getTime()
          bVal = new Date(b.created_at).getTime()
      }
      
      if (sortOrder === 'asc') {
        return aVal > bVal ? 1 : -1
      } else {
        return aVal < bVal ? 1 : -1
      }
    })
  
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
    setSelectedStatus('')
    setMinUrgency(0)
    setMaxUrgency(100)
    setMinNovelty(0)
    setSelectedTags([])
    setDateRange({start: '', end: ''})
    setSortBy('created_at')
    setSortOrder('desc')
    fetchIdeas()
  }
  
  const toggleIdeaSelection = (ideaId: string) => {
    const newSelection = new Set(selectedIdeas)
    if (newSelection.has(ideaId)) {
      newSelection.delete(ideaId)
    } else {
      newSelection.add(ideaId)
    }
    setSelectedIdeas(newSelection)
    setShowBulkActions(newSelection.size > 0)
  }
  
  const selectAllIdeas = () => {
    const allIds = new Set(filteredAndSortedIdeas.map(idea => idea.id))
    setSelectedIdeas(allIds)
    setShowBulkActions(allIds.size > 0)
  }
  
  const clearSelection = () => {
    setSelectedIdeas(new Set())
    setShowBulkActions(false)
  }
  
  const handleBulkDelete = async () => {
    if (window.confirm(`Delete ${selectedIdeas.size} selected ideas?`)) {
      try {
        for (const ideaId of selectedIdeas) {
          await deleteIdea(ideaId)
        }
        success(
          'Ideas Deleted',
          `Successfully deleted ${selectedIdeas.size} ideas.`,
          { source: 'Bulk Actions' }
        )
        clearSelection()
      } catch (err) {
        notifyError(
          'Delete Failed',
          'Failed to delete some ideas. Please try again.',
          { source: 'Bulk Actions' }
        )
      }
    }
  }
  
  const handleBulkArchive = async () => {
    try {
      for (const ideaId of selectedIdeas) {
        await updateIdea(ideaId, { processing_status: 'archived' as any })
      }
      success(
        'Ideas Archived',
        `Successfully archived ${selectedIdeas.size} ideas.`,
        { source: 'Bulk Actions' }
      )
      clearSelection()
    } catch (err) {
      notifyError(
        'Archive Failed',
        'Failed to archive some ideas. Please try again.',
        { source: 'Bulk Actions' }
      )
    }
  }
  
  const toggleTag = (tag: string) => {
    setSelectedTags(prev => 
      prev.includes(tag) 
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    )
  }
  
  const removeTag = (tag: string) => {
    setSelectedTags(prev => prev.filter(t => t !== tag))
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
              {filteredAndSortedIdeas.length} of {ideas.length} ideas • {filteredAndSortedIdeas.filter(i => i.urgency_score > 70).length} high priority
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1 bg-dark-800 rounded-lg p-1">
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded ${viewMode === 'list' ? 'bg-primary-600 text-white' : 'text-dark-400 hover:text-white'}`}
              >
                <List className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded ${viewMode === 'grid' ? 'bg-primary-600 text-white' : 'text-dark-400 hover:text-white'}`}
              >
                <Grid className="w-4 h-4" />
              </button>
            </div>
            
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`btn ${showFilters ? 'btn-primary' : 'btn-secondary'} flex items-center space-x-2`}
            >
              <Filter className="w-4 h-4" />
              <span>Filters</span>
            </button>
          </div>
        </div>
        
        {/* Bulk Actions Bar */}
        {showBulkActions && (
          <div className="bg-primary-600/20 border border-primary-600/30 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <span className="text-white font-medium">
                  {selectedIdeas.size} ideas selected
                </span>
                <button
                  onClick={clearSelection}
                  className="text-primary-400 hover:text-primary-300 text-sm"
                >
                  Clear selection
                </button>
              </div>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleBulkArchive}
                  className="btn btn-secondary btn-sm flex items-center space-x-1"
                >
                  <Archive className="w-4 h-4" />
                  <span>Archive</span>
                </button>
                <button
                  onClick={handleBulkDelete}
                  className="btn btn-danger btn-sm flex items-center space-x-1"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>Delete</span>
                </button>
              </div>
            </div>
          </div>
        )}
        
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
            
            <div className="flex items-center space-x-2">
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortOption)}
                className="input"
              >
                <option value="created_at">Date Created</option>
                <option value="urgency_score">Urgency</option>
                <option value="novelty_score">Novelty</option>
                <option value="title">Title</option>
                <option value="category">Category</option>
              </select>
              
              <button
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                className="btn btn-ghost p-2"
                title={`Sort ${sortOrder === 'asc' ? 'descending' : 'ascending'}`}
              >
                {sortOrder === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />}
              </button>
            </div>
            
            <button
              onClick={selectAllIdeas}
              className="btn btn-secondary flex items-center space-x-2"
            >
              <CheckSquare className="w-4 h-4" />
              <span>Select All</span>
            </button>
          </div>
          
          {/* Selected tags display */}
          {selectedTags.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {selectedTags.map(tag => (
                <span
                  key={tag}
                  className="badge badge-primary flex items-center space-x-1"
                >
                  <span>{tag}</span>
                  <button
                    onClick={() => removeTag(tag)}
                    className="hover:text-red-300"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
          
          {showFilters && (
            <div className="border-t border-dark-600 pt-4 animate-slide-down">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
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
                    <option value="technical">Technical</option>
                    <option value="personal">Personal</option>
                    <option value="metaphysical">Metaphysical</option>
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
                    Status
                  </label>
                  <select
                    value={selectedStatus}
                    onChange={(e) => setSelectedStatus(e.target.value)}
                    className="input w-full"
                  >
                    <option value="">All statuses</option>
                    <option value="pending">Pending</option>
                    <option value="processing">Processing</option>
                    <option value="completed">Completed</option>
                    <option value="failed">Failed</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">
                    <div className="flex items-center space-x-2">
                      <Settings className="w-4 h-4" />
                      <span>Advanced</span>
                    </div>
                  </label>
                  <button
                    onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                    className="btn btn-ghost w-full"
                  >
                    {showAdvancedFilters ? 'Hide' : 'Show'} Advanced
                  </button>
                </div>
              </div>
              
              {showAdvancedFilters && (
                <div className="bg-dark-800 rounded-lg p-4 mb-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <label className="block text-sm font-medium text-dark-300 mb-2">
                        Urgency Range: {minUrgency} - {maxUrgency}
                      </label>
                      <div className="flex items-center space-x-2">
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={minUrgency}
                          onChange={(e) => setMinUrgency(Number(e.target.value))}
                          className="flex-1"
                        />
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={maxUrgency}
                          onChange={(e) => setMaxUrgency(Number(e.target.value))}
                          className="flex-1"
                        />
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-dark-300 mb-2">
                        Min Novelty: {minNovelty}
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={minNovelty}
                        onChange={(e) => setMinNovelty(Number(e.target.value))}
                        className="w-full"
                      />
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <label className="block text-sm font-medium text-dark-300 mb-2">
                        Date Range
                      </label>
                      <div className="flex items-center space-x-2">
                        <input
                          type="date"
                          value={dateRange.start}
                          onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
                          className="input flex-1"
                        />
                        <span className="text-dark-400">to</span>
                        <input
                          type="date"
                          value={dateRange.end}
                          onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
                          className="input flex-1"
                        />
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-dark-300 mb-2">
                        Tags
                      </label>
                      <div className="flex flex-wrap gap-2 max-h-24 overflow-y-auto">
                        {availableTags.map(tag => (
                          <button
                            key={tag}
                            onClick={() => toggleTag(tag)}
                            className={`text-xs px-2 py-1 rounded-full border transition-colors ${
                              selectedTags.includes(tag)
                                ? 'bg-primary-600 border-primary-600 text-white'
                                : 'border-dark-600 text-dark-300 hover:border-primary-500'
                            }`}
                          >
                            {tag}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              <div className="flex items-center justify-between">
                <div className="flex space-x-2">
                  <button onClick={clearFilters} className="btn btn-secondary">
                    Clear All Filters
                  </button>
                  <button
                    onClick={() => {
                      setShowFilters(false)
                      setShowAdvancedFilters(false)
                    }}
                    className="btn btn-ghost"
                  >
                    Hide Filters
                  </button>
                </div>
                
                <div className="text-sm text-dark-400">
                  {filteredAndSortedIdeas.length} results
                </div>
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
        <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4' : 'space-y-4'}>
          {filteredAndSortedIdeas.map((idea) => (
            <div key={idea.id} className={`card p-6 hover:border-primary-500 transition-colors ${
              selectedIdeas.has(idea.id) ? 'border-primary-500 bg-primary-600/10' : ''
            }`}>
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start space-x-3 flex-1">
                  <button
                    onClick={() => toggleIdeaSelection(idea.id)}
                    className="mt-1 text-dark-400 hover:text-primary-400 transition-colors"
                  >
                    {selectedIdeas.has(idea.id) ? (
                      <CheckSquare className="w-4 h-4 text-primary-400" />
                    ) : (
                      <Square className="w-4 h-4" />
                    )}
                  </button>
                  
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
                    
                    <p className={`text-white mb-3 line-clamp-3 ${
                      viewMode === 'grid' ? 'text-base' : 'text-lg'
                    }`}>
                      {idea.content}
                    </p>
                    
                    <div className="flex items-center space-x-4 text-sm text-dark-400">
                      <div className="flex items-center space-x-1">
                        <TrendingUp className="w-4 h-4" />
                        <span className={getUrgencyColor(idea.urgency_score)}>
                          {Math.round(idea.urgency_score)}%
                        </span>
                      </div>
                      
                      <div className="flex items-center space-x-1">
                        <Sparkles className="w-4 h-4" />
                        <span className="text-blue-400">
                          {Math.round(idea.novelty_score)}%
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
                </div>
                
                <div className="flex items-center space-x-2">
                  <Link
                    to={`/ideas/${idea.id}`}
                    className="btn btn-ghost p-2"
                    title="View details"
                  >
                    <Eye className="w-4 h-4" />
                  </Link>
                  
                  <button
                    className="btn btn-ghost p-2"
                    title="More actions"
                  >
                    <MoreHorizontal className="w-4 h-4" />
                  </button>
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
        {filteredAndSortedIdeas.length === 0 && !isLoading && (
          <div className="card p-12 text-center">
            <div className="w-16 h-16 bg-dark-700 rounded-full flex items-center justify-center mx-auto mb-4">
              {ideas.length === 0 ? (
                <Target className="w-8 h-8 text-dark-400" />
              ) : (
                <Search className="w-8 h-8 text-dark-400" />
              )}
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">
              {ideas.length === 0 ? 'No ideas captured yet' : 'No ideas match your filters'}
            </h3>
            <p className="text-dark-400 mb-6">
              {ideas.length === 0 
                ? 'Start capturing your ideas to see them here'
                : 'Try adjusting your search filters or clearing them to see more results'
              }
            </p>
            <div className="flex justify-center space-x-4">
              {ideas.length === 0 ? (
                <Link to="/" className="btn btn-primary">
                  <Plus className="w-4 h-4 mr-2" />
                  Capture Your First Idea
                </Link>
              ) : (
                <button onClick={clearFilters} className="btn btn-primary">
                  <X className="w-4 h-4 mr-2" />
                  Clear All Filters
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default IdeasPage