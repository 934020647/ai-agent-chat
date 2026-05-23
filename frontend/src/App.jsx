import { useState } from 'react'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

function App() {
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [response, setResponse] = useState(null)

  const handleSend = async () => {
    if (!message.trim()) return

    setLoading(true)
    setError(null)
    setResponse(null)

    try {
      const res = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message.trim() }),
      })

      if (!res.ok) {
        throw new Error(`Backend returned ${res.status}`)
      }

      const data = await res.json()
      setResponse(data)
    } catch (err) {
      setError(err.message || 'Failed to connect to backend')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSend()
    }
  }

  return (
    <>
      <header>
        <h1>AI Agent Chat Platform</h1>
        <p>A transparent task-oriented AI assistant</p>
      </header>

      <div className="input-area">
        <input
          type="text"
          placeholder="Type your message..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button onClick={handleSend} disabled={loading || !message.trim()}>
          Send
        </button>
      </div>

      {loading && <div className="loading">Thinking...</div>}
      {error && <div className="error">Error: {error}</div>}

      {response && (
        <>
          <div className="panel">
            <h3>Final Reply</h3>
            <p>{response.reply}</p>
          </div>

          <div className="panel">
            <h3>Intent</h3>
            <p>{response.intent}</p>
          </div>

          <div className="panel">
            <h3>Task Decomposition</h3>
            {response.tasks && response.tasks.length > 0 ? (
              <ul>
                {response.tasks.map((task, i) => (
                  <li key={i}>{task}</li>
                ))}
              </ul>
            ) : (
              <p className="empty">No tasks</p>
            )}
          </div>

          <div className="panel">
            <h3>Execution Steps</h3>
            {response.steps && response.steps.length > 0 ? (
              <ul>
                {response.steps.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ul>
            ) : (
              <p className="empty">No steps</p>
            )}
          </div>
        </>
      )}
    </>
  )
}

export default App
