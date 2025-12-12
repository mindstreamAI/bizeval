import { useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Jobs from './pages/Jobs'
import Prompts from './pages/Prompts'
import Logs from './pages/Logs'
import Settings from './pages/Settings'
import Sidebar from './components/Sidebar'

function App() {
  const [token, setToken] = useState(localStorage.getItem('admin_token'))

  const logout = () => {
    localStorage.removeItem('admin_token')
    setToken(null)
  }

  if (!token) {
    return <Login onLogin={(t) => {
      localStorage.setItem('admin_token', t)
      setToken(t)
    }} />
  }

  return (
    <div className="admin-layout">
      <Sidebar onLogout={logout} />
      <main className="admin-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/jobs" element={<Jobs />} />
          <Route path="/prompts" element={<Prompts />} />
          <Route path="/logs" element={<Logs />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
