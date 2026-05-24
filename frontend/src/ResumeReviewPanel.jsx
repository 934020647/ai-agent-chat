import ReactMarkdown from 'react-markdown'

function ResumeReviewPanel({ review, loading, progress, onRequestReview, canReview, resumeId, profileId }) {
  if (loading) {
    return (
      <div className="review-panel">
        <h3>简历测评</h3>
        {progress && progress.percent > 0 && (
          <div className="progress-feedback">
            <div className="progress-stage">{progress.stage}</div>
            <div className="progress-bar-container">
              <div
                className="progress-fill-animated"
                style={{ width: `${progress.percent}%` }}
              />
            </div>
          </div>
        )}
        {!progress || progress.percent === 0 && (
          <div className="loading">正在生成简历测评，请稍候...</div>
        )}
      </div>
    )
  }

  if (!review) {
    return (
      <div className="review-panel">
        <h3>简历测评</h3>
        <p className="empty">上传简历并点击生成，即可获得 AI 简历测评报告。</p>

        {resumeId && (
          <div className="profile-id-hint">
            已绑定简历：{resumeId.slice(0, 8)}...
            {profileId && <span> ｜ 资料 ID：{profileId.slice(0, 8)}...</span>}
          </div>
        )}

        <button className="start-btn" onClick={onRequestReview} disabled={!canReview}>
          生成简历测评
        </button>
        {!canReview && (
          <div className="error">
            请先在个人资料页上传 PDF 简历，或确认简历已成功绑定到个人资料。
          </div>
        )}
      </div>
    )
  }

  const renderScore = (val) => {
    if (val === null || val === undefined) return 'N/A'
    let color = '#2e7d32'
    if (val < 70) color = '#f9a825'
    if (val < 60) color = '#d9534f'
    return <span style={{ color, fontWeight: 700, fontSize: '24px' }}>{val}</span>
  }

  return (
    <div className="review-panel">
      <h3>简历测评报告</h3>
      {resumeId && (
        <div className="profile-id-hint">
          已绑定简历：{resumeId.slice(0, 8)}...
          {profileId && <span> ｜ 资料 ID：{profileId.slice(0, 8)}...</span>}
        </div>
      )}

      {review.parse_error && (
        <div className="error">测评结果解析异常，以下为原始输出。</div>
      )}

      {review.overall_score !== null && review.overall_score !== undefined && (
        <div className="review-overall">
          <div className="review-score-label">综合评分</div>
          <div className="review-score-value">{renderScore(review.overall_score)}<span className="review-score-max">/100</span></div>
        </div>
      )}

      {review.summary && (
        <div className="panel review-summary-panel">
          <h4>简历总结</h4>
          <div className="review-summary-text">{review.summary}</div>
        </div>
      )}

      {review.strengths && review.strengths.length > 0 && (
        <div className="panel review-list-panel review-strengths">
          <h4>简历亮点</h4>
          <ul>
            {review.strengths.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}

      {review.risks && review.risks.length > 0 && (
        <div className="panel review-list-panel review-risks">
          <h4>简历风险</h4>
          <ul>
            {review.risks.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      )}

      {review.likely_questions && review.likely_questions.length > 0 && (
        <div className="panel review-questions-panel">
          <h4>可能面试问题</h4>
          <div className="question-list">
            {review.likely_questions.map((q, i) => (
              <div className="likely-question-item" key={i}>
                <div className="question-area">{q.area}</div>
                <div className="question-text">{q.question}</div>
                {q.follow_ups && q.follow_ups.length > 0 && (
                  <div className="follow-ups">
                    <span className="follow-ups-label">延伸追问：</span>
                    {q.follow_ups.map((f, j) => (
                      <span className="follow-up-tag" key={j}>{f}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {review.revision_suggestions && review.revision_suggestions.length > 0 && (
        <div className="panel review-list-panel review-suggestions">
          <h4>修改建议</h4>
          <ul>
            {review.revision_suggestions.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}

      {review.suitable_roles && review.suitable_roles.length > 0 && (
        <div className="panel review-roles-panel">
          <h4>适合岗位</h4>
          <div className="role-tags">
            {review.suitable_roles.map((r, i) => (
              <span className="role-tag" key={i}>{r}</span>
            ))}
          </div>
        </div>
      )}

      {review.skill_gap_suggestions && review.skill_gap_suggestions.length > 0 && (
        <div className="panel review-list-panel review-gaps">
          <h4>能力补强建议</h4>
          <ul>
            {review.skill_gap_suggestions.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}

      {review.raw_review && review.parse_error && (
        <div className="panel review-raw-panel">
          <h4>原始输出</h4>
          <pre className="raw-review-text">{review.raw_review}</pre>
        </div>
      )}

      <button className="start-btn" onClick={onRequestReview} disabled={!canReview}>
        重新生成测评
      </button>
    </div>
  )
}

export default ResumeReviewPanel
