import { motion } from 'framer-motion'
import { Download, Loader2, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { api } from '../../lib/api'
import { formatDate, localizedName } from '../../lib/utils'
import { Badge } from '../ui/Badge'
import { Card } from '../ui/Card'

export function ReportCard({ report, index = 0, onDelete }) {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const { accessToken } = useAuth()
  const [downloading, setDownloading] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [confirmingDelete, setConfirmingDelete] = useState(false)

  const top = report.recommendation?.recommendations?.[0]

  const handleView = () => {
    navigate('/app/results', {
      state: {
        result: report.recommendation,
        input_conditions: report.input_conditions,
        commodity_name: report.commodity_name,
        // Lets ResultsPage know this is an already-saved report, so it
        // doesn't try to auto-save a duplicate just from viewing it.
        report_id: report.id,
        feedback_outcome: report.feedback_outcome ?? null,
      },
    })
  }

  const handleDownload = async (e) => {
    e.stopPropagation()
    setDownloading(true)
    try {
      await api.downloadReportPdf(accessToken, report.id, `wrapture-${report.commodity_name}.pdf`)
    } catch {
      // surfaced visually via disabled state reverting; keep it simple here
    } finally {
      setDownloading(false)
    }
  }

  const handleDeleteClick = (e) => {
    e.stopPropagation()
    if (!confirmingDelete) {
      setConfirmingDelete(true)
      return
    }
    doDelete()
  }

  const doDelete = async () => {
    setDeleting(true)
    try {
      await onDelete(report.id)
    } catch {
      setDeleting(false)
      setConfirmingDelete(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.96 }}
      transition={{ duration: 0.35, delay: index * 0.04 }}
    >
      {/* as="div" with role/tabIndex/onKeyDown, not as="button" — the card
          contains real <button> elements (download, delete), and a <button>
          cannot validly contain another <button>. */}
      <Card
        hover
        as="div"
        role="button"
        tabIndex={0}
        onClick={handleView}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            handleView()
          }
        }}
        className="w-full cursor-pointer p-5 text-left"
      >
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="truncate font-bold text-ink-900">{report.commodity_name}</p>
            <p className="mt-0.5 text-xs text-ink-400">{formatDate(report.created_at)}</p>
          </div>
          <div className="flex shrink-0 items-center gap-1">
            <button
              onClick={handleDownload}
              disabled={downloading}
              aria-label={t('dashboard.downloadPdf')}
              className="flex size-9 cursor-pointer items-center justify-center rounded-lg text-ink-400 hover:bg-brand-50 hover:text-brand-700"
            >
              {downloading ? <Loader2 className="size-4 animate-spin" /> : <Download className="size-4" />}
            </button>
            {onDelete && (
              <button
                onClick={handleDeleteClick}
                onBlur={() => setConfirmingDelete(false)}
                disabled={deleting}
                aria-label={confirmingDelete ? t('dashboard.confirmDeleteReport') : t('dashboard.deleteReport')}
                className={`flex h-9 shrink-0 cursor-pointer items-center justify-center rounded-lg px-2 text-xs font-semibold transition-colors ${
                  confirmingDelete
                    ? 'bg-danger-bg text-danger'
                    : 'text-ink-400 hover:bg-danger-bg hover:text-danger'
                }`}
              >
                {deleting ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : confirmingDelete ? (
                  t('common.confirm')
                ) : (
                  <Trash2 className="size-4" />
                )}
              </button>
            )}
          </div>
        </div>

        {top && (
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <Badge tone="brand">{localizedName(top.material_name, top.material_name_hi, i18n.language)}</Badge>
            <Badge tone="neutral">{top.score}/100</Badge>
          </div>
        )}
      </Card>
    </motion.div>
  )
}
