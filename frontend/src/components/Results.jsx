import { useState, useEffect } from 'react'

function Results({ jobId, onBack }) {
  const [status, setStatus] = useState('loading')
  const [report, setReport] = useState(null)

  useEffect(() => {
    const check = setInterval(async () => {
      try {
        const res = await fetch(`/api/report/${jobId}`)
        const data = await res.json()

        if (data.status === 'done') {
          setReport(data.report)
          setStatus('done')
          clearInterval(check)
        } else if (data.status === 'failed') {
          setStatus('error')
          clearInterval(check)
        }
      } catch (err) {
        console.error(err)
      }
    }, 2000)

    return () => clearInterval(check)
  }, [jobId])

  if (status === 'loading') {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <h2>Анализируем вашу идею...</h2>
        <p>Это займет ~15 секунд</p>
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="error">
        <h2>❌ Ошибка анализа</h2>
        <button onClick={onBack}>← Назад</button>
      </div>
    )
  }

  const { consolidation } = report

  return (
    <div className="results">
      <button onClick={onBack} className="back">← Новый анализ</button>

      <section className="summary">
        <h2>📊 Executive Summary</h2>
        <p>{consolidation.executive_summary}</p>
      </section>

      <section className="swot">
        <h2>🎯 SWOT Анализ</h2>
        <div className="swot-grid">
          <div className="swot-item green">
            <h3>✅ Strengths</h3>
            <ul>{consolidation.swot.strengths.map((s, i) => <li key={i}>{s}</li>)}</ul>
          </div>
          <div className="swot-item red">
            <h3>⚠️ Weaknesses</h3>
            <ul>{consolidation.swot.weaknesses.map((w, i) => <li key={i}>{w}</li>)}</ul>
          </div>
          <div className="swot-item blue">
            <h3>🚀 Opportunities</h3>
            <ul>{consolidation.swot.opportunities.map((o, i) => <li key={i}>{o}</li>)}</ul>
          </div>
          <div className="swot-item orange">
            <h3>⚡ Threats</h3>
            <ul>{consolidation.swot.threats.map((t, i) => <li key={i}>{t}</li>)}</ul>
          </div>
        </div>
      </section>

      <section className="recs">
        <h2>💡 Рекомендации</h2>
        <ol>{consolidation.recommendations.map((r, i) => <li key={i}>{r}</li>)}</ol>
      </section>

      <section className="score">
        <h2>⭐ Общая оценка: {consolidation.overall_score}/10</h2>
      </section>

      <section className="downloads">
        <h3>📥 Скачать отчет:</h3>
        <a href={`/api/report/${jobId}/download/pdf`} className="btn">PDF</a>
        <a href={`/api/report/${jobId}/download/docx`} className="btn">DOCX</a>
      </section>
    </div>
  )
}

export default Results
