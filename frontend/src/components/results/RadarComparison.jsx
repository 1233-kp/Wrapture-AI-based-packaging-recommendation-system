import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import {
  Legend,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'
import { buildRadarData, RADAR_COLORS } from '../../lib/resultHelpers'
import { localizedName } from '../../lib/utils'
import { Card, CardDescription, CardHeader, CardTitle } from '../ui/Card'

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border border-ink-200 bg-white px-3 py-2 shadow-soft-md">
      <p className="text-xs font-bold text-ink-900">{label}</p>
      {payload.map((p) => (
        <p key={p.name} className="text-xs" style={{ color: p.color }}>
          {p.name}: <span className="font-bold">{p.value}</span>
        </p>
      ))}
    </div>
  )
}

export function RadarComparison({ recommendations }) {
  const { t, i18n } = useTranslation()
  const localized = recommendations.map((rec) => ({
    ...rec,
    material_name: localizedName(rec.material_name, rec.material_name_hi, i18n.language),
  }))
  const data = buildRadarData(localized, t)

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('results.comparisonTitle')}</CardTitle>
        <CardDescription>
          {t('results.comparisonDescription', { n: recommendations.length })}
        </CardDescription>
      </CardHeader>
      <motion.div
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true, margin: '-40px' }}
        transition={{ duration: 0.6 }}
        className="h-80 px-2 pb-6 sm:h-96"
      >
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data} outerRadius="70%">
            <PolarGrid stroke="var(--color-ink-200)" />
            <PolarAngleAxis dataKey="axis" tick={{ fill: 'var(--color-ink-600)', fontSize: 12 }} />
            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: 'var(--color-ink-400)', fontSize: 10 }} />
            {localized.map((rec, i) => (
              <Radar
                key={rec.material_id}
                name={rec.material_name}
                dataKey={rec.material_name}
                stroke={RADAR_COLORS[i % RADAR_COLORS.length]}
                fill={RADAR_COLORS[i % RADAR_COLORS.length]}
                fillOpacity={i === 0 ? 0.35 : 0.15}
                strokeWidth={2}
              />
            ))}
            <Tooltip content={<ChartTooltip />} />
            <Legend wrapperStyle={{ fontSize: 12, paddingTop: 12 }} />
          </RadarChart>
        </ResponsiveContainer>
      </motion.div>
    </Card>
  )
}
