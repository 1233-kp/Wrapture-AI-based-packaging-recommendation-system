import { motion } from 'framer-motion'
import { Search, Send } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../../lib/api'
import { localizedName } from '../../lib/utils'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'

// Purely a display threshold — the backend's own match/no-match cutoff
// already decided whether to answer at all. This just distinguishes a
// confident match from one that barely cleared the bar, so a borderline
// answer doesn't look as certain as a strong one.
const STRONG_MATCH_THRESHOLD = 70

/**
 * Template-matching FAQ search, not a chatbot. Every answer is one of the
 * existing, hand-written FAQ entries (or an honest fallback) returned by
 * POST /faq/match, which embeds the query locally and does a nearest-
 * neighbor lookup against the FAQ list — no generation, no LLM call.
 * Labeled and worded throughout as "FAQ assistant"/search, deliberately
 * never as "AI chat", to match what it actually does.
 */
export function FaqAssistant() {
  const { t, i18n } = useTranslation()
  const [query, setQuery] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    const trimmed = query.trim()
    if (!trimmed) return
    setLoading(true)
    setError(null)
    try {
      const data = await api.matchFaq(trimmed)
      setResult(data)
    } catch (err) {
      setError(err.message)
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="p-6">
      <div className="flex items-center gap-2">
        <span className="flex size-9 items-center justify-center rounded-xl bg-brand-100 text-brand-700">
          <Search className="size-4" aria-hidden="true" />
        </span>
        <h2 className="text-base font-bold text-ink-900">{t('faq.assistantTitle')}</h2>
      </div>
      <p className="mt-2 text-xs text-ink-400">{t('faq.assistantDisclaimer')}</p>

      <form onSubmit={handleSubmit} className="mt-4 flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t('faq.assistantPlaceholder')}
          className="min-h-11 w-full rounded-xl border border-ink-200 bg-white px-4 text-sm shadow-soft-sm focus:border-brand-400 focus:outline-none"
        />
        <Button type="submit" icon={Send} loading={loading} disabled={!query.trim()}>
          {t('faq.assistantAsk')}
        </Button>
      </form>

      {error && <p className="mt-3 text-sm font-medium text-danger">{error}</p>}

      {result && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="mt-4 rounded-xl border border-ink-100 bg-ink-50 p-4"
        >
          {result.matched ? (
            <>
              <div className="flex items-center justify-between gap-2">
                <p className="text-[11px] font-bold uppercase tracking-wide text-ink-400">
                  {t('faq.assistantClosestMatch')}
                </p>
                <Badge tone={result.similarity_percent >= STRONG_MATCH_THRESHOLD ? 'brand' : 'amber'}>
                  {result.similarity_percent >= STRONG_MATCH_THRESHOLD
                    ? t('faq.assistantStrongMatch')
                    : t('faq.assistantPossibleMatch')}
                </Badge>
              </div>
              <p className="mt-1 text-sm font-bold text-ink-900">
                {localizedName(result.faq.question, result.faq.question_hi, i18n.language)}
              </p>
              <p className="mt-1.5 text-sm text-ink-600">
                {localizedName(result.faq.answer, result.faq.answer_hi, i18n.language)}
              </p>
            </>
          ) : (
            <p className="text-sm text-ink-500">{t('faq.assistantFallback')}</p>
          )}
        </motion.div>
      )}
    </Card>
  )
}
