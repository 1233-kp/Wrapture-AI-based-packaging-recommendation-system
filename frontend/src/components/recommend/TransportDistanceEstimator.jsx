import { AnimatePresence, motion } from 'framer-motion'
import { AlertTriangle, ChevronDown, Info, MapPin, Route } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from '../../lib/api'
import { Button } from '../ui/Button'
import { Spinner } from '../ui/Spinner'

/**
 * "Estimate from locations" — sits alongside the existing manual transport-
 * days slider, never replaces it. Calls POST /logistics/estimate-transport-days
 * (live Nominatim geocoding with an offline major-Indian-cities fallback,
 * haversine straight-line distance) and offers to fill the existing field —
 * the user still has to click "Use this estimate", nothing is auto-applied.
 */
export function TransportDistanceEstimator({ onApply }) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const [source, setSource] = useState('')
  const [destination, setDestination] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [applied, setApplied] = useState(false)

  const handleCalculate = async () => {
    if (!source.trim() || !destination.trim()) {
      setError({ message: t('recommend.fillBothLocations'), suggestions: null })
      return
    }
    setLoading(true)
    setError(null)
    setResult(null)
    setApplied(false)
    try {
      const data = await api.estimateTransportDays(source.trim(), destination.trim())
      setResult(data)
    } catch (err) {
      const detail = err.data?.detail
      if (detail?.suggestions) {
        setError({
          message: t('recommend.locationNotFoundTitle'),
          unresolvedLocation: detail.unresolved_location,
          suggestions: detail.suggestions,
        })
      } else {
        setError({ message: err.message || t('recommend.estimateError'), suggestions: null })
      }
    } finally {
      setLoading(false)
    }
  }

  const handleSuggestionClick = (city) => {
    // Fill whichever field actually failed to resolve, so the user isn't
    // stuck guessing which of the two inputs was the problem.
    if (error?.unresolvedLocation && error.unresolvedLocation.trim().toLowerCase() === source.trim().toLowerCase()) {
      setSource(city)
    } else {
      setDestination(city)
    }
  }

  const handleApply = () => {
    if (!result) return
    onApply(result.estimated_transport_days)
    setApplied(true)
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="inline-flex cursor-pointer items-center gap-1.5 text-xs font-semibold text-ink-500 hover:text-brand-700"
      >
        <Route className="size-3.5" aria-hidden="true" />
        {t('recommend.estimateFromLocations')}
        <ChevronDown className={`size-3.5 transition-transform ${open ? 'rotate-180' : ''}`} aria-hidden="true" />
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
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label htmlFor="transport-source" className="mb-1.5 block text-xs font-semibold text-ink-600">
                    {t('recommend.sourceLocation')}
                  </label>
                  <input
                    id="transport-source"
                    value={source}
                    onChange={(e) => setSource(e.target.value)}
                    placeholder={t('recommend.sourcePlaceholder')}
                    className="min-h-10 w-full rounded-lg border border-ink-200 px-3 text-sm focus:border-brand-400 focus:outline-none"
                  />
                </div>
                <div>
                  <label htmlFor="transport-destination" className="mb-1.5 block text-xs font-semibold text-ink-600">
                    {t('recommend.destinationLocation')}
                  </label>
                  <input
                    id="transport-destination"
                    value={destination}
                    onChange={(e) => setDestination(e.target.value)}
                    placeholder={t('recommend.destinationPlaceholder')}
                    className="min-h-10 w-full rounded-lg border border-ink-200 px-3 text-sm focus:border-brand-400 focus:outline-none"
                  />
                </div>
              </div>

              <div className="mt-3">
                <Button type="button" size="sm" loading={loading} onClick={handleCalculate}>
                  {loading ? t('recommend.calculating') : t('recommend.calculate')}
                </Button>
              </div>

              {loading && (
                <div className="mt-4 flex items-center justify-center py-2">
                  <Spinner size="size-5" />
                </div>
              )}

              {error && !loading && (
                <div className="mt-3 rounded-lg border border-amber-300 bg-amber-50 px-3 py-2.5">
                  <p className="flex items-center gap-1.5 text-xs font-semibold text-amber-800">
                    <AlertTriangle className="size-3.5 shrink-0" aria-hidden="true" />
                    {error.message}
                  </p>
                  {error.suggestions && (
                    <>
                      <p className="mt-1.5 text-xs text-amber-800/80">{t('recommend.tryOneOfThese')}</p>
                      <div className="mt-1.5 flex flex-wrap gap-1.5">
                        {error.suggestions.map((city) => (
                          <button
                            key={city}
                            type="button"
                            onClick={() => handleSuggestionClick(city)}
                            className="rounded-pill border border-amber-300 bg-white px-2.5 py-1 text-xs font-semibold text-amber-800 transition-colors hover:bg-amber-100 cursor-pointer"
                          >
                            {city}
                          </button>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              )}

              {result && !loading && (
                <div className="mt-3 rounded-lg border border-brand-200 bg-brand-50 px-3.5 py-3">
                  <p className="flex items-center gap-1.5 text-sm font-bold text-brand-800">
                    <MapPin className="size-4 shrink-0" aria-hidden="true" />
                    {t('recommend.distanceResult', {
                      distance: result.distance_km,
                      days: result.estimated_transport_days,
                    })}
                  </p>
                  <p className="mt-1.5 text-xs leading-relaxed text-brand-700/80">{result.disclaimer}</p>
                  {result.source_used === 'offline_fallback' && (
                    <p className="mt-1.5 flex items-center gap-1.5 text-xs font-medium text-ink-500">
                      <Info className="size-3.5 shrink-0" aria-hidden="true" />
                      {t('recommend.offlineDataNote')}
                    </p>
                  )}
                  <div className="mt-3">
                    <Button type="button" size="sm" variant="secondary" onClick={handleApply}>
                      {t('recommend.useThisEstimate')}
                    </Button>
                    {applied && <span className="ml-2.5 text-xs font-semibold text-brand-700">{t('recommend.estimateApplied')}</span>}
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
