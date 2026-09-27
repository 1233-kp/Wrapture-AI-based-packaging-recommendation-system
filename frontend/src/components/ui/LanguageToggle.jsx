import { useTranslation } from 'react-i18next'
import { setLanguage } from '../../i18n'
import { cn } from '../../lib/utils'

/** Small persistent EN/हिं switch — applies immediately (i18next re-renders
 * every useTranslation() consumer) and persists the choice to localStorage
 * via setLanguage(), a per-viewer UI preference, not app data. */
export function LanguageToggle({ className }) {
  const { i18n, t } = useTranslation()
  const current = i18n.language === 'hi' ? 'hi' : 'en'

  return (
    <div
      role="group"
      aria-label={t('nav.language')}
      className={cn('inline-flex items-center rounded-pill border border-ink-200 bg-white p-0.5 text-xs font-bold', className)}
    >
      <button
        type="button"
        onClick={() => setLanguage('en')}
        aria-pressed={current === 'en'}
        className={cn(
          'rounded-pill px-2.5 py-1 transition-colors',
          current === 'en' ? 'bg-brand-600 text-white' : 'text-ink-500 hover:text-ink-800'
        )}
      >
        EN
      </button>
      <button
        type="button"
        onClick={() => setLanguage('hi')}
        aria-pressed={current === 'hi'}
        className={cn(
          'rounded-pill px-2.5 py-1 transition-colors',
          current === 'hi' ? 'bg-brand-600 text-white' : 'text-ink-500 hover:text-ink-800'
        )}
      >
        हिं
      </button>
    </div>
  )
}
