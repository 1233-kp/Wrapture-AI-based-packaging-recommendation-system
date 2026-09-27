import { useTranslation } from 'react-i18next'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { FullPageSpinner } from '../ui/Spinner'

export function ProtectedRoute() {
  const { t } = useTranslation()
  const { loading, isAuthenticated } = useAuth()
  const location = useLocation()

  if (loading) return <FullPageSpinner label={t('auth.checkingSession')} />
  if (!isAuthenticated) return <Navigate to="/" state={{ from: location }} replace />
  return <Outlet />
}
