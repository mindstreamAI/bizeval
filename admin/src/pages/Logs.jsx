import { useState, useEffect } from 'react'

function Logs() {
  const [logs, setLogs] = useState([])

  useEffect(() => {
    fetch('/api/admin/llm-logs')
      .then(r => r.json())
      .then(setLogs)
  }, [])

  return (
    <div className="page">
      <h1>📜 Логи LLM</h1>
      <table className="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Track ID</th>
            <th>Модель</th>
            <th>Токены</th>
            <th>Время (мс)</th>
            <th>Статус</th>
            <th>Дата</th>
          </tr>
        </thead>
        <tbody>
          {logs.map(log => (
            <tr key={log.id}>
              <td>{log.id}</td>
              <td>{log.track_id}</td>
              <td>{log.model}</td>
              <td>{log.tokens_used}</td>
              <td>{log.response_time_ms}</td>
              <td>
                <span className={`status-badge ${log.status}`}>
                  {log.status}
                </span>
              </td>
              <td>{new Date(log.created_at).toLocaleString('ru')}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default Logs
