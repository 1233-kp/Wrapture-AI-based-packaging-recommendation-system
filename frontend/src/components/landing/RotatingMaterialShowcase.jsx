import { AnimatePresence, motion } from 'framer-motion'
import { Leaf, Recycle, ShieldCheck } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { CircularProgress } from '../ui/CircularProgress'

export function RotatingMaterialShowcase() {
  const { t } = useTranslation()
  const [index, setIndex] = useState(0)

  const DEMO_MATERIALS = [
    { name: 'HDPE', commodity: t('landing.showcase.commodity1'), score: 91, sustainability: 100, tag: t('landing.showcase.tag1') },
    { name: 'Vented PET Clamshell', commodity: t('landing.showcase.commodity2'), score: 96, sustainability: 100, tag: t('landing.showcase.tag2') },
    { name: 'EVOH Film', commodity: t('landing.showcase.commodity3'), score: 89, sustainability: 20, tag: t('landing.showcase.tag3') },
    { name: 'Glass Jar', commodity: t('landing.showcase.commodity4'), score: 93, sustainability: 100, tag: t('landing.showcase.tag4') },
  ]

  useEffect(() => {
    const id = setInterval(() => setIndex((i) => (i + 1) % DEMO_MATERIALS.length), 2800)
    return () => clearInterval(id)
  }, [DEMO_MATERIALS.length])

  const current = DEMO_MATERIALS[index]

  return (
    <div className="relative mx-auto w-full max-w-sm">
      <motion.div
        animate={{ y: [0, -10, 0] }}
        transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
        className="relative rounded-card border border-white/60 bg-white/90 p-6 shadow-soft-xl backdrop-blur-sm"
      >
        <div className="flex items-center justify-between">
          <span className="inline-flex items-center gap-1.5 rounded-pill bg-brand-100 px-2.5 py-1 text-xs font-bold text-brand-700">
            <Leaf className="size-3" aria-hidden="true" />
            {t('landing.showcase.topRecommendation')}
          </span>
          <span className="text-xs font-medium text-ink-400">{t('landing.showcase.for', { commodity: current.commodity })}</span>
        </div>

        <div className="mt-5 flex items-center gap-5">
          <CircularProgress value={current.sustainability} size={84} strokeWidth={7} sublabel={t('landing.showcase.sustainShort')} />
          <div className="min-w-0">
            <AnimatePresence mode="wait">
              <motion.div
                key={current.name}
                initial={{ opacity: 0, x: 12 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -12 }}
                transition={{ duration: 0.35 }}
              >
                <p className="truncate font-display text-lg font-extrabold text-ink-900">{current.name}</p>
                <p className="mt-0.5 text-xs text-ink-500">{current.tag}</p>
                <div className="mt-2 flex items-center gap-1.5 text-sm font-bold text-brand-700">
                  <ShieldCheck className="size-4" aria-hidden="true" />
                  {t('landing.showcase.fitScore', { score: current.score })}
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>

        <div className="mt-5 flex gap-1.5">
          {DEMO_MATERIALS.map((m, i) => (
            <span
              key={m.name}
              className={`h-1 flex-1 rounded-pill transition-colors duration-300 ${i === index ? 'bg-brand-600' : 'bg-ink-200'}`}
            />
          ))}
        </div>
      </motion.div>

      <motion.div
        animate={{ rotate: [0, 8, 0], y: [0, 6, 0] }}
        transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute -right-6 -top-6 flex size-16 items-center justify-center rounded-2xl bg-amber-500 text-white shadow-soft-lg"
      >
        <Recycle className="size-7" aria-hidden="true" />
      </motion.div>
    </div>
  )
}
