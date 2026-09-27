import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { FaqContent } from '../components/faq/FaqContent'

/**
 * Same FAQ content and Q&A widget as the public /faq page (both render the
 * shared <FaqContent /> — nothing duplicated), reachable here from inside
 * the authenticated app shell. No login required — see the public
 * /app/faq route in App.jsx, same pattern as /app/library.
 */
export default function AppFaqPage() {
  const { t } = useTranslation()
  useEffect(() => {
    document.title = t('faq.pageTitle')
  }, [t])

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 sm:py-12 lg:px-8">
      <FaqContent />
    </div>
  )
}
