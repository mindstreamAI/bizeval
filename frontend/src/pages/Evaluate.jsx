import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

function Evaluate() {
  const navigate = useNavigate()
  const [sessionId, setSessionId] = useState(null)
  const [ws, setWs] = useState(null)
  const [messages, setMessages] = useState([
    { role: 'ai', text: 'Привет! 👋 Я стратегический консультант для анализа бизнес-возможностей. Заполни форму ниже — я проведу глубокий анализ направлений роста, изучу аналоги и антилоги, проанализирую клиентские боли и дам итоговые рекомендации.' }
  ])
  const [formVisible, setFormVisible] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [report, setReport] = useState(null)
  const [jobId, setJobId] = useState(null)
  const messagesEndRef = useRef(null)
  const shouldScrollRef = useRef(false)
  
  const [formData, setFormData] = useState({
    industry_products: '',
    customers: '',
    business_model: '',
    geography: '',
    constraints: '',
    strategic_goals: '',
    additional_info: ''
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
        
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const websocket = new WebSocket(`${wsProtocol}//${window.location.hostname}:8000/ws/${data.session_id}`)
        
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
    
    if (!formData.industry_products || !formData.customers || !formData.business_model || !formData.geography) {
      alert('Заполните все обязательные поля (первые 4)')
      return
    }
    
    shouldScrollRef.current = true
    setFormVisible(false)
    setAnalyzing(true)
    
    const summary = `📋 Контекст бизнеса:

🏭 Отрасль и продукты: ${formData.industry_products.substring(0, 100)}...
👥 Клиенты: ${formData.customers.substring(0, 80)}...
💰 Бизнес-модель: ${formData.business_model.substring(0, 80)}...
🌍 География: ${formData.geography}
⚠️ Ограничения: ${formData.constraints || 'не указаны'}
🎯 Цели: ${formData.strategic_goals || 'не указаны'}`
    
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
        <h3>Стратегический анализ</h3>
      </div>

      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-message ${msg.role}`}>
            <div className="message-avatar">{msg.role === 'ai' ? '🤖' : '👤'}</div>
            <div className="message-text" style={{whiteSpace: 'pre-wrap'}}>{msg.text}</div>
          </div>
        ))}

        {formVisible && (
          <div className="chat-message user">
            <div className="message-avatar">👤</div>
            <div className="message-form">
              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label>Отрасль, продукты и услуги *</label>
                  <textarea
                    value={formData.industry_products}
                    onChange={e => setFormData({...formData, industry_products: e.target.value})}
                    placeholder="Опишите вашу отрасль, ключевые продукты/услуги и чем вы реально помогаете клиентам..."
                    rows="3"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Клиенты и их задачи *</label>
                  <textarea
                    value={formData.customers}
                    onChange={e => setFormData({...formData, customers: e.target.value})}
                    placeholder="Кто ваши клиенты (типы, размеры, сегменты) и какие задачи (jobs-to-be-done) они решают с вашей помощью..."
                    rows="3"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Бизнес-модель и монетизация *</label>
                  <textarea
                    value={formData.business_model}
                    onChange={e => setFormData({...formData, business_model: e.target.value})}
                    placeholder="Как вы зарабатываете деньги: источники выручки, ключевые форматы, модель ценообразования..."
                    rows="3"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>География *</label>
                  <textarea
                    value={formData.geography}
                    onChange={e => setFormData({...formData, geography: e.target.value})}
                    placeholder="В каких странах/регионах вы работаете и какие географии считаете потенциальными..."
                    rows="2"
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Ограничения</label>
                  <textarea
                    value={formData.constraints}
                    onChange={e => setFormData({...formData, constraints: e.target.value})}
                    placeholder="Ваши ограничения: ресурсы, команда, технологии, регуляция, время основателя и т.п. (необязательно)"
                    rows="2"
                  />
                </div>

                <div className="form-group">
                  <label>Стратегические цели и амбиции</label>
                  <textarea
                    value={formData.strategic_goals}
                    onChange={e => setFormData({...formData, strategic_goals: e.target.value})}
                    placeholder="Ваши стратегические цели, амбиции, видение развития... (необязательно)"
                    rows="2"
                  />
                </div>

                <div className="form-group">
                  <label>Дополнительная информация</label>
                  <textarea
                    value={formData.additional_info}
                    onChange={e => setFormData({...formData, additional_info: e.target.value})}
                    placeholder="Любые дополнительные детали, которые считаете важными для выбора новых ниш, рынков и направлений роста... (необязательно)"
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
                <h2>📊 АНАЛИЗ РЫНКОВ И НИШ</h2>
                <div style={{whiteSpace: 'pre-wrap', lineHeight: '1.7'}}>
                  {report.tracks?.market_analysis || report.consolidation?.market_analysis || 'Данные отсутствуют'}
                </div>
              </div>

              <div className="report-section">
                <h2>🔍 АНАЛИЗ АНАЛОГОВ И АНТИЛОГОВ</h2>
                <div style={{whiteSpace: 'pre-wrap', lineHeight: '1.7'}}>
                  {report.tracks?.growth_opportunities || report.consolidation?.growth_opportunities || 'Данные отсутствуют'}
                </div>
              </div>

              <div className="report-section">
                <h2>💡 АНАЛИЗ КЛИЕНТСКИХ БОЛЕЙ</h2>
                <div style={{whiteSpace: 'pre-wrap', lineHeight: '1.7'}}>
                  {report.tracks?.risks_constraints || report.consolidation?.risks_constraints || 'Данные отсутствуют'}
                </div>
              </div>

              <div className="report-section score-section">
                <h2>📋 ИТОГОВОЕ РЕЗЮМЕ</h2>
                <div style={{whiteSpace: 'pre-wrap', lineHeight: '1.7', color: 'white'}}>
                  {report.consolidation?.executive_summary || 'Данные отсутствуют'}
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