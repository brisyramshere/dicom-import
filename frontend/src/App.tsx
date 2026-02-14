import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { MainLayout } from './components/MainLayout'
import { SeriesPage } from './pages/SeriesPage'
import { ConfigsPage } from './pages/ConfigsPage'
import { StatsPage } from './pages/StatsPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Navigate to="/series" replace />} />
          <Route path="series" element={<SeriesPage />} />
          <Route path="configs" element={<ConfigsPage />} />
          <Route path="stats" element={<StatsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
