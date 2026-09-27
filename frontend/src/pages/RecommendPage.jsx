import { AnimatePresence, motion } from 'framer-motion'
import { AlertCircle, ChevronDown, DollarSign, Recycle, Sparkles } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { CommodityMatchFallback } from '../components/recommend/CommodityMatchFallback'
import { CommoditySearchInput } from '../components/recommend/CommoditySearchInput'
import { StorageTypeCards } from '../components/recommend/StorageTypeCards'
import { TransportDistanceEstimator } from '../components/recommend/TransportDistanceEstimator'
import { TransportDuration } from '../components/recommend/TransportDuration'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { SegmentedControl } from '../components/ui/SegmentedControl'
import { Toggle } from '../components/ui/Toggle'
import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'

export default function RecommendPage() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const { accessToken } = useAuth()

  const BUDGET_OPTIONS = [
    { value: 'economy', label: t('recommend.budgetEconomy') },
    { value: 'standard', label: t('recommend.budgetStandard') },
    { value: 'premium', label: t('recommend.budgetPremium') },
  ]

  const [commodities, setCommodities] = useState([])
  const [loadingCommodities, setLoadingCommodities] = useState(true)
  const [commodityId, setCommodityId] = useState('')
  const [matchedFrom, setMatchedFrom] = useState(null)
  const [temperature, setTemperature] = useState(25)
  const [transportDays, setTransportDays] = useState(3)
  const [budgetTier, setBudgetTier] = useState('standard')
  const [prioritizeSustainability, setPrioritizeSustainability] = useState(false)
  const [advancedOpen, setAdvancedOpen] = useState(false)
  const [preciseTemp, setPreciseTemp] = useState('')
  const [preciseDays, setPreciseDays] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    document.title = t('recommend.pageTitle')
    api
      .commodities()
      .then((data) => setCommodities(data.commodities))
      .catch(() => setError(t('recommend.loadError')))
      .finally(() => setLoadingCommodities(false))
  }, [t])

  const selectedCommodity = commodities.find((c) => c.id === commodityId)

  const effectiveTemp = preciseTemp !== '' ? Number(preciseTemp) : temperature
  const effectiveDays = preciseDays !== '' ? Number(preciseDays) : transportDays

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!commodityId) {
      setError(t('recommend.pickCommodityFirst'))
      return
    }
    setError(null)
    setSubmitting(true)
    try {
      const payload = {
        commodity_id: commodityId,
        budget_tier: budgetTier,
        prioritize_sustainability: prioritizeSustainability,
        expected_transport_days: effectiveDays,
        ambient_temperature_c: effectiveTemp,
        lang: i18n.language,
      }
      const result = await api.recommendDetailed(payload)
      sessionStorage.setItem(
        'psa_last_result',
        JSON.stringify({
          result,
          input_conditions: payload,
          commodity_name: result.commodity.name,
          matched_from: matchedFrom,
        })
      )
      navigate('/app/results')
    } catch (err) {
      setError(err.message || t('recommend.genericError'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 sm:py-12 lg:px-8">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
        <h1 className="font-display text-2xl font-extrabold text-ink-900 sm:text-3xl">
          {t('recommend.heading')}
        </h1>
        <p className="mt-1.5 text-sm text-ink-500">{t('recommend.subhead')}</p>
      </motion.div>

      <form onSubmit={handleSubmit} className="mt-8">
        <Card className="p-6 sm:p-8">
          <div className="space-y-7">
            <div>
              <CommoditySearchInput
                commodities={commodities}
                value={commodityId}
                onChange={(id) => {
                  setCommodityId(id)
                  setMatchedFrom(null) // a direct dropdown pick supersedes any prior fallback match
                }}
                loading={loadingCommodities}
              />
              {matchedFrom ? (
                <div className="mt-2.5">
                  <Badge tone="amber">
                    {t('recommend.matchedFrom', {
                      query: matchedFrom.query,
                      confidence: matchedFrom.lowConfidence
                        ? t('recommend.roughEstimate')
                        : t('recommend.similarCommodity'),
                    })}
                  </Badge>
                </div>
              ) : (
                selectedCommodity && (
                  <div className="mt-2.5">
                    <Badge tone={selectedCommodity.confidence === 'high' ? 'brand' : 'amber'}>
                      {t(`results.confidence.${selectedCommodity.confidence}`, { defaultValue: t('recommend.estimatedCommodityData') })}{' '}
                      {t('recommend.commodityDataSuffix')}
                    </Badge>
                  </div>
                )
              )}
              <CommodityMatchFallback
                onSelect={({ commodityId: id, commodityName, query, lowConfidence }) => {
                  setCommodityId(id)
                  setMatchedFrom({ commodityName, query, lowConfidence })
                }}
              />
            </div>

            <StorageTypeCards value={temperature} onChange={setTemperature} />

            <TransportDuration value={transportDays} onChange={setTransportDays} />
            <TransportDistanceEstimator
              onApply={(days) => {
                setTransportDays(days)
                // Applying an estimate should actually take effect — an exact
                // manual override in Advanced mode would otherwise silently
                // keep winning over it in effectiveDays.
                setPreciseDays('')
              }}
            />

            <div>
              <label className="mb-2 block text-sm font-semibold text-ink-800">{t('recommend.budgetTier')}</label>
              <SegmentedControl
                name="budget-tier"
                options={BUDGET_OPTIONS}
                value={budgetTier}
                onChange={setBudgetTier}
              />
            </div>

            <div className="rounded-xl border border-ink-100 bg-ink-50 p-4">
              <Toggle
                id="prioritize-sustainability"
                checked={prioritizeSustainability}
                onChange={setPrioritizeSustainability}
                label={t('recommend.prioritizeSustainability')}
                description={t('recommend.prioritizeSustainabilityDesc')}
              />
            </div>

            <div>
              <button
                type="button"
                onClick={() => setAdvancedOpen((v) => !v)}
                className="flex w-full cursor-pointer items-center justify-between text-sm font-semibold text-ink-700"
              >
                <span>{t('recommend.advancedMode')}</span>
                <ChevronDown className={`size-4 transition-transform ${advancedOpen ? 'rotate-180' : ''}`} aria-hidden="true" />
              </button>
              <AnimatePresence initial={false}>
                {advancedOpen && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.25 }}
                    className="overflow-hidden"
                  >
                    <div className="mt-4 grid grid-cols-1 gap-4 rounded-xl border border-dashed border-ink-200 p-4 sm:grid-cols-2">
                      <div>
                        <label htmlFor="precise-temp" className="mb-1.5 block text-xs font-semibold text-ink-600">
                          {t('recommend.exactTemp')}
                        </label>
                        <input
                          id="precise-temp"
                          type="number"
                          placeholder={`${temperature} (${t('recommend.storageLabel')})`}
                          value={preciseTemp}
                          onChange={(e) => setPreciseTemp(e.target.value)}
                          className="w-full rounded-lg border border-ink-200 px-3 py-2 text-sm focus:border-brand-400 focus:outline-none"
                        />
                      </div>
                      <div>
                        <label htmlFor="precise-days" className="mb-1.5 block text-xs font-semibold text-ink-600">
                          {t('recommend.exactDays')}
                        </label>
                        <input
                          id="precise-days"
                          type="number"
                          step="0.5"
                          placeholder={`${transportDays}`}
                          value={preciseDays}
                          onChange={(e) => setPreciseDays(e.target.value)}
                          className="w-full rounded-lg border border-ink-200 px-3 py-2 text-sm focus:border-brand-400 focus:outline-none"
                        />
                      </div>
                      <p className="sm:col-span-2 text-xs text-ink-400">{t('recommend.advancedHelp')}</p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </Card>

        {error && (
          <div className="mt-4 flex items-center gap-2 rounded-xl bg-danger-bg px-4 py-3 text-sm font-medium text-danger">
            <AlertCircle className="size-4 shrink-0" aria-hidden="true" />
            {error}
          </div>
        )}

        <div className="mt-6 flex justify-end">
          <Button type="submit" size="lg" icon={Sparkles} loading={submitting} disabled={!commodityId}>
            {submitting ? t('recommend.analyzing') : t('recommend.getRecommendation')}
          </Button>
        </div>
      </form>

      <div className="mt-6 flex flex-wrap gap-4 text-xs text-ink-400">
        <span className="flex items-center gap-1">
          <DollarSign className="size-3.5" aria-hidden="true" /> {t('recommend.costAwareRanking')}
        </span>
        <span className="flex items-center gap-1">
          <Recycle className="size-3.5" aria-hidden="true" /> {t('recommend.sustainabilityScored')}
        </span>
      </div>
    </div>
  )
}
