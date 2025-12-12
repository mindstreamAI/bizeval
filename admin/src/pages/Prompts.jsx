import { useState, useEffect } from 'react'

function Prompts() {
  const [prompts, setPrompts] = useState({})
  const [editing, setEditing] = useState(null)
  const [text, setText] = useState('')

  useEffect(() => {
    loadPrompts()
  }, [])

  const loadPrompts = () => {
    fetch('/api/admin/prompts')
      .then(r => r.json())
      .then(setPrompts)
  }

  const savePrompt = async (id) => {
    await fetch(`/api/admin/prompts/${id}/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt_template: text })
    })
    setEditing(null)
    loadPrompts()
  }

  const trackNames = {
    track1_audience: '👥 Аудитория',
    track2_global: '🌍 Глобальные конкуренты',
    track3_local: '📍 Локальный рынок'
  }

  return (
    <div className="page">
      <h1>✏️ Промпты</h1>
      {Object.entries(prompts).map(([track, versions]) => {
        const active = versions.find(v => v.is_active)
        return (
          <div key={track} className="prompt-card">
            <h2>{trackNames[track]}</h2>
            <p>Версия: {active?.version} | Обновлено: {new Date(active?.updated_at).toLocaleString('ru')}</p>
            
            {editing === active?.id ? (
              <>
                <textarea
                  value={text}
                  onChange={e => setText(e.target.value)}
                  rows={15}
                  className="prompt-editor"
                />
                <div className="btn-group">
                  <button onClick={() => savePrompt(active.id)} className="btn-primary">Сохранить</button>
                  <button onClick={() => setEditing(null)} className="btn-secondary">Отмена</button>
                </div>
              </>
            ) : (
              <>
                <pre className="prompt-preview">{active?.prompt_template}</pre>
                <button onClick={() => {
                  setEditing(active.id)
                  setText(active.prompt_template)
                }} className="btn-primary">Редактировать</button>
              </>
            )}
          </div>
        )
      })}
    </div>
  )
}

export default Prompts
