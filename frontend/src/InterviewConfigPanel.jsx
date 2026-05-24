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

function InterviewConfigPanel({ profile, mode, focus, target, onModeChange, onFocusChange, onTargetChange, onStartInterview, isStarting }) {
  const handleClick = (e) => {
    e.preventDefault()
    if (!onStartInterview) {
      console.warn('[InterviewConfigPanel] onStartInterview is not provided')
      return
    }
    onStartInterview()
  }

  return (
    <div className="interview-config-panel">
      <h3>开始模拟面试</h3>

      {profile && (
        <div className="panel profile-ref-panel">
          <h4>已关联个人资料</h4>
          <div className="profile-ref-grid">
            {profile.grade && <div><span className="profile-ref-label">年级:</span> {profile.grade}</div>}
            {profile.major && <div><span className="profile-ref-label">专业:</span> {profile.major}</div>}
            {profile.target && <div><span className="profile-ref-label">默认目标:</span> {profile.target}</div>}
            {profile.preferred_interview_mode && (
              <div>
                <span className="profile-ref-label">默认模式:</span>
                {MODE_OPTIONS.find((o) => o.value === profile.preferred_interview_mode)?.label || profile.preferred_interview_mode}
              </div>
            )}
          </div>
          <div className="profile-ref-hint">以下配置可覆盖资料默认值，仅影响本轮面试</div>
        </div>
      )}

      <div className="config-grid">
        <div className="config-field">
          <label>本轮面试模式</label>
          <select value={mode} onChange={(e) => onModeChange(e.target.value)}>
            {MODE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>

        <div className="config-field">
          <label>本轮考察侧重</label>
          <select value={focus} onChange={(e) => onFocusChange(e.target.value)}>
            {FOCUS_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>

        <div className="config-field" style={{ gridColumn: '1 / -1' }}>
          <label>本轮目标岗位/院校专业（可选覆盖）</label>
          <input
            type="text"
            placeholder="如：后端开发实习、清华人工智能保研..."
            value={target}
            onChange={(e) => onTargetChange(e.target.value)}
          />
        </div>
      </div>

      <button type="button" className="start-btn" onClick={handleClick} disabled={isStarting}>
        {isStarting ? '正在生成面试题...' : '开始模拟面试'}
      </button>
    </div>
  )
}

export default InterviewConfigPanel
