import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { CountUp } from '../ui/CountUp'

// Real counts, pulled from the actual dataset — not placeholder figures. See
// backend/data/commodities.json (80), packaging_materials.json (13), the 8
// dimensions scored in engine/recommender.py's _score_material, and the 4
// condition inputs DetailedRecommendRequest accepts (budget_tier,
// prioritize_sustainability, expected_transport_days, ambient_temperature_c).
export function StatsStrip() {
  const { t } = useTranslation()

  const STATS = [
    { value: 80, suffix: '+', label: t('landing.stats.commodities') },
    { value: 13, suffix: '', label: t('landing.stats.materials') },
    { value: 8, suffix: '', label: t('landing.stats.dimensions') },
    { value: 4, suffix: '', label: t('landing.stats.conditions') },
  ]

  return (
    <section className="border-y border-ink-200 bg-white py-5">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-40px' }}
        transition={{ duration: 0.4 }}
        className="mx-auto flex max-w-5xl flex-wrap items-center justify-center gap-x-10 gap-y-3 px-4 sm:px-6 lg:px-8"
      >
        {STATS.map((stat) => (
          <div key={stat.label} className="flex items-baseline gap-1.5">
            <span className="font-display text-lg font-extrabold text-brand-700 sm:text-xl">
              <CountUp value={stat.value} suffix={stat.suffix} />
            </span>
            <span className="text-xs font-medium text-ink-500 sm:text-sm">{stat.label}</span>
          </div>
        ))}
      </motion.div>
    </section>
  )
}
