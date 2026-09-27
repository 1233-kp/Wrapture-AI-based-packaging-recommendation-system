import { motion } from 'framer-motion'
import { AlertCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../../lib/api'
import { localizedName } from '../../lib/utils'
import { FullPageSpinner } from '../ui/Spinner'
import { FaqAccordionItem } from './FaqAccordionItem'
import { FaqAssistant } from './FaqAssistant'

/**
 * Shared FAQ body — heading, the FAQ assistant widget, and the accordion
 * list. Reused as-is by both the public marketing FAQ page (/faq) and the
 * in-app FAQ page (/app/faq) so the content and the Q&A widget exist in
 * exactly one place, not two. Each caller supplies its own outer chrome
 * (Navbar/Footer vs. AppShell) and page title.
 */
export function FaqContent() {
  const { t, i18n } = useTranslation()
  const [faqs, setFaqs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    api
      .faqs()
      .then((data) => setFaqs(data.faqs))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <>
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="text-center">
        <h1 className="font-display text-3xl font-extrabold text-ink-900 sm:text-4xl">{t('faq.heading')}</h1>
        <p className="mt-3 text-ink-500">{t('faq.subhead')}</p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mt-10"
      >
        <FaqAssistant />
      </motion.div>

      {loading && <FullPageSpinner label={t('faq.loading')} />}

      {!loading && error && (
        <div className="mt-8 flex items-center gap-2 rounded-xl border border-danger-bg bg-danger-bg px-4 py-3 text-sm text-danger">
          <AlertCircle className="size-4 shrink-0" aria-hidden="true" />
          {error}
        </div>
      )}

      {!loading && !error && (
        <div className="mt-10 space-y-3">
          {faqs.map((faq, i) => (
            <motion.div
              key={faq.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: Math.min(i * 0.03, 0.4) }}
            >
              <FaqAccordionItem
                question={localizedName(faq.question, faq.question_hi, i18n.language)}
                answer={localizedName(faq.answer, faq.answer_hi, i18n.language)}
              />
            </motion.div>
          ))}
        </div>
      )}
    </>
  )
}
