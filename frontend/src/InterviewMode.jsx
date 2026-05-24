import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import UserProfilePanel from './UserProfilePanel'
import ResumeReviewPanel from './ResumeReviewPanel'
import InterviewConfigPanel from './InterviewConfigPanel'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

function InterviewMode() {
  // Tabs: profile | review | interview
  const [activeTab, setActiveTab] = useState('profile')

  // Profile state
  const [profile, setProfile] = useState(null)
  const [profileId, setProfileId] = useState(null)

  // Resume state
  const [resumeSessionId, setResumeSessionId] = useState(null)

  // Review state
  const [review, setReview] = useState(null)
  const [reviewLoading, setReviewLoading] = useState(false)
  const [reviewProgress, setReviewProgress] = useState({ percent: 0, stage: '' })

  // Interview config state
  const [mode, setMode] = useState('general_mock')
  const [focus, setFocus] = useState('balanced')
  const [target, setTarget] = useState('')

  // Interview session state
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
  const [answerProgress, setAnswerProgress] = useState({ percent: 0, stage: '' })
  const [isStarting, setIsStarting] = useState(false)
  const [startError, setStartError] = useState('')
  const [startSuccess, setStartSuccess] = useState('')
  const [error, setError] = useState(null)

  // Load profile from localStorage on mount
  useEffect(() => {
    try {
      const savedId = localStorage.getItem('offerdrill_profile_id')
      const savedData = localStorage.getItem('offerdrill_profile_data')
      if (savedId && savedData) {
        const parsed = JSON.parse(savedData)
        setProfileId(savedId)
        setProfile(parsed)
        setMode(parsed.preferred_interview_mode || 'general_mock')
        setFocus(parsed.preferred_focus_mode || 'balanced')
        setTarget(parsed.target || '')
        if (parsed.resume_id) setResumeSessionId(parsed.resume_id)
      }
    } catch {
      // ignore parse errors
    }
  }, [])

  const handleProfileSave = (newProfileId, newProfile) => {
    setProfileId(newProfileId)
    setProfile(newProfile)
    localStorage.setItem('offerdrill_profile_id', newProfileId)
    localStorage.setItem('offerdrill_profile_data', JSON.stringify(newProfile))
    setMode(newProfile.preferred_interview_mode || 'general_mock')
    setFocus(newProfile.preferred_focus_mode || 'balanced')
    setTarget(newProfile.target || '')
    if (newProfile.resume_id) setResumeSessionId(newProfile.resume_id)
    setError(null)
  }

  const handleResumeUpload = (resumeId, preview) => {
    setResumeSessionId(resumeId)
    // Sync resume_id into profile state and localStorage
    setProfile((prev) => {
      if (!prev) {
        const minimal = { resume_id: resumeId, resume_preview: preview }
        localStorage.setItem('offerdrill_profile_data', JSON.stringify(minimal))
        return minimal
      }
      const updated = { ...prev, resume_id: resumeId, resume_preview: preview }
      localStorage.setItem('offerdrill_profile_data', JSON.stringify(updated))
      return updated
    })
  }

  const resolveResumeId = () => {
    // Priority: explicit state > profile > localStorage
    if (resumeSessionId) return resumeSessionId
    if (profile?.resume_id) return profile.resume_id
    try {
      const saved = localStorage.getItem('offerdrill_profile_data')
      if (saved) {
        const parsed = JSON.parse(saved)
        if (parsed.resume_id) return parsed.resume_id
      }
    } catch { /* ignore */ }
    return null
  }

  const handleRequestReview = async () => {
    const rid = resolveResumeId()
    if (!rid) {
      setError('请先在个人资料页上传 PDF 简历，或确认简历已成功绑定到个人资料。')
      return
    }
    setReviewLoading(true)
    setReviewProgress({ percent: 5, stage: '正在读取简历内容...' })
    setError(null)

    const stages = [
      { percent: 15, stage: '正在分析项目经历和技能栈...' },
      { percent: 40, stage: '正在生成可能追问...' },
      { percent: 65, stage: '正在整理修改建议...' },
      { percent: 85, stage: '即将完成...' },
    ]
    let stageIdx = 0
    const progressTimer = setInterval(() => {
      if (stageIdx < stages.length) {
        setReviewProgress(stages[stageIdx])
        stageIdx += 1
      }
    }, 1200)

    try {
      const res = await fetch(`${API_BASE_URL}/api/resume/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resume_id: rid,
          profile_id: profileId || undefined,
        }),
      })
      const data = await res.json()
      if (data.error) {
        if (data.error === 'Resume not found' || data.error.includes('not found')) {
          throw new Error('后端未找到该简历，可能是服务重启导致内存中的简历丢失。请重新上传简历后再生成测评。')
        }
        throw new Error(data.error)
      }
      setReviewProgress({ percent: 100, stage: '测评完成' })
      setReview(data)
    } catch (err) {
      setError('简历测评失败: ' + err.message)
    } finally {
      clearInterval(progressTimer)
      setReviewLoading(false)
    }
  }

  const startInterview = async () => {
    setIsStarting(true)
    setStartError('')
    setStartSuccess('')
    setError(null)
    try {
      const resolvedTarget = (target || profile?.target || '').trim()
      if (!resolvedTarget) {
        setStartError('请填写本轮目标岗位或目标院校专业方向。')
        setIsStarting(false)
        return
      }

      const payload = {
        interview_mode: mode,
        focus_mode: focus,
        target: resolvedTarget,
        role_or_major: resolvedTarget,
        grade: profile?.grade || undefined,
        major: profile?.major || undefined,
        resume_session_id: resumeSessionId || undefined,
        resume_id: resumeSessionId || undefined,
        num_questions: 5,
        job_type: 'developer',
      }
      if (profileId) {
        payload.profile_id = profileId
      }

      const res = await fetch(`${API_BASE_URL}/api/interview/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await res.json()

      if (data.error) {
        throw new Error(data.error)
      }

      const total = data.total_questions ?? data.progress?.total ?? 0
      const current = data.progress?.current ?? 1
      const question = data.current_question || null

      if (!question || total === 0) {
        throw new Error(
          '当前面试配置在题库中没有匹配题目，请尝试切换为“互联网大厂实习/校招”模式，或填写更明确的目标岗位。'
        )
      }

      setSessionId(data.session_id)
      setCurrentQuestion(question)
      setProgress({ current, total })
      setInterviewStatus(data.status || 'ready')
      setHistory([])
      setSummary(null)
      setInterviewerReply('')
      setEvaluation(null)
      setAnswerText('')

      let successMsg = '已基于个人资料和面经题库生成本轮面试。'
      if (data.warnings && data.warnings.length > 0) {
        successMsg += ' 提示：' + data.warnings.join(' ')
      }
      setStartSuccess(successMsg)
    } catch (err) {
      console.error('[startInterview] error:', err)
      let msg = err.message || '未知错误'
      if (msg.includes('Missing target')) {
        msg = '请填写本轮目标岗位或目标院校专业方向。'
      } else if (msg.includes('Profile expired')) {
        msg = '个人资料已失效，已尝试使用当前表单信息开始面试。'
      } else if (msg.includes('Resume not found')) {
        msg = '简历已失效，本轮将不参考简历内容。'
      }
      setStartError('启动面试失败：' + msg)
    } finally {
      setIsStarting(false)
    }
  }

  const submitAnswer = async () => {
    if (!answerText.trim() || !sessionId) return
    setLoading(true)
    setError(null)

    const stages = [
      { percent: 10, stage: '正在分析你的回答...' },
      { percent: 35, stage: '正在对照评分标准...' },
      { percent: 60, stage: '正在生成点评和标准回答...' },
      { percent: 80, stage: '正在准备下一道追问...' },
      { percent: 92, stage: '即将完成...' },
    ]
    let stageIdx = 0
    setAnswerProgress({ percent: 5, stage: '正在提交回答...' })
    const progressTimer = setInterval(() => {
      if (stageIdx < stages.length) {
        setAnswerProgress(stages[stageIdx])
        stageIdx += 1
      }
    }, 1200)

    try {
      const res = await fetch(`${API_BASE_URL}/api/interview/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, answer: answerText.trim() }),
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)

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
      clearInterval(progressTimer)
      setLoading(false)
      setAnswerProgress({ percent: 0, stage: '' })
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
    setStartError('')
    setStartSuccess('')
  }

  const renderScore = (val) => {
    if (val === null || val === undefined) return 'N/A'
    let color = '#2e7d32'
    if (val < 70) color = '#f9a825'
    if (val < 60) color = '#d9534f'
    return <span style={{ color, fontWeight: 700 }}>{val}</span>
  }

  const showInterviewActive = interviewStatus === 'ready' || interviewStatus === 'in_progress'
  const showInterviewCompleted = interviewStatus === 'completed'
  const showQuestionPanel = !!currentQuestion && !showInterviewCompleted

  return (
    <div className="interview-mode">
      <header className="interview-header">
        <h1>OfferDrill</h1>
        <p>面经驱动 AI 模拟面试官</p>
      </header>

      <div className="interview-tabs">
        <button
          className={activeTab === 'profile' ? 'interview-tab active' : 'interview-tab'}
          onClick={() => setActiveTab('profile')}
        >
          个人资料
        </button>
        <button
          className={activeTab === 'review' ? 'interview-tab active' : 'interview-tab'}
          onClick={() => setActiveTab('review')}
        >
          简历测评
        </button>
        <button
          className={activeTab === 'interview' ? 'interview-tab active' : 'interview-tab'}
          onClick={() => setActiveTab('interview')}
        >
          模拟面试
        </button>
      </div>

      {activeTab === 'profile' && (
        <UserProfilePanel
          profile={profile}
          onSave={handleProfileSave}
          resumeSessionId={resumeSessionId}
          onResumeUpload={handleResumeUpload}
        />
      )}

      {activeTab === 'review' && (
        <ResumeReviewPanel
          review={review}
          loading={reviewLoading}
          progress={reviewProgress}
          onRequestReview={handleRequestReview}
          canReview={!!resolveResumeId()}
          resumeId={resolveResumeId()}
          profileId={profileId}
        />
      )}

      {activeTab === 'interview' && !showQuestionPanel && !showInterviewCompleted && (
        <InterviewConfigPanel
          profile={profile}
          mode={mode}
          focus={focus}
          target={target}
          onModeChange={setMode}
          onFocusChange={setFocus}
          onTargetChange={setTarget}
          onStartInterview={startInterview}
          isStarting={isStarting}
        />
      )}

      {activeTab === 'interview' && isStarting && (
        <div className="loading">正在基于个人资料和面经题库生成面试题...</div>
      )}

      {activeTab === 'interview' && startError && (
        <div className="error">{startError}</div>
      )}

      {activeTab === 'interview' && startSuccess && !showQuestionPanel && !showInterviewCompleted && (
        <div className="success">{startSuccess}</div>
      )}

      {activeTab === 'interview' && showQuestionPanel && (
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
              {progress.total > 0
                ? `第 ${progress.current} / ${progress.total} 题`
                : '面试题加载中...'}
            </div>
          </div>

          {startSuccess && (
            <div className="success">{startSuccess}</div>
          )}

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

          {loading && answerProgress.percent > 0 && (
            <div className="progress-feedback">
              <div className="progress-stage">{answerProgress.stage}</div>
              <div className="progress-bar-container">
                <div
                  className="progress-fill-animated"
                  style={{ width: `${answerProgress.percent}%` }}
                />
              </div>
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
              type="button"
              onClick={submitAnswer}
              disabled={loading || !answerText.trim()}
            >
              {loading ? '评分中...' : '提交回答'}
            </button>
          </div>
        </div>
      )}

      {activeTab === 'interview' && showInterviewCompleted && (
        <div className="interview-summary">
          <div className="interview-progress">
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: '100%' }} />
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
                <div className="evaluation-feedback">{evaluation.overall_feedback}</div>
              )}
            </div>
          )}

          {closingMessage && (
            <div className="panel closing-panel">
              <h3>面试结束</h3>
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
