import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

function Dashboard() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    fetch('/api/admin/stats')
      .then(r => r.json())
      .then(setStats)
  }, [])

  if (!stats) return <div className="loading">Загрузка...</div>

  return (
    <div className="dashboard">
      <h1>📊 Дашборд</h1>

      <div className="stats-grid">
        <div className="stat-card">
          <h3>Всего анализов</h3>
          <p className="stat-value">{stats.total_jobs}</p>
        </div>
        <div className="stat-card">
          <h3>Сегодня</h3>
          <p className="stat-value">{stats.today_jobs}</p>
        </div>
        <div className="stat-card">
          <h3>Успешность</h3>
          <p className="stat-value">{stats.success_rate}%</p>
        </div>
        <div className="stat-card">
          <h3>Стоимость LLM</h3>
          <p className="stat-value">${stats.total_cost}</p>
        </div>
      </div>

      <div className="chart-card">
        <h2>Анализы за неделю</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={stats.chart_data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="count" stroke="#667eea" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default Dashboard
