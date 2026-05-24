import { useState, useRef } from 'react'
import ReactMarkdown from 'react-markdown'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const MODE_OPTIONS = [
  { value: 'graduate_reexam', label: '研究生复试/保研' },
  { value: 'industry_interview', label: '互联网大厂实习/校招' },
  { value: 'general_mock', label: '综合模拟面试' },
]

const FOCUS_OPTIONS = [
  { value: 'balanced', label: '综合均衡' },
  { value: 'fundamentals', label: '专业基础' },
  { value: 'project_experience', label: '项目经历' },
]

const GRADE_OPTIONS = ['大一', '大二', '大三', '大四', '研一', '研二']

function InterviewMode() {
  const [mode, setMode] = useState('general_mock')
  const [focus, setFocus] = useState('balanced')
  const [grade, setGrade] = useState('大三')
  const [role, setRole] = useState('')
  const [resumeFile, setResumeFile] = useState(null)
  const [resumeSessionId, setResumeSessionId] = useState(null)
  const [uploading, setUploading] = useState(false)

  const [sessionId, setSessionId] = useState(null)
  const [currentQuestion, setCurrentQuestion] = useState(null)
  const [answerText, setAnswerText] = useState('')
  const [interviewStatus, setInterviewStatus] = useState('idle') // idle, ready, in_progress, completed
  const [progress, setProgress] = useState({ current: 0, total: 0 })
  const [interviewerReply, setInterviewerReply] = useState('')
  const [evaluation, setEvaluation] = useState(null)
  const [history, setHistory] = useState([])
  const [summary, setSummary] = useState(null)
  const [closingMessage, setClosingMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fileInputRef = useRef(null)

  const handleUpload = async (file) => {
    if (!file) return
    setUploading(true)
    setError(null)
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await fetch(`${API_BASE_URL}/api/interview/upload-resume`, {
        method: 'POST',
        body: formData,
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      setResumeSessionId(data.resume_session_id)
      setResumeFile(file)
    } catch (err) {
      setError('简历上传失败: ' + err.message)
    } finally {
      setUploading(false)
    }
  }

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (file) handleUpload(file)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    const file = e.dataTransfer.files?.[0]
    if (file && file.type === 'application/pdf') {
      handleUpload(file)
    } else {
      setError('请上传 PDF 文件')
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
  }

  const startInterview = async () => {
    setLoading(true)
    setError(null)
    try {
      const payload = {
        interview_mode: mode,
        focus_mode: focus,
        role_or_major: role || undefined,
        grade: grade || undefined,
        resume_session_id: resumeSessionId || undefined,
        num_questions: 5,
      }
      const res = await fetch(`${API_BASE_URL}/api/interview/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)

      setSessionId(data.session_id)
      setCurrentQuestion(data.current_question)
      setProgress(data.progress)
      setInterviewStatus(data.status)
      setHistory([])
      setSummary(null)
      setInterviewerReply('')
      setEvaluation(null)
      setAnswerText('')
    } catch (err) {
      setError('开始面试失败: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const submitAnswer = async () => {
    if (!answerText.trim() || !sessionId) return
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE_URL}/api/interview/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, answer: answerText.trim() }),
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)

      // Record history
      setHistory((prev) => [
        ...prev,
        {
          question: currentQuestion,
          answer: answerText.trim(),
          evaluation: data.evaluation,
          interviewer_reply: data.interviewer_reply,
        },
      ])

      setInterviewerReply(data.interviewer_reply)
      setEvaluation(data.evaluation)
      setAnswerText('')

      if (data.status === 'completed') {
        setInterviewStatus('completed')
        setSummary(data.summary)
        setClosingMessage(data.closing_message || '')
        setCurrentQuestion(null)
        setProgress(data.progress)
      } else {
        setInterviewStatus('in_progress')
        setClosingMessage('')
        setCurrentQuestion(data.next_question)
        setProgress(data.progress)
      }
    } catch (err) {
      setError('提交回答失败: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const resetInterview = () => {
    setSessionId(null)
    setCurrentQuestion(null)
    setInterviewStatus('idle')
    setProgress({ current: 0, total: 0 })
    setInterviewerReply('')
    setEvaluation(null)
    setHistory([])
    setSummary(null)
    setClosingMessage('')
    setAnswerText('')
    setError(null)
  }

  const renderScore = (val) => {
    if (val === null || val === undefined) return 'N/A'
    let color = '#2e7d32'
    if (val < 70) color = '#f9a825'
    if (val < 60) color = '#d9534f'
    return <span style={{ color, fontWeight: 700 }}>{val}</span>
  }

  return (
    <div className="interview-mode">
      <header className="interview-header">
        <h1>OfferDrill</h1>
        <p>面经驱动 AI 模拟面试官</p>
      </header>

      {interviewStatus === 'idle' && (
        <div className="interview-config">
          <div className="config-grid">
            <div className="config-field">
              <label>面试类型</label>
              <select value={mode} onChange={(e) => setMode(e.target.value)}>
                {MODE_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="config-field">
              <label>考察侧重</label>
              <select value={focus} onChange={(e) => setFocus(e.target.value)}>
                {FOCUS_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="config-field">
              <label>年级</label>
              <select value={grade} onChange={(e) => setGrade(e.target.value)}>
                {GRADE_OPTIONS.map((g) => (
                  <option key={g} value={g}>
                    {g}
                  </option>
                ))}
              </select>
            </div>

            <div className="config-field">
              <label>目标岗位/专业（可选）</label>
              <input
                type="text"
                placeholder="如：后端开发实习、计算机保研..."
                value={role}
                onChange={(e) => setRole(e.target.value)}
              />
            </div>
          </div>

          <div
            className="resume-dropzone"
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              style={{ display: 'none' }}
              onChange={handleFileChange}
            />
            {resumeFile ? (
              <div className="resume-info">
                <span className="resume-filename">{resumeFile.name}</span>
                <span className="resume-status">已上传</span>
              </div>
            ) : (
              <div className="resume-placeholder">
                <div className="resume-icon">📄</div>
                <div>点击或拖拽上传简历 PDF</div>
                <div className="resume-hint">支持 PDF 格式，自动提取文本</div>
              </div>
            )}
          </div>

          {uploading && <div className="loading">正在解析简历...</div>}

          <button
            className="start-btn"
            onClick={startInterview}
            disabled={loading}
          >
            {loading ? '准备中...' : '开始面试'}
          </button>
        </div>
      )}

      {(interviewStatus === 'ready' || interviewStatus === 'in_progress') && (
        <div className="interview-session">
          <div className="interview-progress">
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{
                  width: `${(progress.current / Math.max(progress.total, 1)) * 100}%`,
                }}
              />
            </div>
            <div className="progress-text">
              第 {progress.current} / {progress.total} 题
            </div>
          </div>

          {interviewerReply && (
            <div className="panel interviewer-panel">
              <h3>面试官</h3>
              <ReactMarkdown>{interviewerReply}</ReactMarkdown>
            </div>
          )}

          {evaluation && (
            <div className="panel evaluation-panel">
              <h3>评分反馈</h3>
              <div className="evaluation-grid">
                <div className="evaluation-item">
                  <span className="evaluation-label">准确性</span>
                  {renderScore(evaluation.accuracy)}
                </div>
                <div className="evaluation-item">
                  <span className="evaluation-label">结构</span>
                  {renderScore(evaluation.structure)}
                </div>
                <div className="evaluation-item">
                  <span className="evaluation-label">深度</span>
                  {renderScore(evaluation.depth)}
                </div>
                <div className="evaluation-item">
                  <span className="evaluation-label">表达</span>
                  {renderScore(evaluation.communication)}
                </div>
              </div>
              {evaluation.overall_feedback && (
                <div className="evaluation-feedback">
                  {evaluation.overall_feedback}
                </div>
              )}
            </div>
          )}

          {currentQuestion && (
            <div className="panel question-panel">
              <div className="question-meta">
                <span className="question-tag">{currentQuestion.topic}</span>
                <span className="question-tag">{currentQuestion.focus_mode}</span>
              </div>
              <h3>{currentQuestion.question}</h3>
              {currentQuestion.answer_points && currentQuestion.answer_points.length > 0 && (
                <div className="answer-points">
                  <div className="answer-points-title">答题要点：</div>
                  <ul>
                    {currentQuestion.answer_points.map((pt, i) => (
                      <li key={i}>{pt}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          <div className="answer-area">
            <textarea
              placeholder="请输入你的回答..."
              value={answerText}
              onChange={(e) => setAnswerText(e.target.value)}
              rows={6}
              disabled={loading}
            />
            <button
              onClick={submitAnswer}
              disabled={loading || !answerText.trim()}
            >
              {loading ? '评分中...' : '提交回答'}
            </button>
          </div>
        </div>
      )}

      {interviewStatus === 'completed' && (
        <div className="interview-summary">
          <div className="interview-progress">
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: '100%' }}
              />
            </div>
            <div className="progress-text">面试已完成 {progress.total} / {progress.total} 题</div>
          </div>

          {interviewerReply && (
            <div className="panel interviewer-panel">
              <h3>面试官</h3>
              <ReactMarkdown>{interviewerReply}</ReactMarkdown>
            </div>
          )}

          {evaluation && (
            <div className="panel evaluation-panel">
              <h3>最后一题评分</h3>
              <div className="evaluation-grid">
                <div className="evaluation-item">
                  <span className="evaluation-label">准确性</span>
                  {renderScore(evaluation.accuracy)}
                </div>
                <div className="evaluation-item">
                  <span className="evaluation-label">结构</span>
                  {renderScore(evaluation.structure)}
                </div>
                <div className="evaluation-item">
                  <span className="evaluation-label">深度</span>
                  {renderScore(evaluation.depth)}
                </div>
                <div className="evaluation-item">
                  <span className="evaluation-label">表达</span>
                  {renderScore(evaluation.communication)}
                </div>
              </div>
              {evaluation.overall_feedback && (
                <div className="evaluation-feedback">
                  {evaluation.overall_feedback}
                </div>
              )}
            </div>
          )}

          {closingMessage && (
            <div className="panel closing-panel">
              <h3>反问环节</h3>
              <div className="closing-message">{closingMessage}</div>
            </div>
          )}

          <div className="panel summary-panel">
            <h3>面试总结</h3>
            {summary && (
              <>
                <div className="summary-scores">
                  {Object.entries(summary.overall_scores || {}).map(([key, val]) => {
                    const labelMap = {
                      accuracy: '准确性',
                      structure: '结构',
                      depth: '深度',
                      communication: '表达',
                    }
                    return (
                      <div className="summary-score-item" key={key}>
                        <span className="summary-score-label">{labelMap[key] || key}</span>
                        <span className="summary-score-value">{renderScore(val)}</span>
                      </div>
                    )
                  })}
                </div>
                <div className="summary-detail">
                  <ReactMarkdown>{summary.summary}</ReactMarkdown>
                </div>
              </>
            )}
          </div>

          {history.length > 0 && (
            <div className="panel history-panel">
              <h3>答题回顾</h3>
              <div className="history-list">
                {history.map((item, idx) => (
                  <div className="history-item" key={idx}>
                    <div className="history-question">
                      <span className="history-num">Q{idx + 1}</span>
                      {item.question?.question}
                    </div>
                    <div className="history-answer">
                      <strong>你的回答：</strong>
                      {item.answer}
                    </div>
                    {item.evaluation && (
                      <div className="history-eval">
                        准确性 {item.evaluation.accuracy ?? 'N/A'} | 结构{' '}
                        {item.evaluation.structure ?? 'N/A'} | 深度{' '}
                        {item.evaluation.depth ?? 'N/A'} | 表达{' '}
                        {item.evaluation.communication ?? 'N/A'}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          <button className="start-btn" onClick={resetInterview}>
            重新开始
          </button>
        </div>
      )}

      {error && <div className="error">{error}</div>}
    </div>
  )
}

export default InterviewMode
