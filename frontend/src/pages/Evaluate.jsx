import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

function Evaluate() {
  const navigate = useNavigate()
  const [sessionId, setSessionId] = useState(null)
  const [ws, setWs] = useState(null)
  const [messages, setMessages] = useState([
    { role: 'ai', text: 'Привет! 👋 Я AI-аналитик бизнес-идей. Заполни форму ниже — я проанализирую твою идею, оценю перспективы и дам конкретные рекомендации для развития.' }
  ])
  const [formVisible, setFormVisible] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [report, setReport] = useState(null)
  const [jobId, setJobId] = useState(null)
  const messagesEndRef = useRef(null)
  const shouldScrollRef = useRef(false)
  
  const [formData, setFormData] = useState({
    idea_description: '',
    target_audience: '',
    industry: 'Tech',
    geography: 'Russia',
    value_proposition: '',
    monetization_model: '',
    project_stage: 'idea',
    additional_comments: ''
  })

  const scrollToBottom = () => {
    if (shouldScrollRef.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    fetch('/api/session/start', { method: 'POST' })
      .then(r => r.json())
      .then(data => {
        setSessionId(data.session_id)
        
        const websocket = new WebSocket(`ws://155.212.222.110:8000/ws/${data.session_id}`)
        
        websocket.onopen = () => {
          console.log('WebSocket connected')
        }
        
        websocket.onmessage = (event) => {
          const data = JSON.parse(event.data)
          console.log('WS message:', data)
          
          shouldScrollRef.current = true
          
          if (data.type === 'connected') {
            console.log(data.message)
          } else if (data.type === 'analysis_started') {
            addMessage('ai', data.message)
          } else if (data.type === 'track_started') {
            addMessage('ai', data.message)
          } else if (data.type === 'track_completed') {
            addMessage('ai', data.message)
          } else if (data.type === 'consolidation_started') {
            addMessage('ai', data.message)
          } else if (data.type === 'analysis_completed') {
            addMessage('ai', data.message)
            setReport(data.data.report)
            setJobId(data.data.job_id)
            setAnalyzing(false)
          } else if (data.type === 'analysis_failed') {
            addMessage('ai', data.message)
            setAnalyzing(false)
          }
        }
        
        websocket.onerror = (error) => {
          console.error('WebSocket error:', error)
        }
        
        websocket.onclose = () => {
          console.log('WebSocket closed')
        }
        
        setWs(websocket)
        
        return () => websocket.close()
      })
  }, [])

  const addMessage = (role, text) => {
    setMessages(prev => [...prev, { role, text }])
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!formData.idea_description || !formData.target_audience || !formData.value_proposition || !formData.monetization_model) {
      alert('Заполните все обязательные поля')
      return
    }
    
    shouldScrollRef.current = true
    setFormVisible(false)
    setAnalyzing(true)
    
    const summary = `📋 Идея: ${formData.idea_description.substring(0, 100)}...
👥 Аудитория: ${formData.target_audience.substring(0, 80)}...
🏭 Индустрия: ${formData.industry}
🌍 География: ${formData.geography}
💰 Монетизация: ${formData.monetization_model}
📊 Стадия: ${formData.project_stage}`
    
    addMessage('user', summary)
    
    try {
      const res = await fetch(`/api/form/submit/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      
      if (!res.ok) throw new Error('Ошибка отправки формы')
      
      const data = await res.json()
      setJobId(data.job_id)
      
    } catch (err) {
      addMessage('ai', '❌ Ошибка: ' + err.message)
      setAnalyzing(false)
    }
  }

  const handleNewAnalysis = () => {
    navigate('/')
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <button onClick={() => navigate('/')} className="back-link">← Назад</button>
        <h3>Анализ бизнес-идеи</h3>
      </div>

      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-message ${msg.role}`}>
            <div className="message-avatar">{msg.role === 'ai' ? '🤖' : '👤'}</div>
            <div className="message-text">{msg.text}</div>
          </div>
        ))}

        {formVisible && (
          <div className="chat-message user">
            <div className="message-avatar">👤</div>
            <div className="message-form">
              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label>Описание идеи *</label>
                  <textarea
                    value={formData.idea_description}
                    onChange={e => setFormData({...formData, idea_description: e.target.value})}
                    placeholder="Опишите вашу бизнес-идею подробно..."
                    rows="3"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Целевая аудитория *</label>
                  <textarea
                    value={formData.target_audience}
                    onChange={e => setFormData({...formData, target_audience: e.target.value})}
                    placeholder="Кто ваши клиенты?..."
                    rows="2"
                    required
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>Индустрия</label>
                    <select value={formData.industry} onChange={e => setFormData({...formData, industry: e.target.value})}>
                      <option>Tech</option>
                      <option>E-commerce</option>
                      <option>Healthcare</option>
                      <option>Education</option>
                      <option>Finance</option>
                      <option>Other</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label>География</label>
                    <select value={formData.geography} onChange={e => setFormData({...formData, geography: e.target.value})}>
                      <option>Russia</option>
                      <option>USA</option>
                      <option>Europe</option>
                      <option>Asia</option>
                      <option>Global</option>
                    </select>
                  </div>
                </div>

                <div className="form-group">
                  <label>Ценностное предложение *</label>
                  <textarea
                    value={formData.value_proposition}
                    onChange={e => setFormData({...formData, value_proposition: e.target.value})}
                    placeholder="Что уникального в вашем решении?..."
                    rows="2"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Модель монетизации *</label>
                  <input
                    value={formData.monetization_model}
                    onChange={e => setFormData({...formData, monetization_model: e.target.value})}
                    placeholder="Как планируете зарабатывать?..."
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Стадия проекта</label>
                  <select value={formData.project_stage} onChange={e => setFormData({...formData, project_stage: e.target.value})}>
                    <option value="idea">Идея</option>
                    <option value="prototype">Прототип</option>
                    <option value="first_clients">Первые клиенты</option>
                    <option value="scale">Масштабирование</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Дополнительные комментарии</label>
                  <textarea
                    value={formData.additional_comments}
                    onChange={e => setFormData({...formData, additional_comments: e.target.value})}
                    placeholder="Что еще важно учесть?... (необязательно)"
                    rows="2"
                  />
                </div>

                <button type="submit" className="submit-btn" disabled={analyzing}>
                  🚀 Запустить анализ
                </button>
              </form>
            </div>
          </div>
        )}

        {report && (
          <div className="chat-message ai">
            <div className="message-avatar">🤖</div>
            <div className="message-report">
              
              <div className="report-section">
                <h3>📊 Executive Summary</h3>
                <p>{report.consolidation.executive_summary}</p>
              </div>

              <div className="report-section">
                <h3>👥 Целевая Аудитория</h3>
                <div className="info-grid">
                  <div className="info-item">
                    <span className="info-label">Приоритетный сегмент:</span>
                    <span className="info-value">{report.consolidation.audience_analysis?.priority_segment}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Product-Market Fit:</span>
                    <span className="info-value">{report.consolidation.audience_analysis?.market_fit_score}/10</span>
                  </div>
                </div>
                <p><strong>Ключевые сегменты:</strong> {report.consolidation.audience_analysis?.key_segments.join(', ')}</p>
              </div>

              <div className="report-section">
                <h3>🌍 Конкурентная Среда</h3>
                <div className="info-grid">
                  <div className="info-item">
                    <span className="info-label">Уровень конкуренции:</span>
                    <span className="info-value">{report.consolidation.competitive_landscape?.competition_intensity}/10</span>
                  </div>
                </div>
                <p><strong>Главные конкуренты:</strong> {report.consolidation.competitive_landscape?.main_competitors.join(', ')}</p>
              </div>

              <div className="report-section">
                <h3>📍 Локальный Рынок</h3>
                <div className="info-grid">
                  <div className="info-item">
                    <span className="info-label">Привлекательность:</span>
                    <span className="info-value">{report.consolidation.local_market?.market_attractiveness}/10</span>
                  </div>
                </div>
              </div>

              <div className="report-section">
                <h3>🎯 SWOT Анализ</h3>
                <div className="swot-grid">
                  <div className="swot-item green">
                    <h4>✅ Strengths</h4>
                    <ul>{report.consolidation.swot.strengths.map((s, i) => <li key={i}>{s}</li>)}</ul>
                  </div>
                  <div className="swot-item red">
                    <h4>⚠️ Weaknesses</h4>
                    <ul>{report.consolidation.swot.weaknesses.map((w, i) => <li key={i}>{w}</li>)}</ul>
                  </div>
                  <div className="swot-item blue">
                    <h4>🚀 Opportunities</h4>
                    <ul>{report.consolidation.swot.opportunities.map((o, i) => <li key={i}>{o}</li>)}</ul>
                  </div>
                  <div className="swot-item orange">
                    <h4>⚡ Threats</h4>
                    <ul>{report.consolidation.swot.threats.map((t, i) => <li key={i}>{t}</li>)}</ul>
                  </div>
                </div>
              </div>

              <div className="report-section">
                <h3>💡 Стратегические Рекомендации</h3>
                {['high', 'medium', 'low'].map(priority => {
                  const recs = report.consolidation.strategic_recommendations?.filter(r => r.priority === priority)
                  if (!recs || recs.length === 0) return null
                  const emoji = {high: '🔴', medium: '🟡', low: '🟢'}[priority]
                  const label = {high: 'Высокий', medium: 'Средний', low: 'Низкий'}[priority]
                  return (
                    <div key={priority} className="recs-group">
                      <h4>{emoji} {label} приоритет</h4>
                      {recs.map((r, i) => (
                        <div key={i} className="rec-item">
                          <div className="rec-header">
                            <span className="rec-category">{{'product': '🛠️', 'marketing': '📢', 'business_model': '💰', 'risks': '⚠️'}[r.category]}</span>
                            <strong>{r.recommendation}</strong>
                          </div>
                          <div className="rec-rationale">{r.rationale}</div>
                        </div>
                      ))}
                    </div>
                  )
                })}
              </div>

              <div className="report-section score-section">
                <h3>⭐ Итоговая Оценка</h3>
                <div className="score-grid">
                  <div className="score-item">
                    <div className="score-value">{report.consolidation.overall_score}</div>
                    <div className="score-label">Общий балл</div>
                  </div>
                  <div className="score-item">
                    <div className="score-value">{{'low': '🟢', 'medium': '🟡', 'high': '🔴'}[report.consolidation.risk_level]}</div>
                    <div className="score-label">Риск: {report.consolidation.risk_level}</div>
                  </div>
                  <div className="score-item">
                    <div className="score-value">📈</div>
                    <div className="score-label">{report.consolidation.investment_readiness?.replace('_', ' ')}</div>
                  </div>
                </div>
              </div>

              <div className="report-actions">
                <a href={`/api/report/${jobId}/download/pdf`} className="action-btn pdf">📥 Скачать PDF</a>
                <a href={`/api/report/${jobId}/download/docx`} className="action-btn docx">📥 Скачать DOCX</a>
                <button onClick={handleNewAnalysis} className="action-btn new">🔄 Новый анализ</button>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </div>
  )
}

export default Evaluate
