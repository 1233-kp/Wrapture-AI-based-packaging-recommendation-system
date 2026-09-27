import { motion } from 'framer-motion'
import { Wind } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Card, CardBody, CardHeader } from '../ui/Card'

function GasBar({ label, range, color, delay, t }) {
  const mid = ((range.min + range.max) / 2).toFixed(1)
  return (
    <div>
      <div className="flex items-center justify-between text-sm">
        <span className="font-semibold text-ink-800">{label}</span>
        <span className="font-bold text-ink-900">
          {range.min}-{range.max}%
        </span>
      </div>
      <div className="relative mt-1.5 h-3 w-full overflow-hidden rounded-pill bg-ink-100">
        <motion.div
          className={`absolute inset-y-0 left-0 rounded-pill ${color}`}
          initial={{ width: 0 }}
          whileInView={{ width: `${range.max}%` }}
          viewport={{ once: true }}
          transition={{ duration: 0.9, delay, ease: 'easeOut' }}
        />
        <motion.div
          className="absolute inset-y-0 rounded-pill bg-black/10"
          initial={{ width: 0 }}
          whileInView={{ width: `${range.min}%` }}
          viewport={{ once: true }}
          transition={{ duration: 0.9, delay, ease: 'easeOut' }}
        />
      </div>
      <p className="mt-1 text-[11px] text-ink-400">{t('results.midpoint', { mid })}</p>
    </div>
  )
}

export function MapGasCard({ guidance }) {
  const { t } = useTranslation()
  if (!guidance?.applicable) return null

  const GASES = [
    { key: 'o2_percent', label: t('results.gas.o2'), color: 'bg-teal-500' },
    { key: 'co2_percent', label: t('results.gas.co2'), color: 'bg-amber-500' },
    { key: 'n2_percent', label: t('results.gas.n2'), color: 'bg-brand-500' },
  ]

  return (
    <Card className="border-teal-200 bg-teal-50/40">
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <div className="flex size-9 items-center justify-center rounded-lg bg-teal-100 text-teal-700">
            <Wind className="size-4.5" aria-hidden="true" />
          </div>
          <div>
            <h3 className="text-base font-bold text-ink-900">{t('results.mapHeading')}</h3>
            <p className="text-xs text-ink-500">
              {t('results.respirationClass', {
                value: t(`results.respirationClassWord.${guidance.respiration_rate_class}`, {
                  defaultValue: guidance.respiration_rate_class,
                }),
              })}
            </p>
          </div>
        </div>
      </CardHeader>
      <CardBody className="space-y-4">
        {GASES.map((g, i) => (
          <GasBar key={g.key} label={g.label} range={guidance[g.key]} color={g.color} delay={i * 0.12} t={t} />
        ))}
      </CardBody>
    </Card>
  )
}
