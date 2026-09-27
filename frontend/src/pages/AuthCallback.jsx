import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Navigate } from 'react-router-dom'
import { FullPageSpinner } from '../components/ui/Spinner'
import { useAuth } from '../context/AuthContext'

/**
 * Supabase's client parses the OAuth redirect hash/query and establishes the
 * session automatically (detectSessionInUrl defaults to true) — this page just
 * waits for AuthContext to pick that up, then routes into the app.
 */
export default function AuthCallback() {
  const { t } = useTranslation()
  const { loading, isAuthenticated } = useAuth()

  useEffect(() => {
    document.title = t('auth.pageTitleCallback')
  }, [t])

  if (!loading && isAuthenticated) return <Navigate to="/app/recommend" replace />
  if (!loading && !isAuthenticated) return <Navigate to="/signin" replace />

  return <FullPageSpinner label={t('auth.finishingSignIn')} />
}
