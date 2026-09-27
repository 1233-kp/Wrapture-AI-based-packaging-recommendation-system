import { motion } from 'framer-motion'
import { QrCode } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { api } from '../../lib/api'
import { Card } from '../ui/Card'

/**
 * Shown right after a report is saved — lets judges/reviewers scan it live
 * during a demo instead of needing to open the PDF. Same QR the PDF export
 * embeds (both call GET /reports/{id}/qrcode, generated on-demand server-side).
 */
export function ReportQrCode({ reportId }) {
  const { t } = useTranslation()
  if (!reportId) return null

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="flex items-center gap-4 p-4">
        <img
          src={api.qrCodeUrl(reportId)}
          alt={t('results.qrAlt')}
          className="size-20 shrink-0 rounded-lg border border-ink-100"
        />
        <div className="min-w-0">
          <p className="flex items-center gap-1.5 text-sm font-bold text-ink-900">
            <QrCode className="size-4 text-brand-600" aria-hidden="true" />
            {t('results.scanToVerify')}
          </p>
          <p className="mt-1 text-xs text-ink-500">{t('results.qrDescription')}</p>
        </div>
      </Card>
    </motion.div>
  )
}
