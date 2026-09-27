import { motion } from 'framer-motion'
import { Leaf, Recycle } from 'lucide-react'
import { useEffect, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { CircularProgress } from '../components/ui/CircularProgress'
import { CountUp } from '../components/ui/CountUp'
import { EmptyState } from '../components/ui/EmptyState'
import { FullPageSpinner } from '../components/ui/Spinner'
import { useReports } from '../hooks/useReports'
import { computeRecyclabilityBreakdown, computeStats } from '../lib/dashboardHelpers'

/**
 * Protected — aggregates fields already stored on the caller's own saved
 * reports (top pick's sustainability_score, already computed by the
 * recommender at save time). No new server-side computation.
 */
export default function SustainabilityPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { reports, loading, error } = useReports({ limit: 100 })

  useEffect(() => {
    document.title = t('sustainability.pageTitle')
  }, [t])

  const { avgSustainability } = useMemo(() => computeStats(reports, null), [reports])
  const { widelyRecyclable, lowerRecyclability } = useMemo(
    () => computeRecyclabilityBreakdown(reports),
    [reports]
  )

  if (loading) return <FullPageSpinner label={t('sustainability.loading')} />

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 sm:py-12 lg:px-8">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-display text-2xl font-extrabold text-ink-900 sm:text-3xl">
          {t('sustainability.heading')}
        </h1>
        <p className="mt-1 text-sm text-ink-500">{t('sustainability.subhead')}</p>
      </motion.div>

      {error && <p className="mt-4 text-sm font-medium text-danger">{error}</p>}

      {reports.length === 0 ? (
        <div className="mt-8">
          <EmptyState
            icon={Recycle}
            title={t('sustainability.emptyTitle')}
            description={t('sustainability.emptyDescription')}
            action={<Button onClick={() => navigate('/app/recommend')}>{t('common.newRecommendation')}</Button>}
          />
        </div>
      ) : (
        <>
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 }}
            className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2"
          >
            <Card className="flex items-center gap-5 p-6">
              <CircularProgress value={avgSustainability} size={88} strokeWidth={8} />
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-ink-400">
                  {t('sustainability.avgScore')}
                </p>
                <p className="mt-1 text-sm text-ink-500">
                  {t('sustainability.acrossReports', { count: reports.length })}
                </p>
              </div>
            </Card>

            <Card className="p-6">
              <p className="text-xs font-semibold uppercase tracking-wide text-ink-400">
                {t('sustainability.breakdown')}
              </p>
              <div className="mt-3 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5 text-sm text-ink-700">
                    <span className="size-2.5 shrink-0 rounded-full bg-brand-500" />
                    {t('sustainability.widelyRecyclable')}
                  </span>
                  <span className="font-display text-lg font-extrabold text-ink-900">
                    <CountUp value={widelyRecyclable} />
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5 text-sm text-ink-700">
                    <span className="size-2.5 shrink-0 rounded-full bg-ink-300" />
                    {t('sustainability.lowerRecyclability')}
                  </span>
                  <span className="font-display text-lg font-extrabold text-ink-900">
                    <CountUp value={lowerRecyclability} />
                  </span>
                </div>
              </div>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mt-6"
          >
            <Card className="flex gap-3 p-6">
              <Leaf className="size-5 shrink-0 text-brand-600" aria-hidden="true" />
              <div>
                <p className="text-sm font-bold text-ink-900">{t('sustainability.explainerTitle')}</p>
                <p className="mt-1.5 text-sm text-ink-500">{t('sustainability.explainerBody')}</p>
              </div>
            </Card>
          </motion.div>
        </>
      )}
    </div>
  )
}
