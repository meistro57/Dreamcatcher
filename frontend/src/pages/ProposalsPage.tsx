import { useState } from 'react'
import { FileText, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

const ProposalsPage = () => {
  const [selectedStatus, setSelectedStatus] = useState<string>('all')
  
  // Mock data - replace with actual API call
  const proposals = [
    {
      id: '1',
      title: 'Dream-Powered Meditation App',
      description: 'A meditation app that adapts to your sleep patterns and dream content to provide personalized mindfulness experiences.',
      status: 'pending',
      created_at: '2025-01-15T10:30:00Z',
      idea_id: 'idea-123',
      generated_by: 'agent_proposer'
    },
    {
      id: '2',
      title: 'AI-Driven Morning Routine Optimizer',
      description: 'An intelligent system that learns your daily patterns and optimizes your morning routine for maximum productivity and well-being.',
      status: 'approved',
      created_at: '2025-01-14T15:45:00Z',
      idea_id: 'idea-124',
      generated_by: 'agent_proposer'
    },
    {
      id: '3',
      title: 'Voice-Activated Idea Capture Device',
      description: 'A dedicated hardware device for capturing ideas through voice commands, with offline processing and cloud sync capabilities.',
      status: 'rejected',
      created_at: '2025-01-13T09:20:00Z',
      idea_id: 'idea-125',
      generated_by: 'scheduler'
    }
  ]
  
  const filteredProposals = selectedStatus === 'all' 
    ? proposals 
    : proposals.filter(p => p.status === selectedStatus)
  
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />
      case 'approved':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'rejected':
        return <XCircle className="w-5 h-5 text-red-500" />
      default:
        return <FileText className="w-5 h-5 text-gray-500" />
    }
  }
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-600/20 text-yellow-300 border-yellow-600/30'
      case 'approved':
        return 'bg-green-600/20 text-green-300 border-green-600/30'
      case 'rejected':
        return 'bg-red-600/20 text-red-300 border-red-600/30'
      default:
        return 'bg-gray-600/20 text-gray-300 border-gray-600/30'
    }
  }
  
  const handleApprove = (id: string) => {
    // API call to approve proposal
    console.log('Approving proposal:', id)
  }
  
  const handleReject = (id: string) => {
    // API call to reject proposal
    console.log('Rejecting proposal:', id)
  }
  
  return (
    <div className="min-h-screen bg-dark-900 mobile-padding">
      <div className="max-w-4xl mx-auto pt-8 pb-24">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Proposals</h1>
            <p className="text-dark-300">
              {proposals.length} total • {proposals.filter(p => p.status === 'pending').length} pending review
            </p>
          </div>
        </div>
        
        {/* Status Filter */}
        <div className="card p-6 mb-8">
          <div className="flex space-x-2 mb-4">
            <button
              onClick={() => setSelectedStatus('all')}
              className={`btn ${selectedStatus === 'all' ? 'btn-primary' : 'btn-secondary'}`}
            >
              All ({proposals.length})
            </button>
            <button
              onClick={() => setSelectedStatus('pending')}
              className={`btn ${selectedStatus === 'pending' ? 'btn-primary' : 'btn-secondary'}`}
            >
              Pending ({proposals.filter(p => p.status === 'pending').length})
            </button>
            <button
              onClick={() => setSelectedStatus('approved')}
              className={`btn ${selectedStatus === 'approved' ? 'btn-primary' : 'btn-secondary'}`}
            >
              Approved ({proposals.filter(p => p.status === 'approved').length})
            </button>
            <button
              onClick={() => setSelectedStatus('rejected')}
              className={`btn ${selectedStatus === 'rejected' ? 'btn-primary' : 'btn-secondary'}`}
            >
              Rejected ({proposals.filter(p => p.status === 'rejected').length})
            </button>
          </div>
        </div>
        
        {/* Proposals List */}
        <div className="space-y-6">
          {filteredProposals.map((proposal) => (
            <div key={proposal.id} className="card p-8">
              {/* Header */}
              <div className="flex items-start justify-between mb-6">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    {getStatusIcon(proposal.status)}
                    <h2 className="text-xl font-semibold text-white">
                      {proposal.title}
                    </h2>
                  </div>
                  
                  <div className="flex items-center space-x-4 text-sm text-dark-400">
                    <div className="flex items-center space-x-1">
                      <Clock className="w-4 h-4" />
                      <span>{formatDistanceToNow(new Date(proposal.created_at), { addSuffix: true })}</span>
                    </div>
                    
                    <span className={`badge ${getStatusColor(proposal.status)} capitalize`}>
                      {proposal.status}
                    </span>
                    
                    <span className="text-dark-500">
                      by {proposal.generated_by}
                    </span>
                  </div>
                </div>
              </div>
              
              {/* Description */}
              <div className="mb-8">
                <p className="text-dark-200 text-lg leading-relaxed">
                  {proposal.description}
                </p>
              </div>
              
              {/* Mock proposal sections */}
              <div className="space-y-6 mb-8">
                <div>
                  <h3 className="text-lg font-semibold text-white mb-3">Problem Statement</h3>
                  <p className="text-dark-300">
                    Current meditation apps don't adapt to individual sleep patterns and dream content, 
                    missing opportunities for personalized mindfulness experiences.
                  </p>
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold text-white mb-3">Solution Approach</h3>
                  <p className="text-dark-300">
                    Develop an AI-powered meditation app that analyzes sleep data and dream logs to 
                    provide customized meditation sessions and mindfulness exercises.
                  </p>
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold text-white mb-3">Key Features</h3>
                  <ul className="list-disc list-inside text-dark-300 space-y-1">
                    <li>Dream journal integration with pattern recognition</li>
                    <li>Adaptive meditation session recommendations</li>
                    <li>Sleep quality correlation analysis</li>
                    <li>Personalized mindfulness exercises</li>
                  </ul>
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold text-white mb-3">Implementation Timeline</h3>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-3">
                      <div className="w-2 h-2 bg-primary-500 rounded-full"></div>
                      <span className="text-dark-300">Week 1-2: Research and design</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="w-2 h-2 bg-primary-500 rounded-full"></div>
                      <span className="text-dark-300">Week 3-4: Core app development</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="w-2 h-2 bg-primary-500 rounded-full"></div>
                      <span className="text-dark-300">Week 5-6: AI integration and testing</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className="w-2 h-2 bg-primary-500 rounded-full"></div>
                      <span className="text-dark-300">Week 7-8: Beta testing and launch</span>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Actions */}
              {proposal.status === 'pending' && (
                <div className="flex space-x-4 pt-6 border-t border-dark-600">
                  <button
                    onClick={() => handleApprove(proposal.id)}
                    className="btn btn-primary flex items-center space-x-2"
                  >
                    <CheckCircle className="w-4 h-4" />
                    <span>Approve</span>
                  </button>
                  
                  <button
                    onClick={() => handleReject(proposal.id)}
                    className="btn btn-danger flex items-center space-x-2"
                  >
                    <XCircle className="w-4 h-4" />
                    <span>Reject</span>
                  </button>
                  
                  <button className="btn btn-secondary">
                    Request Changes
                  </button>
                </div>
              )}
              
              {proposal.status === 'approved' && (
                <div className="flex space-x-4 pt-6 border-t border-dark-600">
                  <button className="btn btn-primary">
                    Start Implementation
                  </button>
                  
                  <button className="btn btn-secondary">
                    View Project
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
        
        {/* Empty State */}
        {filteredProposals.length === 0 && (
          <div className="card p-12 text-center">
            <div className="w-16 h-16 bg-dark-700 rounded-full flex items-center justify-center mx-auto mb-4">
              <FileText className="w-8 h-8 text-dark-400" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">
              No {selectedStatus !== 'all' ? selectedStatus : ''} proposals found
            </h3>
            <p className="text-dark-400 mb-6">
              {selectedStatus === 'all' 
                ? 'Capture more ideas to generate proposals'
                : `No proposals with status "${selectedStatus}"`
              }
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default ProposalsPage