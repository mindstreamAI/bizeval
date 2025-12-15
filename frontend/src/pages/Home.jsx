import { useNavigate } from 'react-router-dom'
import { useState } from 'react'

function Home() {
  const navigate = useNavigate()
  const [showModal, setShowModal] = useState(false)

  return (
    <div className="home-page">
      <div className="home-header">
        <h1>🚀 BizEval</h1>
        <p>AI-платформа для анализа бизнес-идей</p>
      </div>

      <div className="home-cards">
        <div className="home-card active" onClick={() => navigate('/evaluate')}>
          <div className="card-icon">💡</div>
          <h3>Оценить новую идею</h3>
          <p>Комплексный AI-анализ вашей бизнес-идеи</p>
          <button className="card-btn">Начать анализ →</button>
        </div>

        <div className="home-card disabled" onClick={() => setShowModal(true)}>
          <div className="card-icon">📊</div>
          <h3>Анализ конкурентов</h3>
          <p>Глубокое исследование рынка и конкурентов</p>
          <div className="card-badge">В разработке</div>
        </div>

        <div className="home-card disabled" onClick={() => setShowModal(true)}>
          <div className="card-icon">🎯</div>
          <h3>Проверка гипотез</h3>
          <p>Тестирование бизнес-гипотез с AI</p>
          <div className="card-badge">В разработке</div>
        </div>
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2>🚧 В разработке</h2>
            <p>Этот модуль появится в следующей версии</p>
            <button onClick={() => setShowModal(false)}>Понятно</button>
          </div>
        </div>
      )}
    </div>
  )
}

export default Home
