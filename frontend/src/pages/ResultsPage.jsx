import { AnimatePresence, motion } from 'framer-motion'
import { CheckCircle2, Download, History, Loader2, RefreshCw } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useLocation, useNavigate } from 'react-router-dom'
import { AlternativeCard } from '../components/results/AlternativeCard'
import { ColdChainPanel } from '../components/results/ColdChainPanel'
import { ComplianceNotesSection } from '../components/results/ComplianceNotesSection'
import { MapGasCard } from '../components/results/MapGasCard'
import { MatchBreakdownList } from '../components/results/MatchBreakdownList'
import { RadarComparison } from '../components/results/RadarComparison'
import { ReportFeedback } from '../components/results/ReportFeedback'
import { ReportQrCode } from '../components/results/ReportQrCode'
import { TopRecommendationCard } from '../components/results/TopRecommendationCard'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { EmptyState } from '../components/ui/EmptyState'
import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import { localizedName } from '../lib/utils'

export default function ResultsPage() {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const { accessToken } = useAuth()

  const [payload, setPayload] = useState(location.state ?? null)
  // Seeded from payload.report_id when we arrived here via "view" on an
  // already-saved report (see ReportCard.jsx) — that path must never
  // re-trigger a save, only a freshly-generated recommendation should.
  const [savedReportId, setSavedReportId] = useState(location.state?.report_id ?? null)
  const [autoSaving, setAutoSaving] = useState(false)
  const [showSavedToast, setShowSavedToast] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [actionError, setActionError] = useState(null)
  const autoSaveAttempted = useRef(!!location.state?.report_id)

  useEffect(() => {
    document.title = t('results.pageTitle')
    if (!payload) {
      const stored = sessionStorage.getItem('psa_last_result')
      if (stored) {
        const parsed = JSON.parse(stored)
        setPayload(parsed)
        if (parsed.report_id) {
          setSavedReportId(parsed.report_id)
          autoSaveAttempted.current = true
        }
      }
    }
  }, [payload, t])

  const result = payload?.result
  const recommendations = result?.recommendations ?? []
  const top = recommendations[0]
  const alternatives = recommendations.slice(1, 3)

  // Auto-save: fires once per freshly-generated recommendation, for a logged-in
  // user only. Never fires for a report reached via "view" (report_id already
  // set above) or before /recommend/detailed has actually produced a result —
  // commodity search, dropdown autocomplete, and /commodities/match calls never
  // reach this page at all, so they can't trigger a save either.
  useEffect(() => {
    if (!result || !accessToken || autoSaveAttempted.current) return
    autoSaveAttempted.current = true

    let cancelled = false
    setAutoSaving(true)
    api
      .saveReport(accessToken, {
        commodity_name: result.commodity.name,
        input_conditions: payload.input_conditions ?? {},
        recommendation: result,
      })
      .then((report) => {
        if (cancelled) return
        setSavedReportId(report.id)
        setShowSavedToast(true)
        setTimeout(() => setShowSavedToast(false), 4000)
        // Persist the id so a remount (e.g. browser back to this same result)
        // sees it's already saved instead of attempting a duplicate.
        const stored = sessionStorage.getItem('psa_last_result')
        if (stored) {
          try {
            sessionStorage.setItem('psa_last_result', JSON.stringify({ ...JSON.parse(stored), report_id: report.id }))
          } catch {
            // non-fatal — worst case a back-navigation re-saves once more
          }
        }
      })
      .catch((err) => {
        if (!cancelled) setActionError(err.message || t('results.autoSaveError'))
      })
      .finally(() => {
        if (!cancelled) setAutoSaving(false)
      })

    return () => {
      cancelled = true
    }
  }, [result, accessToken, payload, t])

  const handleDownload = async () => {
    setDownloading(true)
    setActionError(null)
    try {
      if (!savedReportId) {
        setActionError(t('results.stillSaving'))
        return
      }
      await api.downloadReportPdf(accessToken, savedReportId, `wrapture-${result.commodity.id}.pdf`)
    } catch (err) {
      setActionError(err.message || t('results.exportError'))
    } finally {
      setDownloading(false)
    }
  }

  if (!result) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16">
        <EmptyState
          title={t('results.emptyTitle')}
          description={t('results.emptyDescription')}
          action={<Button onClick={() => navigate('/app/recommend')}>{t('common.newRecommendation')}</Button>}
        />
      </div>
    )
  }

  const commodityName = localizedName(result.commodity.name, result.commodity.name_hi, i18n.language)

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 sm:py-12 lg:px-8">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-wrap items-center justify-between gap-4"
      >
        <div>
          <Badge tone="neutral">
            {t(`results.category.${result.commodity.category}`, { defaultValue: result.commodity.category })}
          </Badge>
          <h1 className="mt-2 font-display text-2xl font-extrabold text-ink-900 sm:text-3xl">
            {t('results.heading', { commodity: commodityName })}
          </h1>
        </div>
        <Button variant="secondary" icon={RefreshCw} onClick={() => navigate('/app/recommend')}>
          {t('common.newRecommendation')}
        </Button>
      </motion.div>

      <div className="mt-6 flex flex-wrap items-start gap-4">
        <div className="flex flex-wrap items-center gap-3">
          {savedReportId ? (
            <Button variant="secondary" icon={History} onClick={() => navigate('/app/history')}>
              {t('results.viewInHistory')}
            </Button>
          ) : autoSaving ? (
            <span className="flex items-center gap-2 rounded-xl border border-ink-200 bg-ink-50 px-4 py-2.5 text-sm font-medium text-ink-500">
              <Loader2 className="size-4 animate-spin" aria-hidden="true" />
              {t('results.savingToHistory')}
            </span>
          ) : accessToken ? (
            <span className="rounded-xl border border-ink-200 bg-ink-50 px-4 py-2.5 text-sm font-medium text-ink-500">
              {t('results.notSavedYet')}
            </span>
          ) : (
            <span className="rounded-xl border border-ink-200 bg-ink-50 px-4 py-2.5 text-sm font-medium text-ink-500">
              {t('results.signInToSave')}
            </span>
          )}
          <Button variant="teal" icon={Download} loading={downloading} onClick={handleDownload}>
            {t('results.downloadPdf')}
          </Button>
        </div>
        <ReportQrCode reportId={savedReportId} />

        <AnimatePresence>
          {showSavedToast && (
            <motion.div
              initial={{ opacity: 0, y: -6, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -6, scale: 0.96 }}
              transition={{ duration: 0.25 }}
              className="flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white shadow-soft-md"
            >
              <CheckCircle2 className="size-4" aria-hidden="true" />
              {t('results.savedToast')}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      {actionError && <p className="mt-2 text-sm font-medium text-danger">{actionError}</p>}

      <div className="mt-8 space-y-8">
        {top && (
          <TopRecommendationCard
            recommendation={top}
            commodity={result.commodity}
            matchedFrom={payload?.matched_from}
            mlAgreement={result.ml_agreement}
            shelfLifePrediction={result.shelf_life_prediction}
          />
        )}

        {top && (
          <MatchBreakdownList recommendation={top} regulatoryNote={result.regulatory_note} defaultOpen />
        )}

        {top && (
          <ComplianceNotesSection notes={top.compliance_notes} disclaimer={result.compliance_disclaimer} />
        )}

        {alternatives.length > 0 && (
          <div>
            <h3 className="mb-4 text-base font-bold text-ink-900">{t('results.alternativeOptions')}</h3>
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
              {alternatives.map((rec, i) => (
                <AlternativeCard key={rec.material_id} recommendation={rec} rank={i} />
              ))}
            </div>
          </div>
        )}

        {recommendations.length > 1 && <RadarComparison recommendations={recommendations} />}

        <MapGasCard guidance={result.map_gas_guidance} />

        {savedReportId && (
          <div className="space-y-6">
            <ReportFeedback reportId={savedReportId} initialOutcome={payload?.feedback_outcome ?? null} />
            <ColdChainPanel reportId={savedReportId} />
          </div>
        )}

        <p className="text-center text-xs text-ink-400">{result.disclaimer}</p>
      </div>
    </div>
  )
}
