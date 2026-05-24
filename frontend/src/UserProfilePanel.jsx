import { useState, useRef, useEffect } from 'react'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

const GRADE_OPTIONS = ['大一', '大二', '大三', '大四', '研一', '研二', '研三', '博一', '博二', '博三', '博四', '博五']

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

function UserProfilePanel({ profile, onProfileChange, onSave, resumeSessionId, onResumeUpload }) {
  const [localProfile, setLocalProfile] = useState({
    grade: profile?.grade || '大三',
    major: profile?.major || '',
    school_or_background: profile?.school_or_background || '',
    target: profile?.target || '',
    target_school_or_major: profile?.target_school_or_major || '',
    preferred_interview_mode: profile?.preferred_interview_mode || 'general_mock',
    preferred_focus_mode: profile?.preferred_focus_mode || 'balanced',
    resume_id: profile?.resume_id || resumeSessionId || '',
    resume_preview: profile?.resume_preview || '',
  })
  const [uploading, setUploading] = useState(false)
  const [saveStatus, setSaveStatus] = useState('idle') // idle | saving | success | error
  const [saveMessage, setSaveMessage] = useState(null)
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  useEffect(() => {
    setLocalProfile((prev) => ({
      ...prev,
      resume_id: profile?.resume_id || resumeSessionId || prev.resume_id,
    }))
  }, [profile, resumeSessionId])

  const handleChange = (field, value) => {
    setLocalProfile((prev) => ({ ...prev, [field]: value }))
  }

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
      if (data.status === 'warning' && data.warning) {
        setError(data.warning)
      }
      const rid = data.resume_id || data.resume_session_id
      setLocalProfile((prev) => {
        const updated = {
          ...prev,
          resume_id: rid,
          resume_preview: data.extracted_text_preview || '',
        }
        onProfileChange?.(updated)
        return updated
      })
      onResumeUpload?.(rid, data.extracted_text_preview || '')
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

  const handleSave = async () => {
    setError(null)
    setSaveStatus('saving')
    setSaveMessage(null)
    try {
      const payload = {
        ...localProfile,
        profile_id: profile?.profile_id || undefined,
      }
      const res = await fetch(`${API_BASE_URL}/api/profile/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await res.json()
      if (data.error) throw new Error(data.error)
      onSave?.(data.profile_id, data.profile)
      setSaveStatus('success')
      setSaveMessage('个人资料已保存，后续模拟面试将自动参考这些信息。')
    } catch (err) {
      setSaveStatus('error')
      setError('保存失败，请检查后端服务或稍后重试。')
    }
  }

  return (
    <div className="profile-panel">
      <h3>个人资料</h3>

      <div className="config-grid">
        <div className="config-field">
          <label>年级</label>
          <select value={localProfile.grade} onChange={(e) => handleChange('grade', e.target.value)}>
            {GRADE_OPTIONS.map((g) => (
              <option key={g} value={g}>{g}</option>
            ))}
          </select>
        </div>

        <div className="config-field">
          <label>专业</label>
          <input
            type="text"
            placeholder="如：计算机科学与技术"
            value={localProfile.major}
            onChange={(e) => handleChange('major', e.target.value)}
          />
        </div>

        <div className="config-field">
          <label>学校/背景（可选）</label>
          <input
            type="text"
            placeholder="如：普通本科，有后端项目经历"
            value={localProfile.school_or_background}
            onChange={(e) => handleChange('school_or_background', e.target.value)}
          />
        </div>

        <div className="config-field">
          <label>默认目标岗位/方向</label>
          <input
            type="text"
            placeholder="如：后端开发实习、人工智能保研..."
            value={localProfile.target}
            onChange={(e) => handleChange('target', e.target.value)}
          />
        </div>

        <div className="config-field">
          <label>目标院校/专业方向（可选）</label>
          <input
            type="text"
            placeholder="如：清华大学计算机系"
            value={localProfile.target_school_or_major}
            onChange={(e) => handleChange('target_school_or_major', e.target.value)}
          />
        </div>

        <div className="config-field">
          <label>默认面试模式</label>
          <select
            value={localProfile.preferred_interview_mode}
            onChange={(e) => handleChange('preferred_interview_mode', e.target.value)}
          >
            {MODE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>

        <div className="config-field">
          <label>默认考察侧重</label>
          <select
            value={localProfile.preferred_focus_mode}
            onChange={(e) => handleChange('preferred_focus_mode', e.target.value)}
          >
            {FOCUS_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
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
        {localProfile.resume_id ? (
          <div className="resume-info">
            <span className="resume-filename">简历已上传</span>
            <span className="resume-status">{localProfile.resume_preview ? '可提取文本' : '无文本'}</span>
          </div>
        ) : (
          <div className="resume-placeholder">
            <div className="resume-icon">📄</div>
            <div>点击或拖拽上传简历 PDF</div>
            <div className="resume-hint">支持 PDF 格式，自动提取文本</div>
          </div>
        )}
      </div>

      {localProfile.resume_preview && (
        <div className="panel resume-preview-panel">
          <h4>简历文本预览</h4>
          <div className="resume-preview-text">{localProfile.resume_preview}...</div>
        </div>
      )}

      {localProfile.resume_id && (
        <div className="profile-id-hint">
          已绑定简历：{localProfile.resume_id.slice(0, 8)}...
        </div>
      )}

      {uploading && <div className="loading">正在解析简历...</div>}
      {error && <div className="error">{error}</div>}
      {saveStatus === 'success' && saveMessage && (
        <div className="success">{saveMessage}</div>
      )}
      {saveStatus === 'success' && (
        <div className="profile-id-hint">
          当前资料 ID：{(profile?.profile_id || localProfile.profile_id || '').slice(0, 12)}
          {!localProfile.resume_id && (
            <span className="resume-warning"> ｜ 当前资料未绑定简历，可继续使用无简历面试。</span>
          )}
        </div>
      )}

      <button
        className="start-btn"
        onClick={handleSave}
        disabled={saveStatus === 'saving'}
      >
        {saveStatus === 'saving' ? '保存中...' : saveStatus === 'success' ? '已保存' : '保存个人资料'}
      </button>
    </div>
  )
}

export default UserProfilePanel
