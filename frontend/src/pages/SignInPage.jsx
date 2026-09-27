import { motion } from 'framer-motion'
import { ShieldCheck } from 'lucide-react'
import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, Navigate, useLocation } from 'react-router-dom'
import { OAuthButtons } from '../components/auth/OAuthButtons'
import { BrandMark } from '../components/ui/BrandMark'
import { LanguageToggle } from '../components/ui/LanguageToggle'
import { useAuth } from '../context/AuthContext'

export default function SignInPage() {
  const { t } = useTranslation()
  const { isAuthenticated } = useAuth()
  const location = useLocation()

  useEffect(() => {
    document.title = t('auth.pageTitleSignIn')
  }, [t])

  if (isAuthenticated) {
    const from = location.state?.from?.pathname || '/app/recommend'
    return <Navigate to={from} replace />
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-grain bg-ink-50 px-4 py-12">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        className="w-full max-w-md rounded-card border border-ink-200/70 bg-white p-8 shadow-soft-xl"
      >
        <div className="mb-6 flex items-center justify-center">
          <LanguageToggle />
        </div>
        <Link to="/" className="mb-6 flex items-center justify-center gap-2">
          <BrandMark size="size-10" />
          <span className="font-display text-xl font-extrabold text-ink-900">{t('common.brand')}</span>
        </Link>

        <h1 className="text-center text-2xl font-extrabold text-ink-900">{t('auth.welcomeBack')}</h1>
        <p className="mt-2 text-center text-sm text-ink-500">{t('auth.subhead')}</p>

        <div className="mt-8">
          <OAuthButtons />
        </div>

        <div className="mt-6 flex items-center justify-center gap-1.5 text-xs text-ink-400">
          <ShieldCheck className="size-3.5" aria-hidden="true" />
          {t('auth.supabaseNote')}
        </div>
      </motion.div>
    </div>
  )
}
