import { useState, useEffect } from 'react'
import { usePorcupine } from '@picovoice/porcupine-react'
import SiriAnimation from './components/SiriAnimation'
import './App.css'

// Extend Window interface to include ipcRenderer
declare global {
  interface Window {
    ipcRenderer: {
      on: (...args: any[]) => void
      off: (...args: any[]) => void
      send: (...args: any[]) => void
      invoke: (...args: any[]) => Promise<any>
      startRecording: () => Promise<{ success: boolean; text?: string; error?: string }>
      stopAgent: () => Promise<{ success: boolean; error?: string }>
    }
  }
}

function App() {
  const [isListening, setIsListening] = useState(false)
  const [isAgentRunning, setIsAgentRunning] = useState(false)

  const {
    keywordDetection,
    isLoaded,
    error,
    init,
    start,
    release,
  } = usePorcupine()

  // Initialize Porcupine
  useEffect(() => {
    const porcupineKeyword = {
      publicPath: '/Jarvis_en_wasm_v4_0_0/Jarvis_en_wasm_v4_0_0.ppn',
      label: 'jarvis',
    }

    const porcupineModel = {
      publicPath: '/porcupine_params.pv',
    }

    init(
      import.meta.env.VITE_PICOVOICE_ACCESS_KEY,
      porcupineKeyword,
      porcupineModel
    )
  }, [])

  // Start listening once loaded
  useEffect(() => {
    if (isLoaded) {
      console.log('Porcupine loaded successfully, starting listening...')
      start()
    } else {
      console.log('Porcupine not yet loaded. Error:', error)
    }
  }, [isLoaded])

  // Stop glow when recording ends (user finished speaking)
  useEffect(() => {
    const handler = () => {
      console.log('Recording stopped, ending glow')
      setIsListening(false)
    }
    window.ipcRenderer.on('recording-stopped', handler)
    return () => {
      window.ipcRenderer.off('recording-stopped', handler)
    }
  }, [])

  // Track agent lifecycle
  useEffect(() => {
    const onStarted = () => {
      console.log('Agent S3 started')
      setIsAgentRunning(true)
    }
    const onStopped = () => {
      console.log('Agent S3 stopped')
      setIsAgentRunning(false)
    }
    window.ipcRenderer.on('agent-started', onStarted)
    window.ipcRenderer.on('agent-stopped', onStopped)
    return () => {
      window.ipcRenderer.off('agent-started', onStarted)
      window.ipcRenderer.off('agent-stopped', onStopped)
    }
  }, [])

  // Handle wake word detection
  useEffect(() => {
    if (keywordDetection !== null) {
      console.log('Porcupine detected:', keywordDetection.label)
      if (isAgentRunning) {
        handleStopAgent()
      } else {
        handleWakeWordDetected()
      }
    }
  }, [keywordDetection])

  // Stop the running agent
  const handleStopAgent = async () => {
    console.log('Stopping agent...')
    await window.ipcRenderer.stopAgent()
  }

  // Handle recording and transcription when wake word is detected
  const handleWakeWordDetected = async () => {
    setIsListening(true)

    try {
      console.log('Starting recording...')
      const result = await window.ipcRenderer.startRecording()

      if (result.success) {
        console.log('Transcription result:', result.text)
      } else {
        console.error('Recording/Transcription failed:', result.error)
      }
    } catch (error) {
      console.error('Error during recording:', error)
    }
    // Glow is already stopped by 'recording-stopped' IPC event
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      release()
    }
  }, [])

  // Handle errors
  useEffect(() => {
    if (error) {
      console.error('Porcupine error:', error)
    }
  }, [error])

  return (
    <div className={`draggable-icon ${isListening ? 'listening' : ''}`}>
      {error && <div className="error">Error: {error.message}</div>}
      <SiriAnimation isListening={isListening} />
    </div>
  )
}

export default App