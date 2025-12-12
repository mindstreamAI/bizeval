import { useState, useEffect } from 'react'

function Settings() {
  const [settings, setSettings] = useState({
    s3_endpoint: '',
    s3_access_key: '',
    s3_secret_key: '',
    s3_bucket: '',
    openai_api_key: '',
    llm_model: 'gpt-4.1-nano'
  })
  const [loading, setLoading] = useState(false)
  const [restarting, setRestarting] = useState(false)

  useEffect(() => {
    fetch('/api/admin/settings')
      .then(r => r.json())
      .then(data => {
        setSettings(prev => ({ ...prev, ...data }))
      })
  }, [])

  const handleSave = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/admin/settings/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ settings })
      })
      const data = await res.json()
      alert(data.message)
    } catch (err) {
      alert('Ошибка: ' + err.message)
    }
    setLoading(false)
  }

  const handleRestart = async () => {
    if (!confirm('Перезапустить worker? Текущие задачи будут прерваны.')) return
    
    setRestarting(true)
    try {
      const res = await fetch('/api/admin/restart-worker', { method: 'POST' })
      const data = await res.json()
      alert(data.message)
    } catch (err) {
      alert('Ошибка: ' + err.message)
    }
    setRestarting(false)
  }

  const update = (key, value) => setSettings({ ...settings, [key]: value })

  return (
    <div className="page">
      <h1>⚙️ Настройки</h1>

      <div className="settings-card">
        <h2>☁️ Yandex Cloud S3</h2>
        
        <div className="field">
          <label>S3 Endpoint</label>
          <input
            value={settings.s3_endpoint}
            onChange={e => update('s3_endpoint', e.target.value)}
            placeholder="https://storage.yandexcloud.net"
          />
        </div>

        <div className="field">
          <label>Access Key</label>
          <input
            value={settings.s3_access_key}
            onChange={e => update('s3_access_key', e.target.value)}
            placeholder="YCAxxxxxxxx"
          />
        </div>

        <div className="field">
          <label>Secret Key</label>
          <input
            type="password"
            value={settings.s3_secret_key}
            onChange={e => update('s3_secret_key', e.target.value)}
            placeholder="YCMxxxxxxxx"
          />
        </div>

        <div className="field">
          <label>Bucket Name</label>
          <input
            value={settings.s3_bucket}
            onChange={e => update('s3_bucket', e.target.value)}
            placeholder="bizeval-reports"
          />
        </div>
      </div>

      <div className="settings-card">
        <h2>🤖 OpenAI</h2>
        
        <div className="field">
          <label>API Key</label>
          <input
            type="password"
            value={settings.openai_api_key}
            onChange={e => update('openai_api_key', e.target.value)}
            placeholder="sk-proj-..."
          />
        </div>

        <div className="field">
          <label>Модель</label>
          <select
            value={settings.llm_model}
            onChange={e => update('llm_model', e.target.value)}
          >
            <option>gpt-4o-mini</option>
            <option>gpt-4.1-nano</option>
            <option>gpt-4.1-mini</option>
          </select>
        </div>
      </div>

      <div className="btn-group">
        <button onClick={handleSave} disabled={loading} className="save-btn">
          {loading ? '💾 Сохранение...' : '💾 Сохранить настройки'}
        </button>
        
        <button onClick={handleRestart} disabled={restarting} className="restart-btn">
          {restarting ? '🔄 Перезапуск...' : '🔄 Перезапустить Worker'}
        </button>
      </div>

      <div className="info-box">
        💡 После изменения настроек нужно перезапустить worker для применения
      </div>
    </div>
  )
}

export default Settings
