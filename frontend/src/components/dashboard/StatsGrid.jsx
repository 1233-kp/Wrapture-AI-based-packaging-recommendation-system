import { motion } from 'framer-motion'
import { Calendar, FileText, Leaf, Tags } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { CountUp } from '../ui/CountUp'
import { Card } from '../ui/Card'

/**
 * KPI-card grid pattern informed by 21st.dev's "Advanced Stats" (uilayout.contact,
 * id 19070 — KPI cards + animated chart + scroll-triggered reveal; code wasn't
 * retrievable this session, quota hit after 2 fetches). Built directly against
 * our tokens: staggered whileInView reveal + CountUp per card.
 */
function StatCard({ icon: Icon, label, value, suffix, decimals = 0, isText = false, delay = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
    >
      <Card className="p-5">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-xl bg-brand-100 text-brand-700">
            <Icon className="size-5" aria-hidden="true" />
          </div>
          <p className="text-xs font-semibold text-ink-500">{label}</p>
        </div>
        <p className="mt-3 font-display text-2xl font-extrabold text-ink-900">
          {isText ? value : <CountUp value={value} suffix={suffix} decimals={decimals} />}
        </p>
      </Card>
    </motion.div>
  )
}

export function StatsGrid({ totalReports, topCategory, avgSustainability, memberSince }) {
  const { t } = useTranslation()
  const topCategoryLabel = topCategory
    ? t(`results.category.${topCategory}`, { defaultValue: topCategory })
    : '—'

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <StatCard icon={FileText} label={t('dashboard.totalReports')} value={totalReports} delay={0} />
      <StatCard icon={Tags} label={t('dashboard.topCategory')} value={topCategoryLabel} isText delay={0.06} />
      <StatCard
        icon={Leaf}
        label={t('dashboard.avgSustainability')}
        value={avgSustainability}
        suffix="/100"
        decimals={0}
        delay={0.12}
      />
      <StatCard icon={Calendar} label={t('dashboard.memberSince')} value={memberSince} isText delay={0.18} />
    </div>
  )
}
