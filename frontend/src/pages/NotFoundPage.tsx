import { Link } from 'react-router-dom'
import { Home, ArrowLeft } from 'lucide-react'

const NotFoundPage = () => {
  return (
    <div className="min-h-screen bg-dark-900 flex items-center justify-center mobile-padding">
      <div className="text-center">
        <div className="mb-8">
          <div className="text-6xl font-bold text-dark-600 mb-4">404</div>
          <h1 className="text-3xl font-bold text-white mb-2">Page Not Found</h1>
          <p className="text-dark-300 text-lg">
            The page you're looking for doesn't exist or has been moved.
          </p>
        </div>
        
        <div className="space-x-4">
          <Link 
            to="/" 
            className="btn btn-primary inline-flex items-center space-x-2"
          >
            <Home className="w-4 h-4" />
            <span>Go Home</span>
          </Link>
          
          <button 
            onClick={() => window.history.back()}
            className="btn btn-secondary inline-flex items-center space-x-2"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Go Back</span>
          </button>
        </div>
      </div>
    </div>
  )
}

export default NotFoundPage