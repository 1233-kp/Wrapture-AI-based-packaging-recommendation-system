import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { useTranslation } from 'react-i18next'
import { Card, CardDescription, CardHeader, CardTitle } from '../ui/Card'

function ChartTooltip({ active, payload, label, t }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border border-ink-200 bg-white px-3 py-2 shadow-soft-md">
      <p className="text-xs font-bold text-ink-900">{label}</p>
      <p className="text-xs text-brand-700">{t('dashboard.reportCount', { count: payload[0].value })}</p>
    </div>
  )
}

export function ActivityChart({ data }) {
  const { t } = useTranslation()
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('dashboard.reportsOverTime')}</CardTitle>
        <CardDescription>{t('dashboard.reportsPerWeek')}</CardDescription>
      </CardHeader>
      <div className="h-64 px-2 pb-6">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
            <defs>
              <linearGradient id="activityFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--color-brand-500)" stopOpacity={0.35} />
                <stop offset="100%" stopColor="var(--color-brand-500)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-ink-200)" vertical={false} />
            <XAxis dataKey="label" tick={{ fill: 'var(--color-ink-400)', fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis allowDecimals={false} tick={{ fill: 'var(--color-ink-400)', fontSize: 11 }} axisLine={false} tickLine={false} width={28} />
            <Tooltip content={<ChartTooltip t={t} />} />
            <Area
              type="monotone"
              dataKey="count"
              stroke="var(--color-brand-600)"
              strokeWidth={2.5}
              fill="url(#activityFill)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}
