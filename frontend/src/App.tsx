import { useState } from 'react'
import LogUpload from './components/LogUpload'
import ChatInterface from './components/ChatInterface'
import './App.css'

type AppPhase = 'upload' | 'chat'

export interface UploadData {
  filename: string
  collectionName: string
}

function App() {
  const [phase, setPhase] = useState<AppPhase>('upload')
  const [uploadData, setUploadData] = useState<UploadData | null>(null)

  const handleUploadSuccess = (data: UploadData) => {
    setUploadData(data)
    setPhase('chat')
  }

  const handleReset = () => {
    setUploadData(null)
    setPhase('upload')
  }

  return (
    <div className="min-h-screen bg-linear-to-br from-slate-900 via-purple-900 to-slate-900">
      {phase === 'upload' ? (
        <LogUpload onUploadSuccess={handleUploadSuccess} />
      ) : (
        <ChatInterface 
          uploadData={uploadData!} 
          onReset={handleReset}
        />
      )}
    </div>
  )
}

export default App
