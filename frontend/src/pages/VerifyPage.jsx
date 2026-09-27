import { motion } from 'framer-motion'
import { AlertCircle, BadgeCheck, Calendar, Layers, Leaf, Package, ShieldCheck, Wind } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useParams } from 'react-router-dom'
import { BrandMark } from '../components/ui/BrandMark'
import { LanguageToggle } from '../components/ui/LanguageToggle'
import { api } from '../lib/api'
import { formatDateTime } from '../lib/utils'

function SpecRow({ icon: Icon, label, value }) {
  if (value == null) return null
  return (
    <div className="flex items-center justify-between border-b border-ink-100 py-3 last:border-0">
      <span className="flex items-center gap-2 text-sm text-ink-500">
        <Icon className="size-4 text-ink-400" aria-hidden="true" />
        {label}
      </span>
      <span className="text-sm font-semibold text-ink-900">{value}</span>
    </div>
  )
}

function formatRange(range, unit) {
  if (!range) return null
  return `${range.min}-${range.max} ${unit}`
}

/**
 * Public, no-login verification page — reached by scanning the QR code on a
 * printed report or exported PDF. Deliberately plain and trustworthy-looking,
 * not styled like the marketing landing page: this is meant to be read by an
 * auditor or supply-chain partner in a few seconds, not sold to.
 */
export default function VerifyPage() {
  const { t } = useTranslation()
  const { reportId } = useParams()
  const [view, setView] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    document.title = t('verify.pageTitle')
    api
      .publicReport(reportId)
      .then(setView)
      .catch((err) => setError(err.status === 404 ? 'not_found' : err.message))
      .finally(() => setLoading(false))
  }, [reportId, t])

  return (
    <div className="flex min-h-screen items-center justify-center bg-ink-50 px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-4 flex items-center justify-center">
          <LanguageToggle />
        </div>
        <div className="mb-6 flex items-center justify-center gap-2">
          <BrandMark size="size-8" />
          <span className="font-display text-base font-bold text-ink-900">{t('common.brand')}</span>
        </div>

        {loading && (
          <div className="rounded-2xl border border-ink-200 bg-white p-10 text-center shadow-soft-md">
            <p className="text-sm text-ink-400">{t('verify.loading')}</p>
          </div>
        )}

        {!loading && error === 'not_found' && (
          <div className="rounded-2xl border border-ink-200 bg-white p-10 text-center shadow-soft-md">
            <AlertCircle className="mx-auto size-8 text-ink-300" aria-hidden="true" />
            <h1 className="mt-3 text-lg font-bold text-ink-900">{t('verify.notFoundTitle')}</h1>
            <p className="mt-1.5 text-sm text-ink-500">{t('verify.notFoundDescription')}</p>
          </div>
        )}

        {!loading && error && error !== 'not_found' && (
          <div className="rounded-2xl border border-ink-200 bg-white p-10 text-center shadow-soft-md">
            <AlertCircle className="mx-auto size-8 text-danger" aria-hidden="true" />
            <h1 className="mt-3 text-lg font-bold text-ink-900">{t('verify.errorTitle')}</h1>
            <p className="mt-1.5 text-sm text-ink-500">{error}</p>
          </div>
        )}

        {!loading && view && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="overflow-hidden rounded-2xl border border-ink-200 bg-white shadow-soft-lg"
          >
            <div className="flex items-center gap-3 border-b border-ink-100 bg-brand-50 px-6 py-4">
              <ShieldCheck className="size-6 shrink-0 text-brand-600" aria-hidden="true" />
              <div>
                <p className="text-sm font-bold text-brand-800">{t('verify.banner')}</p>
                <p className="text-xs text-brand-700/80">{t('verify.traceId', { id: view.trace_id })}</p>
              </div>
            </div>

            <div className="px-6 py-5">
              <p className="text-xs font-semibold uppercase tracking-wide text-ink-400">{t('verify.commodity')}</p>
              <h1 className="mt-1 font-display text-2xl font-extrabold text-ink-900">{view.commodity_name}</h1>

              <div className="mt-3 flex items-center gap-2 rounded-xl bg-ink-50 px-3.5 py-2.5">
                <BadgeCheck className="size-4 shrink-0 text-brand-600" aria-hidden="true" />
                <span className="text-sm font-semibold text-ink-800">{view.material_name}</span>
              </div>

              <div className="mt-5">
                <SpecRow icon={Wind} label={t('verify.otr')} value={formatRange(view.otr_cm3_m2_day_atm, 'cm³/m²/day')} />
                <SpecRow icon={Layers} label={t('verify.wvtr')} value={formatRange(view.wvtr_g_m2_day, 'g/m²/day')} />
                <SpecRow icon={Package} label={t('verify.thickness')} value={formatRange(view.thickness_range_micron, 'µm')} />
                <SpecRow icon={Leaf} label={t('verify.sustainabilityScore')} value={`${Math.round(view.sustainability_score)}/100`} />
                <SpecRow icon={Calendar} label={t('verify.generated')} value={formatDateTime(view.generated_at)} />
              </div>
            </div>

            <div className="border-t border-ink-100 bg-ink-50 px-6 py-3 text-center text-[11px] text-ink-400">
              {t('verify.footerDisclaimer')}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  )
}
