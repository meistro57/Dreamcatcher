import { useState, useRef, useEffect } from 'react'
import { Mic, MicOff, Zap, Loader2 } from 'lucide-react'
import { useIdeaStore } from '../stores/ideaStore'
import { useAppStore } from '../stores/appStore'

const VoiceCaptureButton = () => {
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [audioLevel, setAudioLevel] = useState(0)
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const animationRef = useRef<number>()
  const timerRef = useRef<NodeJS.Timeout>()
  
  const { createIdea } = useIdeaStore()
  const { settings } = useAppStore()
  
  useEffect(() => {
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [])
  
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000
        }
      })
      
      streamRef.current = stream
      
      // Set up audio level monitoring
      const audioContext = new AudioContext()
      const analyser = audioContext.createAnalyser()
      const source = audioContext.createMediaStreamSource(stream)
      
      analyser.fftSize = 256
      source.connect(analyser)
      
      audioContextRef.current = audioContext
      analyserRef.current = analyser
      
      // Start audio level monitoring
      monitorAudioLevel()
      
      // Set up MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      const chunks: Blob[] = []
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data)
        }
      }
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' })
        await processAudio(audioBlob)
      }
      
      mediaRecorderRef.current = mediaRecorder
      mediaRecorder.start()
      
      setIsRecording(true)
      setRecordingTime(0)
      
      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1)
      }, 1000)
      
    } catch (error) {
      console.error('Failed to start recording:', error)
      alert('Failed to access microphone. Please check permissions.')
    }
  }
  
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
      setIsProcessing(true)
      
      // Clean up
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
      }
      
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
      
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
      
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
      
      setAudioLevel(0)
    }
  }
  
  const monitorAudioLevel = () => {
    if (!analyserRef.current) return
    
    const analyser = analyserRef.current
    const dataArray = new Uint8Array(analyser.frequencyBinCount)
    
    const updateLevel = () => {
      analyser.getByteFrequencyData(dataArray)
      
      // Calculate average level
      let sum = 0
      for (let i = 0; i < dataArray.length; i++) {
        sum += dataArray[i]
      }
      const average = sum / dataArray.length
      const normalizedLevel = Math.min(average / 128, 1)
      
      setAudioLevel(normalizedLevel)
      
      if (isRecording) {
        animationRef.current = requestAnimationFrame(updateLevel)
      }
    }
    
    updateLevel()
  }
  
  const processAudio = async (audioBlob: Blob) => {
    try {
      const audioFile = new File([audioBlob], 'recording.webm', {
        type: 'audio/webm'
      })
      
      const ideaId = await createIdea('', 'voice', {
        audioFile,
        urgency: settings.defaultUrgency
      })
      
      if (ideaId) {
        // Success feedback
        navigator.vibrate?.(100)
      }
      
    } catch (error) {
      console.error('Failed to process audio:', error)
    } finally {
      setIsProcessing(false)
      setRecordingTime(0)
    }
  }
  
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }
  
  const buttonSize = isRecording ? 'w-20 h-20' : 'w-16 h-16'
  const buttonScale = isRecording ? 'scale-110' : 'scale-100'
  
  return (
    <div className="fixed bottom-6 right-6 z-50">
      {/* Recording Timer */}
      {isRecording && (
        <div className="absolute -top-12 left-1/2 transform -translate-x-1/2 animate-slide-down">
          <div className="bg-red-600 text-white px-3 py-1 rounded-full text-sm font-mono">
            {formatTime(recordingTime)}
          </div>
        </div>
      )}
      
      {/* Audio Level Indicator */}
      {isRecording && (
        <div className="absolute -top-6 left-1/2 transform -translate-x-1/2 w-12 h-1 bg-dark-700 rounded-full overflow-hidden">
          <div 
            className="h-full bg-primary-500 transition-all duration-75"
            style={{ width: `${audioLevel * 100}%` }}
          />
        </div>
      )}
      
      {/* Main Button */}
      <button
        onClick={isRecording ? stopRecording : startRecording}
        disabled={isProcessing}
        className={`
          ${buttonSize} ${buttonScale}
          bg-gradient-to-r from-primary-600 to-primary-700
          hover:from-primary-700 hover:to-primary-800
          disabled:from-gray-600 disabled:to-gray-700
          text-white rounded-full
          shadow-2xl shadow-primary-600/30
          transition-all duration-300
          flex items-center justify-center
          touch-manipulation
          ${isRecording ? 'recording-pulse' : ''}
          ${isProcessing ? 'animate-pulse' : ''}
        `}
      >
        {isProcessing ? (
          <Loader2 className="w-8 h-8 animate-spin" />
        ) : isRecording ? (
          <MicOff className="w-8 h-8" />
        ) : (
          <Mic className="w-8 h-8" />
        )}
      </button>
      
      {/* Emergency Mode Button */}
      <button
        onClick={() => {
          // Emergency capture - skip processing, just record
          alert('Emergency capture mode activated!')
        }}
        className="absolute -top-2 -right-2 w-8 h-8 bg-yellow-600 hover:bg-yellow-700 text-white rounded-full shadow-lg flex items-center justify-center"
        title="Emergency Capture"
      >
        <Zap className="w-4 h-4" />
      </button>
      
      {/* Ripple Effect */}
      {isRecording && (
        <div className="absolute inset-0 animate-ping">
          <div className="w-full h-full bg-primary-600 rounded-full opacity-20"></div>
        </div>
      )}
    </div>
  )
}

export default VoiceCaptureButton