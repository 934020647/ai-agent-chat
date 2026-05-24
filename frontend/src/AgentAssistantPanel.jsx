import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

function AgentAssistantPanel() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, loading])

  const sendMessage = async () => {
    const text = input.trim()
    if (!text || loading) return

    const userMsg = { role: 'user', content: text }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      })
      const data = await res.json()
      const reply = data.reply || '抱歉，暂时没有回复。'
      const assistantMsg = { role: 'assistant', content: reply }
      setMessages((prev) => [...prev, assistantMsg])
    } catch (err) {
      const errorMsg = {
        role: 'assistant',
        content: '请求失败，请稍后重试。',
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="agent-assistant-panel">
      <div className="agent-assistant-header">
        <span className="agent-assistant-title">Agent 助手</span>
        <span className="agent-assistant-subtitle">随时提问或反馈</span>
      </div>

      <div className="agent-assistant-messages" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="agent-assistant-empty">
            <p>👋 我是 Agent 助手</p>
            <p>你可以随时向我提问，或反馈面试体验。</p>
            <p>例如：</p>
            <ul>
              <li>"我觉得面试题里 RAG 的题目太多了"</li>
              <li>"能不能增加一些 Agent 相关的题目？"</li>
              <li>"这道题的追问不够深入"</li>
            </ul>
          </div>
        )}
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`agent-assistant-message ${msg.role}`}
          >
            <div className="agent-assistant-bubble">
              {msg.role === 'assistant' ? (
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              ) : (
                <div>{msg.content}</div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="agent-assistant-message assistant">
            <div className="agent-assistant-bubble">
              <div className="agent-assistant-typing">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="agent-assistant-input">
        <textarea
          placeholder="输入消息..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          disabled={loading}
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
        >
          发送
        </button>
      </div>
    </div>
  )
}

export default AgentAssistantPanel
