import { motion } from 'framer-motion'
import { Award, Calendar, IndianRupee, Info, PiggyBank, Recycle, Sparkles, Thermometer } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { localizedName } from '../../lib/utils'
import { Badge } from '../ui/Badge'
import { CircularProgress } from '../ui/CircularProgress'

function StatChip({ icon: Icon, label, value, hint }) {
  return (
    <div className="flex items-center gap-2.5 rounded-xl border border-ink-100 bg-ink-50 px-3.5 py-2.5">
      <Icon className="size-4 text-brand-600 shrink-0" aria-hidden="true" />
      <div className="min-w-0">
        <p className="inline-flex items-center gap-1 text-[11px] font-medium text-ink-400 leading-none">
          {label}
          {hint && <Info className="size-3 text-ink-300" aria-hidden="true" title={hint} />}
        </p>
        <p className="truncate text-sm font-bold text-ink-900 mt-0.5">{value}</p>
      </div>
    </div>
  )
}

export function TopRecommendationCard({ recommendation, commodity, matchedFrom, mlAgreement, shelfLifePrediction }) {
  const { t, i18n } = useTranslation()
  const materialName = localizedName(recommendation.material_name, recommendation.material_name_hi, i18n.language)
  const commodityName = localizedName(commodity.name, commodity.name_hi, i18n.language)

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="relative overflow-hidden rounded-card border border-brand-200 bg-gradient-to-br from-brand-50 via-white to-teal-50 p-6 shadow-soft-xl sm:p-8"
    >
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone="brand" icon={Award}>
          {t('results.topRecommendation')}
        </Badge>
        {matchedFrom ? (
          // Reuses the same Badge used for the normal per-field confidence flag, just with a
          // different message: this uncertainty comes from the free-text commodity-matching
          // fallback (borrowed properties from a similar-but-different commodity), which is
          // meaningfully less certain than the database's own "estimated" confidence levels.
          <Badge tone="amber">{t('results.estimatedFromSimilar', { name: matchedFrom.commodityName })}</Badge>
        ) : (
          recommendation.overall_confidence !== 'high' && (
            <Badge tone="amber">{t(`results.confidence.${recommendation.overall_confidence}`)}</Badge>
          )
        )}
      </div>

      <div className="mt-4 flex flex-col gap-6 sm:flex-row sm:items-center">
        <CircularProgress
          value={recommendation.sustainability_score}
          size={116}
          strokeWidth={9}
          sublabel={t('results.sustainability')}
        />

        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-ink-400">
            {t('results.for', { commodity: commodityName })}
          </p>
          <h2 className="mt-1 font-display text-2xl font-extrabold text-ink-900 sm:text-3xl">
            {materialName}
          </h2>
          <div className="mt-2 flex items-center gap-2">
            <div className="h-2 flex-1 max-w-[180px] overflow-hidden rounded-pill bg-ink-200">
              <motion.div
                className="h-full rounded-pill bg-brand-600"
                initial={{ width: 0 }}
                animate={{ width: `${recommendation.score}%` }}
                transition={{ duration: 0.9, delay: 0.2, ease: 'easeOut' }}
              />
            </div>
            <span className="text-sm font-bold text-brand-700">
              {t('results.fitSuffix', { score: recommendation.score })}
            </span>
          </div>
          {recommendation.ml_confidence_score != null && (
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-1.5 text-sm font-bold text-teal-700">
                <Sparkles className="size-4" aria-hidden="true" />
                {t('results.mlConfidence', { score: Math.round(recommendation.ml_confidence_score) })}
              </span>
              {mlAgreement && (
                <Badge tone={mlAgreement.agrees ? 'brand' : 'amber'}>
                  {mlAgreement.agrees ? t('results.mlAgrees') : t('results.mlDisagrees')}
                </Badge>
              )}
            </div>
          )}
          <p className="mt-3 text-sm font-medium text-ink-600">{recommendation.trade_off_summary}</p>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatChip
          icon={PiggyBank}
          label={t('results.costTier')}
          value={t(`results.costTierValue.${recommendation.cost_tier}`, { defaultValue: recommendation.cost_tier })}
        />
        <StatChip
          icon={Calendar}
          label={t('results.estShelfLife')}
          value={
            recommendation.estimated_shelf_life_days != null
              ? t('results.estShelfLifeValue', { n: recommendation.estimated_shelf_life_days.toFixed(1) })
              : t('common.na')
          }
        />
        <StatChip
          icon={Recycle}
          label={t('results.recyclability')}
          value={recommendation.recyclability_rating.split(',')[0].split('(')[0].trim()}
        />
        {shelfLifePrediction && (
          <StatChip
            icon={Thermometer}
            label={t('results.predictedShelfLife')}
            hint={`${shelfLifePrediction.explanation} ${shelfLifePrediction.disclaimer}`}
            value={t('results.estShelfLifeValue', { n: shelfLifePrediction.predicted_shelf_life_days })}
          />
        )}
        {recommendation.estimated_cost_per_unit_inr && (
          <StatChip
            icon={IndianRupee}
            label={t('results.estCost')}
            hint={t('results.estCostHint')}
            value={`~₹${recommendation.estimated_cost_per_unit_inr.min}-${recommendation.estimated_cost_per_unit_inr.max}/kg`}
          />
        )}
      </div>
    </motion.div>
  )
}
