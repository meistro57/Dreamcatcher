import { ReactNode } from 'react'
import { useLocation } from 'react-router-dom'
import Navbar from './Navbar'
import VoiceCaptureButton from './VoiceCaptureButton'
import ConnectionStatus from './ConnectionStatus'

interface LayoutProps {
  children: ReactNode
}

const Layout = ({ children }: LayoutProps) => {
  const location = useLocation()
  
  return (
    <div className="min-h-screen bg-dark-900 text-dark-50">
      {/* Connection Status */}
      <ConnectionStatus />
      
      {/* Main Content */}
      <div className="flex flex-col min-h-screen">
        {/* Navigation */}
        <Navbar />
        
        {/* Page Content */}
        <main className="flex-1 safe-area-inset">
          {children}
        </main>
        
        {/* Floating Voice Capture Button */}
        <VoiceCaptureButton />
      </div>
    </div>
  )
}

export default Layout