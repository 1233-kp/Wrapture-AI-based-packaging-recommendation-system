import { motion } from 'framer-motion'
import { Check, ExternalLink, Link2, ShieldCheck } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { ReportQrCode } from '../components/results/ReportQrCode'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { EmptyState } from '../components/ui/EmptyState'
import { FullPageSpinner } from '../components/ui/Spinner'
import { useReports } from '../hooks/useReports'
import { formatDate } from '../lib/utils'

function VerifyLinkRow({ reportId }) {
  const { t } = useTranslation()
  const [copied, setCopied] = useState(false)
  const url = `${window.location.origin}/verify/${reportId}`

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // clipboard access denied — the "Open" link below still works
    }
  }

  return (
    <div className="mt-3 flex items-center gap-2">
      <button
        onClick={handleCopy}
        className="flex min-h-9 cursor-pointer items-center gap-1.5 rounded-lg border border-ink-200 px-3 text-xs font-semibold text-ink-600 hover:bg-ink-50"
      >
        {copied ? <Check className="size-3.5 text-brand-600" /> : <Link2 className="size-3.5" />}
        {copied ? t('traceability.copied') : t('traceability.copyLink')}
      </button>
      <a
        href={`/verify/${reportId}`}
        target="_blank"
        rel="noreferrer"
        className="flex min-h-9 cursor-pointer items-center gap-1.5 rounded-lg border border-ink-200 px-3 text-xs font-semibold text-ink-600 hover:bg-ink-50"
      >
        <ExternalLink className="size-3.5" />
        {t('traceability.openVerification')}
      </a>
    </div>
  )
}

/**
 * Protected — lists the caller's own saved reports with each one's QR/verify
 * link, reusing GET /reports (existing, RLS-scoped) and the existing
 * /reports/{id}/qrcode + /reports/{id}/public public endpoints. No new
 * backend logic.
 */
export default function TraceabilityPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { reports, loading, error } = useReports({ limit: 100 })

  useEffect(() => {
    document.title = t('traceability.pageTitle')
  }, [t])

  if (loading) return <FullPageSpinner label={t('traceability.loading')} />

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6 sm:py-12 lg:px-8">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-display text-2xl font-extrabold text-ink-900 sm:text-3xl">
          {t('traceability.heading')}
        </h1>
        <p className="mt-1 text-sm text-ink-500">{t('traceability.subhead')}</p>
      </motion.div>

      <div className="mt-5 flex gap-3 rounded-xl border border-brand-200 bg-brand-50 p-4">
        <ShieldCheck className="size-5 shrink-0 text-brand-600" aria-hidden="true" />
        <p className="text-sm text-brand-800">{t('traceability.explainer')}</p>
      </div>

      {error && <p className="mt-4 text-sm font-medium text-danger">{error}</p>}

      {reports.length === 0 ? (
        <div className="mt-8">
          <EmptyState
            icon={Link2}
            title={t('traceability.emptyTitle')}
            description={t('traceability.emptyDescription')}
            action={<Button onClick={() => navigate('/app/recommend')}>{t('common.newRecommendation')}</Button>}
          />
        </div>
      ) : (
        <div className="mt-6 space-y-4">
          {reports.map((report, i) => (
            <motion.div
              key={report.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: Math.min(i * 0.04, 0.4) }}
            >
              <Card className="p-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate font-bold text-ink-900">{report.commodity_name}</p>
                    <p className="mt-0.5 text-xs text-ink-400">{formatDate(report.created_at)}</p>
                  </div>
                </div>
                <div className="mt-3">
                  <ReportQrCode reportId={report.id} />
                </div>
                <VerifyLinkRow reportId={report.id} />
              </Card>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
