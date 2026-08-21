import { useState, useEffect, useRef } from 'react'
import { usePorcupine } from '@picovoice/porcupine-react'
import SiriAnimation from './components/SiriAnimation'
import './App.css'

// `Window.ipcRenderer` is declared globally in electron/electron-env.d.ts

function App() {
  const [isListening, setIsListening] = useState(false)

  // Agent state lives in a ref, not state: it is only read inside effects, never
  // rendered. As state it would force a no-op re-render on every agent transition,
  // and the wake-word effect below would have to take it as a dependency — which
  // would re-fire the wake-word action the moment the agent started, immediately
  // stopping the agent it had just launched.
  const isAgentRunningRef = useRef(false)

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
  }, [init])

  // Start listening once loaded.
  // `error` is deliberately not read here — it is logged by its own effect below.
  // Depending on it would re-run this effect (and call start() again) every time
  // an error changes while already loaded.
  useEffect(() => {
    if (isLoaded) {
      console.log('Porcupine loaded successfully, starting listening...')
      start()
    } else {
      console.log('Porcupine not yet loaded.')
    }
  }, [isLoaded, start])

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
      console.log('Jarvis agent started')
      isAgentRunningRef.current = true
    }
    const onStopped = () => {
      console.log('Jarvis agent stopped')
      isAgentRunningRef.current = false
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
      if (isAgentRunningRef.current) {
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
  }, [release])

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