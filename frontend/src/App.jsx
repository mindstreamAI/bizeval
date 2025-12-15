import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import Evaluate from './pages/Evaluate'
import Results from './pages/Results'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/evaluate" element={<Evaluate />} />
      <Route path="/results/:jobId" element={<Results />} />
    </Routes>
  )
}

export default App
