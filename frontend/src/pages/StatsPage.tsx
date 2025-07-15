import { useState } from 'react'
import { 
  TrendingUp, 
  Activity, 
  Zap, 
  Clock,
  BarChart3,
  PieChart,
  Calendar,
  Target
} from 'lucide-react'

const StatsPage = () => {
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'year'>('week')
  
  // Mock data - replace with actual API calls
  const stats = {
    ideas: {
      total: 127,
      by_source: {
        voice: 45,
        text: 67,
        dream: 15
      },
      high_urgency: 23
    },
    classification: {
      total_ideas: 127,
      category_counts: {
        business: 34,
        creative: 28,
        utility: 25,
        personal: 23,
        metaphysical: 17
      },
      urgency_distribution: {
        low: 42,
        medium: 62,
        high: 23
      },
      avg_urgency: 58.3
    },
    agents: {
      total_agents: 5,
      active_agents: 5,
      agent_performance: [
        { agent_id: 'listener', total_processed: 127, success_rate: 0.98 },
        { agent_id: 'classifier', total_processed: 127, success_rate: 0.94 },
        { agent_id: 'expander', total_processed: 45, success_rate: 0.89 },
        { agent_id: 'visualizer', total_processed: 23, success_rate: 0.87 },
        { agent_id: 'proposer', total_processed: 12, success_rate: 0.92 }
      ]
    }
  }
  
  const getPercentage = (value: number, total: number) => {
    return Math.round((value / total) * 100)
  }
  
  const getAgentColor = (agentId: string) => {
    const colors = {
      listener: 'bg-blue-500',
      classifier: 'bg-green-500',
      expander: 'bg-purple-500',
      visualizer: 'bg-pink-500',
      proposer: 'bg-orange-500'
    }
    return colors[agentId as keyof typeof colors] || 'bg-gray-500'
  }
  
  return (
    <div className="min-h-screen bg-dark-900 mobile-padding">
      <div className="max-w-6xl mx-auto pt-8 pb-24">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Statistics</h1>
            <p className="text-dark-300">
              System performance and idea analytics
            </p>
          </div>
          
          <div className="flex space-x-2">
            <button
              onClick={() => setTimeRange('week')}
              className={`btn ${timeRange === 'week' ? 'btn-primary' : 'btn-secondary'}`}
            >
              Week
            </button>
            <button
              onClick={() => setTimeRange('month')}
              className={`btn ${timeRange === 'month' ? 'btn-primary' : 'btn-secondary'}`}
            >
              Month
            </button>
            <button
              onClick={() => setTimeRange('year')}
              className={`btn ${timeRange === 'year' ? 'btn-primary' : 'btn-secondary'}`}
            >
              Year
            </button>
          </div>
        </div>
        
        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-primary-600 rounded-full flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
              <span className="text-green-400 text-sm">+12%</span>
            </div>
            <h3 className="text-2xl font-bold text-white mb-1">{stats.ideas.total}</h3>
            <p className="text-dark-400">Total Ideas</p>
          </div>
          
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <span className="text-green-400 text-sm">+8%</span>
            </div>
            <h3 className="text-2xl font-bold text-white mb-1">{stats.agents.active_agents}</h3>
            <p className="text-dark-400">Active Agents</p>
          </div>
          
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-yellow-600 rounded-full flex items-center justify-center">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <span className="text-green-400 text-sm">+15%</span>
            </div>
            <h3 className="text-2xl font-bold text-white mb-1">{stats.ideas.high_urgency}</h3>
            <p className="text-dark-400">High Priority</p>
          </div>
          
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 bg-purple-600 rounded-full flex items-center justify-center">
                <Target className="w-6 h-6 text-white" />
              </div>
              <span className="text-green-400 text-sm">+5%</span>
            </div>
            <h3 className="text-2xl font-bold text-white mb-1">
              {Math.round(stats.classification.avg_urgency)}%
            </h3>
            <p className="text-dark-400">Avg Urgency</p>
          </div>
        </div>
        
        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Ideas by Source */}
          <div className="card p-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-white flex items-center">
                <PieChart className="w-5 h-5 mr-2" />
                Ideas by Source
              </h2>
            </div>
            
            <div className="space-y-4">
              {Object.entries(stats.ideas.by_source).map(([source, count]) => (
                <div key={source} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`w-4 h-4 rounded-full ${
                      source === 'voice' ? 'bg-blue-500' :
                      source === 'text' ? 'bg-green-500' :
                      'bg-purple-500'
                    }`} />
                    <span className="text-dark-300 capitalize">{source}</span>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <div className="w-24 h-2 bg-dark-600 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${
                          source === 'voice' ? 'bg-blue-500' :
                          source === 'text' ? 'bg-green-500' :
                          'bg-purple-500'
                        }`}
                        style={{ width: `${getPercentage(count, stats.ideas.total)}%` }}
                      />
                    </div>
                    <span className="text-white font-medium w-8 text-right">{count}</span>
                    <span className="text-dark-400 text-sm w-8 text-right">
                      {getPercentage(count, stats.ideas.total)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Category Distribution */}
          <div className="card p-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-white flex items-center">
                <BarChart3 className="w-5 h-5 mr-2" />
                Categories
              </h2>
            </div>
            
            <div className="space-y-4">
              {Object.entries(stats.classification.category_counts)
                .sort(([,a], [,b]) => b - a)
                .map(([category, count]) => (
                <div key={category} className="flex items-center justify-between">
                  <span className="text-dark-300 capitalize">{category}</span>
                  <div className="flex items-center space-x-3">
                    <div className="w-24 h-2 bg-dark-600 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary-500"
                        style={{ width: `${getPercentage(count, stats.ideas.total)}%` }}
                      />
                    </div>
                    <span className="text-white font-medium w-8 text-right">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        {/* Agent Performance */}
        <div className="card p-8 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white flex items-center">
              <Activity className="w-5 h-5 mr-2" />
              Agent Performance
            </h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {stats.agents.agent_performance.map((agent) => (
              <div key={agent.agent_id} className="bg-dark-700 rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${getAgentColor(agent.agent_id)}`} />
                    <h3 className="font-semibold text-white capitalize">
                      {agent.agent_id}
                    </h3>
                  </div>
                  <span className="text-dark-400 text-sm">
                    {agent.total_processed} tasks
                  </span>
                </div>
                
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-dark-300 text-sm">Success Rate</span>
                      <span className="text-white font-medium">
                        {Math.round(agent.success_rate * 100)}%
                      </span>
                    </div>
                    <div className="w-full h-2 bg-dark-600 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-green-500"
                        style={{ width: `${agent.success_rate * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Urgency Distribution */}
        <div className="card p-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white flex items-center">
              <Clock className="w-5 h-5 mr-2" />
              Urgency Distribution
            </h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {Object.entries(stats.classification.urgency_distribution).map(([level, count]) => (
              <div key={level} className="text-center">
                <div className={`w-20 h-20 rounded-full mx-auto mb-4 flex items-center justify-center ${
                  level === 'high' ? 'bg-red-600' :
                  level === 'medium' ? 'bg-yellow-600' :
                  'bg-green-600'
                }`}>
                  <span className="text-white font-bold text-lg">{count}</span>
                </div>
                <h3 className="font-semibold text-white capitalize mb-2">{level}</h3>
                <p className="text-dark-400 text-sm">
                  {getPercentage(count, stats.ideas.total)}% of ideas
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default StatsPage