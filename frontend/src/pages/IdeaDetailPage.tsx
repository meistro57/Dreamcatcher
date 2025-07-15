import { useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Clock, Tag, TrendingUp, Mic, Type, Moon, Image } from 'lucide-react'
import { useIdeaStore } from '../stores/ideaStore'
import { formatDistanceToNow } from 'date-fns'

const IdeaDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const { currentIdea, fetchIdeaById, isLoading, error } = useIdeaStore()
  
  useEffect(() => {
    if (id) {
      fetchIdeaById(id)
    }
  }, [id, fetchIdeaById])
  
  if (isLoading) {
    return (
      <div className="min-h-screen bg-dark-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-dark-300">Loading idea...</p>
        </div>
      </div>
    )
  }
  
  if (error || !currentIdea) {
    return (
      <div className="min-h-screen bg-dark-900 flex items-center justify-center mobile-padding">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white mb-4">Idea Not Found</h1>
          <p className="text-dark-300 mb-6">{error || 'This idea doesn\'t exist or has been deleted.'}</p>
          <Link to="/ideas" className="btn btn-primary">
            Back to Ideas
          </Link>
        </div>
      </div>
    )
  }
  
  const getSourceIcon = (source: string) => {
    switch (source) {
      case 'voice': return <Mic className="w-5 h-5" />
      case 'text': return <Type className="w-5 h-5" />
      case 'dream': return <Moon className="w-5 h-5" />
      case 'image': return <Image className="w-5 h-5" />
      default: return <Type className="w-5 h-5" />
    }
  }
  
  const getUrgencyColor = (score: number) => {
    if (score >= 80) return 'text-red-400'
    if (score >= 60) return 'text-yellow-400'
    if (score >= 40) return 'text-blue-400'
    return 'text-gray-400'
  }
  
  return (
    <div className="min-h-screen bg-dark-900 mobile-padding">
      <div className="max-w-4xl mx-auto pt-8 pb-24">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <Link 
            to="/ideas"
            className="btn btn-ghost flex items-center space-x-2"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Ideas</span>
          </Link>
        </div>
        
        {/* Main Content */}
        <div className="card p-8 mb-8">
          {/* Metadata */}
          <div className="flex items-center space-x-4 mb-6">
            <div className="flex items-center space-x-2 text-dark-400">
              {getSourceIcon(currentIdea.source_type)}
              <span className="capitalize">{currentIdea.source_type}</span>
            </div>
            
            {currentIdea.category && (
              <span className="badge badge-secondary capitalize">
                {currentIdea.category}
              </span>
            )}
            
            <div className="flex items-center space-x-1">
              <Clock className="w-4 h-4 text-dark-400" />
              <span className="text-dark-400 text-sm">
                {formatDistanceToNow(new Date(currentIdea.created_at), { addSuffix: true })}
              </span>
            </div>
          </div>
          
          {/* Content */}
          <div className="prose prose-invert max-w-none mb-8">
            <p className="text-xl text-white leading-relaxed whitespace-pre-wrap">
              {currentIdea.content}
            </p>
          </div>
          
          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-dark-700 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <TrendingUp className="w-5 h-5 text-primary-500" />
                <span className="text-dark-300">Urgency Score</span>
              </div>
              <div className={`text-2xl font-bold ${getUrgencyColor(currentIdea.urgency_score)}`}>
                {Math.round(currentIdea.urgency_score)}%
              </div>
            </div>
            
            <div className="bg-dark-700 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <span className="w-5 h-5 text-purple-500 flex items-center justify-center text-sm">✨</span>
                <span className="text-dark-300">Novelty Score</span>
              </div>
              <div className="text-2xl font-bold text-purple-400">
                {Math.round(currentIdea.novelty_score)}%
              </div>
            </div>
            
            <div className="bg-dark-700 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-2">
                <span className="w-5 h-5 text-green-500 flex items-center justify-center text-sm">⚡</span>
                <span className="text-dark-300">Status</span>
              </div>
              <div className="text-lg font-semibold text-green-400 capitalize">
                {currentIdea.processing_status}
              </div>
            </div>
          </div>
          
          {/* Tags */}
          {currentIdea.tags.length > 0 && (
            <div className="mb-8">
              <div className="flex items-center space-x-2 mb-3">
                <Tag className="w-5 h-5 text-dark-400" />
                <span className="text-dark-300 font-medium">Tags</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {currentIdea.tags.map((tag, index) => (
                  <span key={index} className="badge badge-primary">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
        
        {/* Expansions */}
        {currentIdea.expansions && currentIdea.expansions.length > 0 && (
          <div className="card p-8 mb-8">
            <h2 className="text-xl font-semibold text-white mb-6">AI Expansions</h2>
            <div className="space-y-6">
              {currentIdea.expansions.map((expansion, index) => (
                <div key={index} className="border-l-4 border-primary-600 pl-6">
                  <div className="prose prose-invert max-w-none">
                    <p className="text-dark-200 whitespace-pre-wrap">{expansion}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Visuals */}
        {currentIdea.visuals && currentIdea.visuals.length > 0 && (
          <div className="card p-8 mb-8">
            <h2 className="text-xl font-semibold text-white mb-6">Generated Visuals</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {currentIdea.visuals.map((visual, index) => (
                <div key={index} className="bg-dark-700 rounded-lg p-4">
                  <div className="aspect-video bg-dark-600 rounded-lg mb-4 flex items-center justify-center">
                    <Image className="w-12 h-12 text-dark-400" />
                  </div>
                  <div className="text-sm text-dark-400">
                    <strong>Prompt:</strong> {visual.prompt}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Actions */}
        <div className="card p-8">
          <h2 className="text-xl font-semibold text-white mb-6">Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button className="btn btn-primary">
              Generate Proposal
            </button>
            <button className="btn btn-secondary">
              Create Visual
            </button>
            <button className="btn btn-secondary">
              Expand Idea
            </button>
            <button className="btn btn-secondary">
              Find Related Ideas
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default IdeaDetailPage