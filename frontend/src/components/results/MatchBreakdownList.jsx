import { AnimatePresence, motion } from 'framer-motion'
import { AlertTriangle, ChevronDown, Scale } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { DIMENSION_ICON } from '../../lib/resultHelpers'
import { cn, FIT_COLOR } from '../../lib/utils'
import { Card } from '../ui/Card'

function BreakdownRow({ item, t }) {
  const Icon = DIMENSION_ICON[item.dimension] ?? DIMENSION_ICON.category_fit
  return (
    <div className="flex items-start gap-3 py-3.5">
      <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-ink-100 text-ink-500">
        <Icon className="size-4.5" aria-hidden="true" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-sm font-bold text-ink-900">
            {t(`results.dimension.${item.dimension}`, { defaultValue: item.dimension })}
          </p>
          <span className={cn('rounded-pill px-2 py-0.5 text-[11px] font-bold', FIT_COLOR[item.fit])}>
            {t(`results.fit.${item.fit}`)}
          </span>
        </div>
        <p className="mt-1 text-xs text-ink-500">{item.commodity_property}</p>
        <p className="text-xs text-ink-500">{item.packaging_property}</p>
        <p className="mt-1.5 text-sm text-ink-700">{item.explanation}</p>
      </div>
    </div>
  )
}

export function MatchBreakdownList({ recommendation, regulatoryNote, defaultOpen = false }) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(defaultOpen)
  const warnings = recommendation.warnings ?? []

  return (
    <Card>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full cursor-pointer items-center justify-between p-6 text-left"
      >
        <div>
          <h3 className="text-base font-bold text-ink-900">{t('results.why')}</h3>
          <p className="mt-0.5 text-xs text-ink-500">
            {t('results.fullBreakdown', { n: recommendation.match_breakdown.length })}
          </p>
        </div>
        <ChevronDown className={cn('size-5 shrink-0 text-ink-400 transition-transform', open && 'rotate-180')} aria-hidden="true" />
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="px-6 pb-6">
              {warnings.length > 0 && (
                <div className="mb-2 rounded-xl border border-amber-200 bg-amber-50 p-4">
                  <div className="flex items-center gap-2 text-sm font-bold text-amber-800">
                    <AlertTriangle className="size-4 shrink-0" aria-hidden="true" />
                    {t('results.thingsToKnow')}
                  </div>
                  <ul className="mt-2 space-y-1.5">
                    {warnings.map((w, i) => (
                      <li key={i} className="text-sm text-amber-800/90 leading-relaxed">
                        • {w}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="divide-y divide-ink-100">
                {recommendation.match_breakdown.map((item) => (
                  <BreakdownRow key={item.dimension} item={item} t={t} />
                ))}
              </div>

              {regulatoryNote && (
                <div className="mt-4 flex items-start gap-2.5 rounded-xl border border-ink-200 bg-ink-50 p-4">
                  <Scale className="mt-0.5 size-4 shrink-0 text-ink-400" aria-hidden="true" />
                  <p className="text-xs leading-relaxed text-ink-500">{regulatoryNote}</p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  )
}
