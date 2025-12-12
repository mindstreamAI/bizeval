import { NavLink } from 'react-router-dom'

function Sidebar({ onLogout }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>🚀 BizEval</h2>
        <p>Admin Panel</p>
      </div>
      
      <nav className="sidebar-nav">
        <NavLink to="/" end>📊 Дашборд</NavLink>
        <NavLink to="/jobs">📋 Анализы</NavLink>
        <NavLink to="/prompts">✏️ Промпты</NavLink>
        <NavLink to="/logs">📜 Логи LLM</NavLink>
      </nav>
      
      <button onClick={onLogout} className="logout-btn">
        🚪 Выйти
      </button>
    </aside>
  )
}

export default Sidebar
