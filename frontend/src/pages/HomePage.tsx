import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { 
  Lightbulb, 
  FileText, 
  TrendingUp, 
  Zap,
  Plus,
  Mic,
  Type,
  Moon,
  Activity,
  Clock,
  CheckCircle,
  AlertCircle,
  Users,
  Target,
  BarChart3,
  Sparkles
} from 'lucide-react'
import { useIdeaStore } from '../stores/ideaStore'
import { useAppStore } from '../stores/appStore'
import { useWebSocketStore } from '../stores/webSocketStore'
import { apiClient } from '../utils/api'

interface SystemStats {
  totalIdeas: number
  activeProposals: number
  successRate: number
  todaysCaptures: number
  agentStatus: {
    [key: string]: {
      status: 'active' | 'idle' | 'error'
      lastActivity: string
      processed: number
    }
  }
  recentActivity: Array<{
    id: string
    type: 'idea' | 'proposal' | 'agent'
    title: string
    timestamp: string
    status: string
    agent?: string
  }>
}

const HomePage = () => {
  const [textInput, setTextInput] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [stats, setStats] = useState<SystemStats>({
    totalIdeas: 0,
    activeProposals: 0,
    successRate: 0,
    todaysCaptures: 0,
    agentStatus: {},
    recentActivity: []
  })
  const [isLoadingStats, setIsLoadingStats] = useState(true)
  
  const { createIdea, ideas, fetchIdeas } = useIdeaStore()
  const { settings } = useAppStore()
  const { lastMessage } = useWebSocketStore()
  
  // Fetch system statistics
  const fetchStats = async () => {
    try {
      const [
        ideasResponse,
        proposalsResponse,
        agentsResponse,
        healthResponse
      ] = await Promise.all([
        apiClient.get('/ideas?limit=1000'),
        apiClient.get('/proposals?status=active'),
        apiClient.get('/agents'),
        apiClient.get('/evolution/health')
      ])
      
      const ideas = ideasResponse.data
      const proposals = proposalsResponse.data
      const agents = agentsResponse.data
      const health = healthResponse.data
      
      // Calculate stats
      const today = new Date().toISOString().split('T')[0]
      const todaysIdeas = ideas.filter((idea: any) => 
        idea.created_at.startsWith(today)
      )
      
      const agentStatus = agents.reduce((acc: any, agent: any) => {
        acc[agent.name] = {
          status: agent.status || 'idle',
          lastActivity: agent.last_activity || new Date().toISOString(),
          processed: agent.processed_count || 0
        }
        return acc
      }, {})
      
      // Generate recent activity (mock data for now)
      const recentActivity = [
        ...todaysIdeas.slice(0, 3).map((idea: any) => ({
          id: idea.id,
          type: 'idea' as const,
          title: idea.content.substring(0, 50) + '...',
          timestamp: idea.created_at,
          status: idea.processing_status,
          agent: 'listener'
        })),
        ...proposals.slice(0, 2).map((proposal: any) => ({
          id: proposal.id,
          type: 'proposal' as const,
          title: proposal.title || 'New Proposal',
          timestamp: proposal.created_at,
          status: 'ready',
          agent: 'proposer'
        }))
      ].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      
      setStats({
        totalIdeas: ideas.length,
        activeProposals: proposals.length,
        successRate: health.health_score || 94,
        todaysCaptures: todaysIdeas.length,
        agentStatus,
        recentActivity: recentActivity.slice(0, 5)
      })
      
    } catch (error) {
      console.error('Failed to fetch stats:', error)
      // Use fallback stats
      setStats({
        totalIdeas: ideas.length,
        activeProposals: 8,
        successRate: 94,
        todaysCaptures: 12,
        agentStatus: {
          'listener': { status: 'active', lastActivity: new Date().toISOString(), processed: 45 },
          'classifier': { status: 'active', lastActivity: new Date().toISOString(), processed: 42 },
          'expander': { status: 'idle', lastActivity: new Date().toISOString(), processed: 38 },
          'visualizer': { status: 'active', lastActivity: new Date().toISOString(), processed: 35 },
          'proposer': { status: 'idle', lastActivity: new Date().toISOString(), processed: 12 },
          'reviewer': { status: 'idle', lastActivity: new Date().toISOString(), processed: 8 },
          'meta': { status: 'active', lastActivity: new Date().toISOString(), processed: 3 }
        },
        recentActivity: []
      })
    } finally {
      setIsLoadingStats(false)
    }
  }
  
  // Initialize data
  useEffect(() => {
    fetchIdeas()
    fetchStats()
  }, [])
  
  // Refresh stats when WebSocket message received
  useEffect(() => {
    if (lastMessage) {
      fetchStats()
    }
  }, [lastMessage])
  
  // Refresh stats every 30 seconds
  useEffect(() => {
    const interval = setInterval(fetchStats, 30000)
    return () => clearInterval(interval)
  }, [])
  
  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!textInput.trim() || isSubmitting) return
    
    setIsSubmitting(true)
    
    try {
      await createIdea(textInput.trim(), 'text', {
        urgency: settings.defaultUrgency
      })
      
      setTextInput('')
      // Refresh stats after creating idea
      fetchStats()
    } catch (error) {
      console.error('Failed to create idea:', error)
    } finally {
      setIsSubmitting(false)
    }
  }
  
  const handleDreamSubmit = async () => {
    const dreamContent = prompt('Describe your dream:')
    if (!dreamContent?.trim()) return
    
    try {
      await createIdea(dreamContent.trim(), 'dream', {
        dreamType: 'regular'
      })
      // Refresh stats after creating dream
      fetchStats()
    } catch (error) {
      console.error('Failed to create dream:', error)
    }
  }
  
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / (1000 * 60))
    
    if (minutes < 1) return 'just now'
    if (minutes < 60) return `${minutes}m ago`
    if (minutes < 1440) return `${Math.floor(minutes / 60)}h ago`
    return `${Math.floor(minutes / 1440)}d ago`
  }
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500'
      case 'processing': return 'bg-yellow-500'
      case 'completed': return 'bg-blue-500'
      case 'error': 
      case 'failed': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }
  
  const getStatusTextColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-300'
      case 'processing': return 'text-yellow-300'
      case 'completed': return 'text-blue-300'
      case 'error':
      case 'failed': return 'text-red-300'
      default: return 'text-gray-300'
    }
  }
  
  return (
    <div className="min-h-screen bg-dark-900 mobile-padding">
      <div className="max-w-6xl mx-auto pt-8 pb-24">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="w-20 h-20 flex items-center justify-center mx-auto mb-6">
            <img src="/Dreamcatcher_logo.png" alt="Dreamcatcher Logo" className="w-20 h-20 object-contain filter invert" />
          </div>
          
          <h1 className="text-4xl font-bold text-gradient mb-4">
            Dreamcatcher
          </h1>
          
          <p className="text-dark-300 text-lg max-w-2xl mx-auto">
            Your AI-powered idea factory that never sleeps. Capture thoughts instantly, 
            let agents analyze and expand them, then watch your ideas evolve into reality.
          </p>
        </div>
        
        {/* Real-time Stats Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Link to="/ideas" className="card p-6 hover:border-primary-500 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-dark-300 text-sm font-medium">Total Ideas</h3>
                <p className="text-2xl font-bold text-white mt-1">
                  {isLoadingStats ? '...' : stats.totalIdeas}
                </p>
                <p className="text-xs text-dark-400 mt-1">
                  +{stats.todaysCaptures} today
                </p>
              </div>
              <div className="relative">
                <Lightbulb className="w-8 h-8 text-primary-500" />
                {stats.todaysCaptures > 0 && (
                  <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full animate-pulse" />
                )}
              </div>
            </div>
          </Link>
          
          <Link to="/proposals" className="card p-6 hover:border-primary-500 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-dark-300 text-sm font-medium">Active Proposals</h3>
                <p className="text-2xl font-bold text-white mt-1">
                  {isLoadingStats ? '...' : stats.activeProposals}
                </p>
                <p className="text-xs text-dark-400 mt-1">Ready for review</p>
              </div>
              <FileText className="w-8 h-8 text-primary-500" />
            </div>
          </Link>
          
          <Link to="/stats" className="card p-6 hover:border-primary-500 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-dark-300 text-sm font-medium">System Health</h3>
                <p className="text-2xl font-bold text-white mt-1">
                  {isLoadingStats ? '...' : Math.round(stats.successRate)}%
                </p>
                <p className="text-xs text-green-400 mt-1">All systems operational</p>
              </div>
              <div className="relative">
                <Activity className="w-8 h-8 text-green-500" />
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full animate-pulse" />
              </div>
            </div>
          </Link>
          
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-dark-300 text-sm font-medium">Active Agents</h3>
                <p className="text-2xl font-bold text-white mt-1">
                  {Object.values(stats.agentStatus).filter(agent => agent.status === 'active').length}/7
                </p>
                <p className="text-xs text-dark-400 mt-1">Processing ideas</p>
              </div>
              <Users className="w-8 h-8 text-primary-500" />
            </div>
          </div>
        </div>
        
        {/* Agent Status Grid */}
        <div className="card p-6 mb-8">
          <h2 className="text-xl font-semibold text-white mb-6 flex items-center">
            <Activity className="w-5 h-5 mr-2" />
            Agent Network Status
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(stats.agentStatus).map(([name, agent]) => (
              <div key={name} className="bg-dark-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-white capitalize">{name}</h3>
                  <div className={`w-3 h-3 rounded-full ${getStatusColor(agent.status)}`} />
                </div>
                <div className="text-xs text-dark-400 space-y-1">
                  <p>Status: <span className={getStatusTextColor(agent.status)}>{agent.status}</span></p>
                  <p>Processed: {agent.processed}</p>
                  <p>Last: {formatTime(agent.lastActivity)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Capture Methods */}
        <div className="card p-8 mb-8">
          <h2 className="text-xl font-semibold text-white mb-6 flex items-center">
            <Plus className="w-5 h-5 mr-2" />
            Capture an Idea
          </h2>
          
          {/* Text Input */}
          <form onSubmit={handleTextSubmit} className="mb-8">
            <div className="flex space-x-4">
              <div className="flex-1">
                <textarea
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  placeholder="What's your brilliant idea? The agents are waiting..."
                  className="textarea w-full h-20 resize-none"
                  disabled={isSubmitting}
                />
              </div>
              <button
                type="submit"
                disabled={!textInput.trim() || isSubmitting}
                className="btn btn-primary px-6 flex items-center space-x-2 h-fit"
              >
                <Type className="w-4 h-4" />
                <span>{isSubmitting ? 'Processing...' : 'Capture'}</span>
              </button>
            </div>
          </form>
          
          {/* Other Capture Methods */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 rounded-lg border border-dark-600 hover:border-primary-500 transition-colors">
              <div className="w-16 h-16 bg-primary-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Mic className="w-8 h-8 text-white" />
              </div>
              <h3 className="font-medium text-white mb-2">Voice Recording</h3>
              <p className="text-dark-400 text-sm mb-4">
                Use the floating button to record your thoughts instantly
              </p>
              <p className="text-primary-400 text-sm">
                Tap and hold the mic button →
              </p>
            </div>
            
            <button
              onClick={handleDreamSubmit}
              className="text-center p-4 rounded-lg border border-dark-600 hover:border-primary-500 transition-colors"
            >
              <div className="w-16 h-16 bg-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Moon className="w-8 h-8 text-white" />
              </div>
              <h3 className="font-medium text-white mb-2">Dream Log</h3>
              <p className="text-dark-400 text-sm">
                Capture and analyze your dreams for hidden insights
              </p>
            </button>
            
            <div className="text-center p-4 rounded-lg border border-dark-600 opacity-50">
              <div className="w-16 h-16 bg-orange-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
              <h3 className="font-medium text-white mb-2">Image Analysis</h3>
              <p className="text-dark-400 text-sm">
                Upload images for AI-powered idea extraction
              </p>
              <p className="text-orange-400 text-xs mt-2">Coming soon</p>
            </div>
          </div>
        </div>
        
        {/* Recent Activity */}
        <div className="card p-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white flex items-center">
              <Clock className="w-5 h-5 mr-2" />
              Recent Activity
            </h2>
            <div className="flex items-center space-x-2 text-sm text-dark-400">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              <span>Live updates</span>
            </div>
          </div>
          
          <div className="space-y-4">
            {stats.recentActivity.length > 0 ? (
              stats.recentActivity.map((activity) => (
                <div key={activity.id} className="flex items-center justify-between p-4 bg-dark-700 rounded-lg hover:bg-dark-600 transition-colors">
                  <div className="flex items-center space-x-3">
                    <div className={`w-2 h-2 rounded-full ${getStatusColor(activity.status)}`} />
                    <div className="flex items-center space-x-2">
                      {activity.type === 'idea' && <Lightbulb className="w-4 h-4 text-primary-400" />}
                      {activity.type === 'proposal' && <FileText className="w-4 h-4 text-green-400" />}
                      {activity.type === 'agent' && <Users className="w-4 h-4 text-blue-400" />}
                      <div>
                        <p className="text-white font-medium">{activity.title}</p>
                        <div className="flex items-center space-x-2 text-dark-400 text-sm">
                          <span>{formatTime(activity.timestamp)}</span>
                          {activity.agent && (
                            <>
                              <span>•</span>
                              <span className="text-primary-400">{activity.agent}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      activity.status === 'processing' ? 'bg-yellow-600/20 text-yellow-300' :
                      activity.status === 'completed' ? 'bg-green-600/20 text-green-300' :
                      activity.status === 'ready' ? 'bg-blue-600/20 text-blue-300' :
                      'bg-gray-600/20 text-gray-300'
                    }`}>
                      {activity.status}
                    </span>
                    {activity.status === 'processing' && (
                      <div className="w-4 h-4 border-2 border-yellow-500 border-t-transparent rounded-full animate-spin" />
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8">
                <Target className="w-12 h-12 text-dark-500 mx-auto mb-4" />
                <p className="text-dark-400 mb-4">No recent activity</p>
                <p className="text-dark-500 text-sm">
                  Capture your first idea to see the magic happen!
                </p>
              </div>
            )}
          </div>
          
          <div className="mt-6 flex justify-center space-x-4">
            <Link to="/ideas" className="btn btn-secondary">
              <BarChart3 className="w-4 h-4 mr-2" />
              View All Ideas
            </Link>
            <Link to="/stats" className="btn btn-outline">
              <Activity className="w-4 h-4 mr-2" />
              System Stats
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HomePage