import { motion } from 'framer-motion'
import { CheckCircle2, TrendingDown, TrendingUp } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../../context/AuthContext'
import { api } from '../../lib/api'
import { cn } from '../../lib/utils'
import { Card } from '../ui/Card'

const OPTIONS = [
  { value: 'spoiled_early', icon: TrendingDown, tone: 'danger' },
  { value: 'as_expected', icon: CheckCircle2, tone: 'brand' },
  { value: 'lasted_longer', icon: TrendingUp, tone: 'teal' },
]

const TONE_CLASSES = {
  danger: { active: 'border-danger bg-danger-bg text-danger', icon: 'text-danger' },
  brand: { active: 'border-brand-500 bg-brand-50 text-brand-700', icon: 'text-brand-600' },
  teal: { active: 'border-teal-500 bg-teal-50 text-teal-700', icon: 'text-teal-600' },
}

/**
 * Purely optional data capture — "was this accurate?" — never blocks
 * viewing or using the report. No retraining/auto-improvement happens from
 * this; it's stored for later human review only, which the copy says
 * plainly rather than implying the app "learns" from it instantly.
 */
export function ReportFeedback({ reportId, initialOutcome = null }) {
  const { t } = useTranslation()
  const { accessToken } = useAuth()
  const [outcome, setOutcome] = useState(initialOutcome)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const handleSelect = async (value) => {
    if (submitting || value === outcome) return
    setSubmitting(true)
    setError(null)
    const previous = outcome
    setOutcome(value)
    try {
      await api.submitReportFeedback(accessToken, reportId, value)
    } catch (err) {
      setOutcome(previous)
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Card className="p-5">
      <p className="text-sm font-bold text-ink-900">{t('results.feedbackTitle')}</p>
      <p className="mt-1 text-xs text-ink-400">{t('results.feedbackDisclaimer')}</p>

      <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-3">
        {OPTIONS.map((opt) => {
          const active = outcome === opt.value
          const tone = TONE_CLASSES[opt.tone]
          return (
            <motion.button
              key={opt.value}
              type="button"
              whileTap={{ scale: 0.97 }}
              disabled={submitting}
              onClick={() => handleSelect(opt.value)}
              className={cn(
                'flex items-center justify-center gap-2 rounded-xl border px-3 py-2.5 text-xs font-semibold transition-colors cursor-pointer disabled:cursor-wait',
                active ? tone.active : 'border-ink-200 bg-white text-ink-600 hover:border-ink-300'
              )}
            >
              <opt.icon className={cn('size-4 shrink-0', active ? tone.icon : 'text-ink-400')} aria-hidden="true" />
              {t(`results.feedbackOption.${opt.value}`)}
            </motion.button>
          )
        })}
      </div>

      {outcome && !error && <p className="mt-3 text-xs font-medium text-brand-700">{t('results.feedbackThanks')}</p>}
      {error && <p className="mt-3 text-xs font-medium text-danger">{error}</p>}
    </Card>
  )
}
