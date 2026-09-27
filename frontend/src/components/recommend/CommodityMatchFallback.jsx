import { AnimatePresence, motion } from 'framer-motion'
import { AlertTriangle, CheckCircle2, HelpCircle, Search } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../../lib/api'
import { localizedName } from '../../lib/utils'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'
import { Spinner } from '../ui/Spinner'

/**
 * "Can't find your commodity?" fallback — sits alongside the normal dropdown,
 * never replaces it. Embeds the user's free-text description locally
 * (sentence-transformers, no external API) and shows the closest existing
 * commodities so the tool stays usable for anything not in our 30-item
 * database, instead of just leaving the user stuck.
 */
export function CommodityMatchFallback({ onSelect }) {
  const { t, i18n } = useTranslation()
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [selectedId, setSelectedId] = useState(null)

  const handleSearch = async () => {
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await api.matchCommodity(query.trim())
      setResult(data)
    } catch (err) {
      setError(err.message || t('recommend.matchError'))
    } finally {
      setLoading(false)
    }
  }

  const handlePick = (match) => {
    setSelectedId(match.commodity_id)
    onSelect({
      commodityId: match.commodity_id,
      commodityName: match.commodity_name,
      query: result.query,
      lowConfidence: result.low_confidence_match,
    })
  }

  return (
    <div className="mt-2.5">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="inline-flex cursor-pointer items-center gap-1.5 text-xs font-semibold text-ink-500 hover:text-brand-700"
      >
        <HelpCircle className="size-3.5" aria-hidden="true" />
        {t('recommend.cantFindCommodity')}
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="mt-3 rounded-xl border border-dashed border-ink-200 p-4">
              <p className="text-xs text-ink-500">{t('recommend.describeHelp')}</p>
              {/* A <form> here would nest inside RecommendPage's own <form>, which is invalid
                  HTML — the native 'submit' event bubbles up and fires the outer form's submit
                  handler too. Plain div + explicit button/Enter-key handling instead. */}
              <div className="mt-3 flex gap-2">
                <div className="relative flex-1">
                  <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-ink-400" aria-hidden="true" />
                  <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        handleSearch()
                      }
                    }}
                    placeholder={t('recommend.describePlaceholder')}
                    className="min-h-10 w-full rounded-lg border border-ink-200 py-2 pl-9 pr-3 text-sm focus:border-brand-400 focus:outline-none"
                  />
                </div>
                <Button type="button" size="sm" loading={loading} disabled={!query.trim()} onClick={handleSearch}>
                  {t('recommend.findMatches')}
                </Button>
              </div>

              {error && <p className="mt-2 text-xs font-medium text-danger">{error}</p>}

              {loading && (
                <div className="mt-4 flex items-center justify-center py-4">
                  <Spinner size="size-5" />
                </div>
              )}

              {result && !loading && (
                <div className="mt-4">
                  {result.low_confidence_match && (
                    <div className="mb-3 flex items-start gap-2 rounded-lg border border-amber-300 bg-amber-50 px-3 py-2.5">
                      <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-600" aria-hidden="true" />
                      <p className="text-xs text-amber-800">{t('recommend.lowConfidenceWarning')}</p>
                    </div>
                  )}

                  <div className="space-y-2">
                    {result.matches.map((match) => {
                      const isSelected = selectedId === match.commodity_id
                      const cardIsLow = result.low_confidence_match
                      return (
                        <Card
                          key={match.commodity_id}
                          as="button"
                          type="button"
                          hover
                          onClick={() => handlePick(match)}
                          className={`w-full cursor-pointer p-3.5 text-left ${
                            isSelected
                              ? 'border-brand-500 ring-2 ring-brand-200'
                              : cardIsLow
                                ? 'border-amber-300'
                                : 'border-ink-200'
                          }`}
                        >
                          <div className="flex items-center justify-between gap-3">
                            <div className="min-w-0">
                              <p className="flex items-center gap-1.5 text-sm font-bold text-ink-900">
                                {localizedName(match.commodity_name, match.commodity_name_hi, i18n.language)}
                                {isSelected && <CheckCircle2 className="size-4 text-brand-600" aria-hidden="true" />}
                              </p>
                              <p className="text-xs text-ink-400">
                                {t(`results.category.${match.category}`, { defaultValue: match.category })}
                              </p>
                            </div>
                            <span
                              className={`shrink-0 rounded-pill px-2.5 py-1 text-xs font-bold ${
                                cardIsLow ? 'bg-amber-100 text-amber-700' : 'bg-brand-100 text-brand-700'
                              }`}
                            >
                              {t('recommend.percentMatch', { percent: match.similarity_percent.toFixed(0) })}
                            </span>
                          </div>
                          <p className="mt-2 text-xs text-ink-500">{t('recommend.propertiesEstimatedFrom')}</p>
                        </Card>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
