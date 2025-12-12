import { useState } from 'react'

function Form({ onSubmit }) {
  const [loading, setLoading] = useState(false)
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

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      const sessionRes = await fetch('/api/session/start', { method: 'POST' })
      const { session_id } = await sessionRes.json()

      const formRes = await fetch(`/api/form/submit/${session_id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      const { job_id } = await formRes.json()

      onSubmit(session_id, job_id)
    } catch (err) {
      alert('Ошибка: ' + err.message)
      setLoading(false)
    }
  }

  const update = (field, value) => setFormData({ ...formData, [field]: value })

  return (
    <form onSubmit={handleSubmit} className="form">
      <div className="field">
        <label>Описание идеи *</label>
        <textarea value={formData.idea_description} onChange={e => update('idea_description', e.target.value)} required rows={4} />
      </div>

      <div className="field">
        <label>Целевая аудитория *</label>
        <textarea value={formData.target_audience} onChange={e => update('target_audience', e.target.value)} required rows={3} />
      </div>

      <div className="row">
        <div className="field">
          <label>Индустрия *</label>
          <select value={formData.industry} onChange={e => update('industry', e.target.value)} required>
            <option>Tech</option>
            <option>E-commerce</option>
            <option>Healthcare</option>
            <option>Education</option>
            <option>Finance</option>
            <option>Other</option>
          </select>
        </div>

        <div className="field">
          <label>География *</label>
          <select value={formData.geography} onChange={e => update('geography', e.target.value)} required>
            <option>Russia</option>
            <option>USA</option>
            <option>Europe</option>
            <option>Asia</option>
            <option>Global</option>
          </select>
        </div>
      </div>

      <div className="field">
        <label>Ценностное предложение *</label>
        <textarea value={formData.value_proposition} onChange={e => update('value_proposition', e.target.value)} required rows={3} />
      </div>

      <div className="field">
        <label>Модель монетизации *</label>
        <input value={formData.monetization_model} onChange={e => update('monetization_model', e.target.value)} required />
      </div>

      <div className="field">
        <label>Стадия проекта *</label>
        <select value={formData.project_stage} onChange={e => update('project_stage', e.target.value)} required>
          <option value="idea">Идея</option>
          <option value="prototype">Прототип</option>
          <option value="first_clients">Первые клиенты</option>
          <option value="scale">Масштабирование</option>
        </select>
      </div>

      <div className="field">
        <label>Комментарии</label>
        <textarea value={formData.additional_comments} onChange={e => update('additional_comments', e.target.value)} rows={2} />
      </div>

      <button type="submit" disabled={loading}>
        {loading ? '⏳ Отправка...' : '🚀 Запустить анализ'}
      </button>
    </form>
  )
}

export default Form
