import { motion } from 'framer-motion'
import { AlertCircle, Droplets, Wind } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Badge } from '../components/ui/Badge'
import { Card } from '../components/ui/Card'
import { FullPageSpinner } from '../components/ui/Spinner'
import { api } from '../lib/api'
import { localizedName, titleCase } from '../lib/utils'

const COST_TONE = { low: 'brand', medium: 'amber', high: 'danger' }

/**
 * Public, no-login reference page — same 13 packaging_materials.json records
 * already used by the recommender and reports, just browsable directly via
 * GET /materials. Not behind ProtectedRoute, but still rendered inside
 * AppShell (see App.jsx) so it shares the sidebar/header with the rest of
 * the app instead of the marketing layout.
 */
export default function PackagingLibraryPage() {
  const { t, i18n } = useTranslation()
  const [materials, setMaterials] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    document.title = t('library.pageTitle')
    api
      .materials()
      .then((data) => setMaterials(data.materials))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [t])

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-12 lg:px-8">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-display text-2xl font-extrabold text-ink-900 sm:text-3xl">
          {t('library.heading')}
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-ink-500">{t('library.subhead')}</p>
      </motion.div>

      {loading && <FullPageSpinner label={t('library.loading')} />}

      {!loading && error && (
        <div className="mt-8 flex items-center gap-2 rounded-xl border border-danger-bg bg-danger-bg px-4 py-3 text-sm text-danger">
          <AlertCircle className="size-4 shrink-0" aria-hidden="true" />
          {error}
        </div>
      )}

      {!loading && !error && (
        <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {materials.map((m, i) => (
            <motion.div
              key={m.id}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, delay: Math.min(i * 0.04, 0.4) }}
            >
              <Card className="flex h-full flex-col p-5">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="text-sm font-extrabold text-ink-900">
                      {localizedName(m.name, m.name_hi, i18n.language)}
                    </h3>
                    <p className="mt-0.5 text-[11px] uppercase tracking-wide text-ink-400">
                      {titleCase(m.category)}
                    </p>
                  </div>
                  <Badge tone={COST_TONE[m.cost_tier]}>{t(`results.costTierValue.${m.cost_tier}`)}</Badge>
                </div>

                <div className="mt-4 space-y-2 text-xs text-ink-600">
                  {m.otr_cm3_m2_day_atm && (
                    <div className="flex items-center gap-1.5">
                      <Wind className="size-3.5 shrink-0 text-teal-600" aria-hidden="true" />
                      <span className="font-semibold text-ink-700">OTR</span> {m.otr_cm3_m2_day_atm.min}-
                      {m.otr_cm3_m2_day_atm.max}
                    </div>
                  )}
                  {m.wvtr_g_m2_day && (
                    <div className="flex items-center gap-1.5">
                      <Droplets className="size-3.5 shrink-0 text-brand-600" aria-hidden="true" />
                      <span className="font-semibold text-ink-700">WVTR</span> {m.wvtr_g_m2_day.min}-
                      {m.wvtr_g_m2_day.max}
                    </div>
                  )}
                </div>

                <p className="mt-3 text-xs text-ink-500">{m.recyclability_rating}</p>

                <div className="mt-3 flex flex-1 flex-wrap items-end gap-1.5">
                  {m.typical_use_cases.map((use) => (
                    <span
                      key={use}
                      className="rounded-pill bg-ink-100 px-2 py-0.5 text-[10px] font-medium text-ink-600"
                    >
                      {use}
                    </span>
                  ))}
                </div>
              </Card>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
