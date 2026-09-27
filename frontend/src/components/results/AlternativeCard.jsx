import { motion } from 'framer-motion'
import { ArrowRight, Info, Scale } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { localizedName } from '../../lib/utils'
import { Badge } from '../ui/Badge'
import { Card, CardBody, CardHeader } from '../ui/Card'

/**
 * Comparison-card layout informed by 21st.dev's "Pricing Cards" pattern
 * (prebuiltui, id 7262 — free/pro/enterprise 3-column comparison; code wasn't
 * retrievable this session, quota hit after 2 fetches) — built directly
 * against our tokens using the same "one option per card, key stats + a
 * headline delta" structure, adapted for trade-off text instead of feature
 * checklists.
 */
export function AlternativeCard({ recommendation, rank }) {
  const { t, i18n } = useTranslation()
  const materialName = localizedName(recommendation.material_name, recommendation.material_name_hi, i18n.language)

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-40px' }}
      transition={{ duration: 0.4, delay: rank * 0.08 }}
    >
      <Card hover className="h-full">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <Badge tone="neutral">{t('results.optionNumber', { n: rank + 2 })}</Badge>
            <span className="text-xs font-bold text-ink-400">{recommendation.score}/100</span>
          </div>
          <h4 className="mt-3 text-lg font-bold text-ink-900">{materialName}</h4>
        </CardHeader>
        <CardBody>
          <div className="flex flex-wrap items-center gap-4 text-sm">
            <div>
              <p className="text-[11px] font-medium text-ink-400">{t('results.cost')}</p>
              <p className="font-bold text-ink-800">
                {t(`results.costTierValue.${recommendation.cost_tier}`, { defaultValue: recommendation.cost_tier })}
              </p>
            </div>
            <div className="h-8 w-px bg-ink-100" />
            <div>
              <p className="text-[11px] font-medium text-ink-400">{t('results.sustainability')}</p>
              <p className="font-bold text-ink-800">{Math.round(recommendation.sustainability_score)}/100</p>
            </div>
            <div className="h-8 w-px bg-ink-100" />
            <div>
              <p className="text-[11px] font-medium text-ink-400">{t('results.shelfLife')}</p>
              <p className="font-bold text-ink-800">
                {recommendation.estimated_shelf_life_days != null
                  ? t('results.shelfLifeShort', { n: recommendation.estimated_shelf_life_days.toFixed(0) })
                  : t('common.na')}
              </p>
            </div>
            {recommendation.estimated_cost_per_unit_inr && (
              <>
                <div className="h-8 w-px bg-ink-100" />
                <div>
                  <p className="inline-flex items-center gap-1 text-[11px] font-medium text-ink-400">
                    {t('results.estCost')}
                    <Info className="size-3 text-ink-300" aria-hidden="true" title={t('results.estCostHint')} />
                  </p>
                  <p className="font-bold text-ink-800">
                    ~₹{recommendation.estimated_cost_per_unit_inr.min}-{recommendation.estimated_cost_per_unit_inr.max}/kg
                  </p>
                </div>
              </>
            )}
          </div>

          <div className="mt-4 flex items-start gap-2 rounded-lg bg-ink-50 px-3 py-2.5">
            <ArrowRight className="mt-0.5 size-3.5 shrink-0 text-teal-600" aria-hidden="true" />
            <p className="text-sm text-ink-700">{recommendation.trade_off_summary}</p>
          </div>

          {/* Lighter than the top pick's full ComplianceNotesSection — just a count
              flag, omitted entirely when there are no notes (the common case). */}
          {recommendation.compliance_notes?.length > 0 && (
            <div className="mt-2.5 flex items-center gap-1.5 text-xs font-medium text-amber-700">
              <Scale className="size-3.5 shrink-0" aria-hidden="true" />
              {t('results.complianceCountShort', { count: recommendation.compliance_notes.length })}
            </div>
          )}
        </CardBody>
      </Card>
    </motion.div>
  )
}
