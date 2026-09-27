import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { ProtectedRoute } from './components/layout/ProtectedRoute'
import { AuthProvider } from './context/AuthContext'
import AppFaqPage from './pages/AppFaqPage'
import AuthCallback from './pages/AuthCallback'
import DashboardPage from './pages/DashboardPage'
import FaqPage from './pages/FaqPage'
import HistoryPage from './pages/HistoryPage'
import LandingPage from './pages/LandingPage'
import PackagingLibraryPage from './pages/PackagingLibraryPage'
import RecommendPage from './pages/RecommendPage'
import ResultsPage from './pages/ResultsPage'
import SettingsPage from './pages/SettingsPage'
import SignInPage from './pages/SignInPage'
import SustainabilityPage from './pages/SustainabilityPage'
import TraceabilityPage from './pages/TraceabilityPage'
import VerifyPage from './pages/VerifyPage'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/signin" element={<SignInPage />} />
          <Route path="/auth/callback" element={<AuthCallback />} />
          <Route path="/verify/:reportId" element={<VerifyPage />} />
          <Route path="/faq" element={<FaqPage />} />
          {/* Old path from when this briefly lived outside the app shell. */}
          <Route path="/library" element={<Navigate to="/app/library" replace />} />

          <Route element={<AppShell />}>
            {/* Public reference pages — no ProtectedRoute — but still
                rendered inside the app shell so they get the same
                sidebar/header as every other /app/* page instead of the
                marketing layout. */}
            <Route path="/app/library" element={<PackagingLibraryPage />} />
            <Route path="/app/faq" element={<AppFaqPage />} />

            <Route element={<ProtectedRoute />}>
              <Route path="/app/recommend" element={<RecommendPage />} />
              <Route path="/app/results" element={<ResultsPage />} />
              <Route path="/app/dashboard" element={<DashboardPage />} />
              <Route path="/app/history" element={<HistoryPage />} />
              <Route path="/app/settings" element={<SettingsPage />} />
              <Route path="/app/sustainability" element={<SustainabilityPage />} />
              <Route path="/app/traceability" element={<TraceabilityPage />} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
