import { useState } from 'react'
import Form from './components/Form'
import Results from './components/Results'

function App() {
  const [sessionId, setSessionId] = useState(null)
  const [jobId, setJobId] = useState(null)
  const [status, setStatus] = useState('form')

  return (
    <div className="app">
      <header>
        <h1>🚀 BizEval</h1>
        <p>AI-анализ бизнес-идей</p>
      </header>
      <main>
        {status === 'form' && (
          <Form onSubmit={(sid, jid) => {
            setSessionId(sid)
            setJobId(jid)
            setStatus('results')
          }} />
        )}
        {status === 'results' && (
          <Results jobId={jobId} onBack={() => setStatus('form')} />
        )}
      </main>
    </div>
  )
}

export default App
