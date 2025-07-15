import { useState } from 'react'
import { Link } from 'react-router-dom'
import { 
  Lightbulb, 
  FileText, 
  TrendingUp, 
  Zap,
  Plus,
  Mic,
  Type,
  Moon
} from 'lucide-react'
import { useIdeaStore } from '../stores/ideaStore'
import { useAppStore } from '../stores/appStore'

const HomePage = () => {
  const [textInput, setTextInput] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  
  const { createIdea } = useIdeaStore()
  const { settings } = useAppStore()
  
  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!textInput.trim() || isSubmitting) return
    
    setIsSubmitting(true)
    
    try {
      await createIdea(textInput.trim(), 'text', {
        urgency: settings.defaultUrgency
      })
      
      setTextInput('')
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
    } catch (error) {
      console.error('Failed to create dream:', error)
    }
  }
  
  return (
    <div className="min-h-screen bg-dark-900 mobile-padding">
      <div className="max-w-4xl mx-auto pt-8 pb-24">
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
        
        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <Link to="/ideas" className="card p-6 hover:border-primary-500 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-dark-300 text-sm font-medium">Ideas Captured</h3>
                <p className="text-2xl font-bold text-white mt-1">127</p>
              </div>
              <Lightbulb className="w-8 h-8 text-primary-500" />
            </div>
          </Link>
          
          <Link to="/proposals" className="card p-6 hover:border-primary-500 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-dark-300 text-sm font-medium">Proposals Ready</h3>
                <p className="text-2xl font-bold text-white mt-1">8</p>
              </div>
              <FileText className="w-8 h-8 text-primary-500" />
            </div>
          </Link>
          
          <Link to="/stats" className="card p-6 hover:border-primary-500 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-dark-300 text-sm font-medium">Success Rate</h3>
                <p className="text-2xl font-bold text-white mt-1">94%</p>
              </div>
              <TrendingUp className="w-8 h-8 text-primary-500" />
            </div>
          </Link>
        </div>
        
        {/* Capture Methods */}
        <div className="card p-8 mb-12">
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
                  placeholder="What's your idea? Type it here..."
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
                <span>{isSubmitting ? 'Saving...' : 'Save'}</span>
              </button>
            </div>
          </form>
          
          {/* Other Capture Methods */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="text-center">
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
          </div>
        </div>
        
        {/* Recent Activity */}
        <div className="card p-8">
          <h2 className="text-xl font-semibold text-white mb-6">Recent Activity</h2>
          
          <div className="space-y-4">
            {[
              {
                type: 'idea',
                title: 'AI-powered morning routine optimizer',
                time: '2 minutes ago',
                status: 'Processing'
              },
              {
                type: 'proposal',
                title: 'Dream journal with pattern recognition',
                time: '15 minutes ago',
                status: 'Ready for review'
              },
              {
                type: 'idea',
                title: 'Voice-activated meditation timer',
                time: '1 hour ago',
                status: 'Proposal generated'
              }
            ].map((item, index) => (
              <div key={index} className="flex items-center justify-between p-4 bg-dark-700 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className={`w-2 h-2 rounded-full ${
                    item.status === 'Processing' ? 'bg-yellow-500' :
                    item.status === 'Ready for review' ? 'bg-green-500' :
                    'bg-blue-500'
                  }`} />
                  <div>
                    <p className="text-white font-medium">{item.title}</p>
                    <p className="text-dark-400 text-sm">{item.time}</p>
                  </div>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  item.status === 'Processing' ? 'bg-yellow-600/20 text-yellow-300' :
                  item.status === 'Ready for review' ? 'bg-green-600/20 text-green-300' :
                  'bg-blue-600/20 text-blue-300'
                }`}>
                  {item.status}
                </span>
              </div>
            ))}
          </div>
          
          <div className="mt-6 text-center">
            <Link to="/ideas" className="btn btn-secondary">
              View All Ideas
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HomePage