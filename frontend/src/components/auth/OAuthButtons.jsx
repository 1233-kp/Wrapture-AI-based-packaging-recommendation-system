import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../../context/AuthContext'
import { GithubIcon, GoogleIcon } from '../ui/BrandIcons'

/**
 * Adapted from 21st.dev "Social Auth Card" (ruixen.ui, id 7966): kept the
 * stacked full-width branded button pattern, dropped the email/password form
 * and LinkedIn button (OAuth-only per spec), restyled onto our design tokens,
 * and added a loading/disabled state per provider.
 */
export function OAuthButtons() {
  const { t } = useTranslation()
  const { signInWithGoogle, signInWithGithub } = useAuth()
  const [pending, setPending] = useState(null)

  const handle = async (provider, action) => {
    setPending(provider)
    try {
      await action()
    } catch {
      setPending(null)
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <button
        type="button"
        disabled={!!pending}
        onClick={() => handle('google', signInWithGoogle)}
        className="flex min-h-12 w-full cursor-pointer items-center justify-center gap-3 rounded-xl border border-ink-200 bg-white px-4 py-3 text-sm font-semibold text-ink-800 shadow-soft-sm transition-colors hover:bg-ink-50 disabled:opacity-60 disabled:cursor-wait"
      >
        {pending === 'google' ? (
          <span className="size-[18px] animate-spin rounded-full border-2 border-ink-300 border-t-ink-700" />
        ) : (
          <GoogleIcon />
        )}
        {t('auth.continueWithGoogle')}
      </button>

      <button
        type="button"
        disabled={!!pending}
        onClick={() => handle('github', signInWithGithub)}
        className="flex min-h-12 w-full cursor-pointer items-center justify-center gap-3 rounded-xl bg-ink-900 px-4 py-3 text-sm font-semibold text-white shadow-soft-sm transition-colors hover:bg-ink-800 disabled:opacity-60 disabled:cursor-wait"
      >
        {pending === 'github' ? (
          <span className="size-[18px] animate-spin rounded-full border-2 border-white/30 border-t-white" />
        ) : (
          <GithubIcon className="size-[18px]" aria-hidden="true" />
        )}
        {t('auth.continueWithGithub')}
      </button>
    </div>
  )
}
