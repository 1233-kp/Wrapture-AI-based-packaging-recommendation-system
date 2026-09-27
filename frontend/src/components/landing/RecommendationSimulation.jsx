import { motion } from 'framer-motion'
import { ArrowRight, Cpu, Droplets, Leaf, ShieldCheck, Thermometer, Timer, Wind } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Badge } from '../ui/Badge'
import { Card } from '../ui/Card'
import { CircularProgress } from '../ui/CircularProgress'

// This walkthrough is a real, one-time capture of recommend_detailed('mango',
// budget_tier='standard', expected_transport_days=5, ambient_temperature_c=30)
// against the live backend — not a live call from this page, and not invented
// numbers. Re-running the same inputs against the current model/rules may
// shift these slightly as the dataset evolves; that's expected and fine for
// an illustrative example.
const INPUT = {
  commodity: 'Mango',
  moisture: '78-84% moisture',
  respiration: 'High respiration rate',
  transport: '5 days transport',
  ambient: '30°C ambient storage',
}

const OUTPUT = {
  material: 'Vented PET Clamshell',
  score: 92.7,
  sustainability: 100,
  otr: '~19,000 cm³/m²/day/atm',
  wvtr: '~42.5 g/m²/day',
  shelfLifeDays: 4.4,
  shelfLifeTypical: 6.5,
}

export function RecommendationSimulation() {
  const { t } = useTranslation()

  return (
    <section className="py-20 sm:py-28">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-2xl text-center"
        >
          <h2 className="font-display text-3xl font-extrabold text-ink-900 sm:text-4xl">
            {t('landing.simulation.heading')}
          </h2>
          <p className="mt-3 text-ink-500">{t('landing.simulation.subhead')}</p>
          <Badge tone="amber" className="mt-4">
            {t('landing.simulation.illustrativeBadge')}
          </Badge>
        </motion.div>

        <div className="mt-14 grid grid-cols-1 items-center gap-4 lg:grid-cols-[1fr_auto_1fr]">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.5 }}
          >
            <Card className="p-6">
              <p className="text-xs font-bold uppercase tracking-wide text-ink-400">
                {t('landing.simulation.inputLabel')}
              </p>
              <p className="mt-1 font-display text-xl font-extrabold text-ink-900">{INPUT.commodity}</p>
              <div className="mt-4 space-y-2.5 text-sm text-ink-600">
                <div className="flex items-center gap-2">
                  <Droplets className="size-4 shrink-0 text-brand-600" aria-hidden="true" />
                  {INPUT.moisture}
                </div>
                <div className="flex items-center gap-2">
                  <Wind className="size-4 shrink-0 text-teal-600" aria-hidden="true" />
                  {INPUT.respiration}
                </div>
                <div className="flex items-center gap-2">
                  <Timer className="size-4 shrink-0 text-amber-600" aria-hidden="true" />
                  {INPUT.transport}
                </div>
                <div className="flex items-center gap-2">
                  <Thermometer className="size-4 shrink-0 text-danger" aria-hidden="true" />
                  {INPUT.ambient}
                </div>
              </div>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.4, delay: 0.2 }}
            className="flex flex-row items-center justify-center gap-2 lg:flex-col"
          >
            <ArrowRight className="size-4 text-ink-300 lg:hidden" aria-hidden="true" />
            <span className="flex size-14 flex-col items-center justify-center gap-0.5 rounded-full bg-white shadow-soft-md">
              <Cpu className="size-5 text-teal-600" aria-hidden="true" />
              <span className="text-[8px] font-bold uppercase tracking-wide text-ink-400">
                {t('landing.simulation.aiAnalysis')}
              </span>
            </span>
            <ArrowRight className="hidden size-4 text-ink-300 lg:block" aria-hidden="true" />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.5, delay: 0.15 }}
          >
            <Card className="p-6">
              <div className="flex items-center justify-between">
                <p className="text-xs font-bold uppercase tracking-wide text-ink-400">
                  {t('landing.simulation.outputLabel')}
                </p>
                <span className="inline-flex items-center gap-1 text-xs font-bold text-brand-700">
                  <ShieldCheck className="size-3.5" aria-hidden="true" />
                  {t('landing.simulation.fitScore', { score: OUTPUT.score })}
                </span>
              </div>
              <p className="mt-1 font-display text-xl font-extrabold text-ink-900">{OUTPUT.material}</p>

              <div className="mt-4 flex items-center gap-4">
                <CircularProgress value={OUTPUT.sustainability} size={64} strokeWidth={5} />
                <div className="min-w-0 space-y-1 text-xs text-ink-500">
                  <div className="flex items-center gap-1.5">
                    <Wind className="size-3.5 shrink-0 text-teal-600" aria-hidden="true" />
                    <span className="font-semibold text-ink-700">OTR</span> {OUTPUT.otr}
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Droplets className="size-3.5 shrink-0 text-brand-600" aria-hidden="true" />
                    <span className="font-semibold text-ink-700">WVTR</span> {OUTPUT.wvtr}
                  </div>
                </div>
              </div>

              <div className="mt-4 flex items-center gap-2 rounded-lg bg-ink-50 px-3 py-2.5 text-xs text-ink-600">
                <Leaf className="size-4 shrink-0 text-brand-600" aria-hidden="true" />
                {t('landing.simulation.shelfLifeNote', {
                  days: OUTPUT.shelfLifeDays,
                  typical: OUTPUT.shelfLifeTypical,
                })}
              </div>
            </Card>
          </motion.div>
        </div>

        <p className="mt-6 text-center text-xs text-ink-400">{t('landing.simulation.footnote')}</p>
      </div>
    </section>
  )
}
