import { useState, useEffect } from 'react'

function Jobs() {
  const [jobs, setJobs] = useState([])

  useEffect(() => {
    fetch('/api/admin/jobs')
      .then(r => r.json())
      .then(setJobs)
  }, [])

  const statusColor = (s) => ({
    pending: '#ffa500',
    running: '#2196f3',
    done: '#4caf50',
    failed: '#f44336',
    partial: '#ff9800'
  }[s] || '#999')

  return (
    <div className="page">
      <h1>📋 Анализы</h1>
      <table className="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Дата</th>
            <th>Статус</th>
            <th>Идея</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map(job => (
            <tr key={job.id}>
              <td>{job.id}</td>
              <td>{new Date(job.created_at).toLocaleString('ru')}</td>
              <td>
                <span className="status-badge" style={{background: statusColor(job.status)}}>
                  {job.status}
                </span>
              </td>
              <td className="idea-cell">{job.idea}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default Jobs
