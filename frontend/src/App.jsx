import { useState } from 'react'
import { flushSync } from 'react-dom'
import ReactMarkdown from 'react-markdown'
import './App.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const TEMP_RESPONSE = {
  reply: 'The agent is analyzing your request...',
  intent: 'Analyzing...',
  tasks: [
    'Understanding the user request',
    'Identifying the task type',
    'Preparing a task plan',
  ],
  steps: [
    'Received the user message',
    'Recognizing user intent',
    'Decomposing the task',
    'Calling Kimi API to generate the reply',
  ],
  retrieved_context: [],
  mode: 'thinking',
}

const ERROR_RESPONSE = {
  reply: 'Something went wrong while processing your request. Please try again.',
  intent: 'unknown',
  tasks: ['Attempt to understand the failed request', 'Provide guidance to retry'],
  steps: [
    'Received the user message',
    'Tried to call backend API',
    'Backend request failed',
  ],
  retrieved_context: [],
  mode: 'error',
}

function App() {
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [response, setResponse] = useState(null)
  const [isStreamingReply, setIsStreamingReply] = useState(false)

  const handleSend = async () => {
    if (!message.trim()) return

    setLoading(true)
    setError(null)
    setIsStreamingReply(false)
    setResponse({ ...TEMP_RESPONSE })

    const tryStream = async () => {
      const res = await fetch(`${API_BASE_URL}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message.trim() }),
      })

      if (!res.ok || !res.body) {
        throw new Error('Stream not available')
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // SSE events are separated by double newlines
        const parts = buffer.split('\n\n')
        buffer = parts.pop() // keep incomplete tail

        for (const part of parts) {
          const lines = part.split('\n')
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const jsonStr = line.slice(6)
              try {
                const event = JSON.parse(jsonStr)
                switch (event.type) {
                  case 'status':
                    flushSync(() => {
                      setResponse((prev) => ({
                        ...prev,
                        steps: event.steps,
                        mode: event.mode,
                      }))
                    })
                    break
                  case 'intent':
                    flushSync(() => {
                      setResponse((prev) => ({
                        ...prev,
                        intent: event.intent,
                        steps: event.steps,
                        mode: event.mode,
                      }))
                    })
                    break
                  case 'tasks':
                    flushSync(() => {
                      setResponse((prev) => ({
                        ...prev,
                        tasks: event.tasks,
                        steps: event.steps,
                        mode: event.mode,
                      }))
                    })
                    break
                  case 'retrieved_context':
                    flushSync(() => {
                      setResponse((prev) => ({
                        ...prev,
                        retrieved_context: event.retrieved_context,
                        mode: event.mode,
                      }))
                    })
                    break
                  case 'react_trace':
                    flushSync(() => {
                      setResponse((prev) => ({
                        ...prev,
                        react_trace: event.react_trace,
                        mode: event.mode,
                      }))
                    })
                    break
                  case 'delta':
                    flushSync(() => {
                      setResponse((prev) => {
                        const isFirstDelta = prev.reply === TEMP_RESPONSE.reply
                        return {
                          ...prev,
                          reply: isFirstDelta
                            ? (event.delta || '')
                            : (prev.reply || '') + (event.delta || ''),
                          mode: event.mode || prev.mode,
                        }
                      })
                      setIsStreamingReply(true)
                    })
                    break
                  case 'final':
                    flushSync(() => {
                      setResponse((prev) => ({
                        ...prev,
                        reply: event.reply,
                        intent: event.intent,
                        tasks: event.tasks,
                        steps: event.steps,
                        retrieved_context: event.retrieved_context,
                        mode: event.mode,
                        react_trace: event.react_trace || prev.react_trace,
                      }))
                      setIsStreamingReply(false)
                    })
                    break
                  case 'done':
                    // stream complete
                    break
                  default:
                    break
                }
              } catch {
                // ignore malformed JSON lines
              }
            }
          }
        }
      }
    }

    const tryFallback = async () => {
      const res = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message.trim() }),
      })

      if (!res.ok) {
        throw new Error(`Backend returned ${res.status}`)
      }

      const data = await res.json()
      flushSync(() => {
        setResponse((prev) => ({
          ...prev,
          ...data,
        }))
        setIsStreamingReply(false)
      })
    }

    try {
      await tryStream()
    } catch (streamErr) {
      try {
        await tryFallback()
      } catch (fallbackErr) {
        setError(fallbackErr.message || 'Failed to connect to backend')
        setResponse({ ...ERROR_RESPONSE })
      }
    } finally {
      setLoading(false)
      setIsStreamingReply(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSend()
    }
  }

  const displayResponse = response || {}
  const showPlainText = loading && isStreamingReply

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
          {loading ? 'Thinking...' : 'Send'}
        </button>
      </div>

      {loading && (
        <div className="loading">
          The agent is analyzing your request...
        </div>
      )}
      {error && (
        <div className="error">
          Error: {error}
        </div>
      )}

      {response && (
        <>
          <div className="panel reply-panel">
            <h3>Final Reply</h3>
            <div className={`markdown-body ${loading ? 'dimmed' : ''}`}>
              {showPlainText ? (
                <div className="streaming-text">
                  {displayResponse.reply}
                  <span className="cursor">▌</span>
                </div>
              ) : (
                <ReactMarkdown>{displayResponse.reply || ''}</ReactMarkdown>
              )}
            </div>
          </div>

          <div className="panel">
            <h3>Intent</h3>
            <p className={loading ? 'dimmed' : ''}>{displayResponse.intent}</p>
          </div>

          <div className="panel">
            <h3>Task Decomposition</h3>
            {displayResponse.tasks && displayResponse.tasks.length > 0 ? (
              <ul className={loading ? 'dimmed' : ''}>
                {displayResponse.tasks.map((task, i) => (
                  <li key={i}>{task}</li>
                ))}
              </ul>
            ) : (
              <p className="empty">No tasks</p>
            )}
          </div>

          <div className="panel">
            <h3>Execution Steps</h3>
            {displayResponse.steps && displayResponse.steps.length > 0 ? (
              <ul className={loading ? 'dimmed' : ''}>
                {displayResponse.steps.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ul>
            ) : (
              <p className="empty">No steps</p>
            )}
          </div>

          <div className="panel">
            <h3>Mode</h3>
            <p className={loading ? 'dimmed' : ''}>
              {displayResponse.mode === 'error_fallback' ? 'error' : displayResponse.mode}
            </p>
          </div>

          {/* Retrieved Context Panel */}
          {displayResponse.retrieved_context && displayResponse.retrieved_context.length > 0 ? (
            <div className="panel retrieved-context-panel">
              <h3>Retrieved Context</h3>
              <div className="retrieved-context-list">
                {displayResponse.retrieved_context.map((item, i) => (
                  <div key={i} className="retrieved-context-item">
                    <div className="retrieved-context-header">
                      <span className="retrieved-context-title">{item.title}</span>
                      <span className="retrieved-context-score">score: {item.score}</span>
                    </div>
                    <div className="retrieved-context-body">
                      {item.content.length > 300
                        ? item.content.slice(0, 300) + '...'
                        : item.content}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            !loading && (
              <div className="panel retrieved-context-panel">
                <h3>Retrieved Context</h3>
                <p className="empty">No retrieved context for this query.</p>
              </div>
            )
          )}

          {displayResponse.react_trace && displayResponse.react_trace.length > 0 && (
            <div className="panel react-trace-panel">
              <h3>ReAct Trace</h3>
              <div className="react-trace-list">
                {displayResponse.react_trace.map((item, i) => (
                  <div key={i} className="react-trace-item">
                    <div className="react-trace-action">
                      <span className="react-trace-label">Action:</span>{' '}
                      {item.action}
                    </div>
                    <div className="react-trace-observation">
                      <span className="react-trace-label">Observation:</span>{' '}
                      {item.observation}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </>
  )
}

export default App
