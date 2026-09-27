import { motion } from 'framer-motion'
import { Recycle, ShieldCheck, Sprout } from 'lucide-react'
import { useTranslation } from 'react-i18next'

const IDEAS = [
  { icon: Sprout, tone: 'brand', key: 'reduceWaste' },
  { icon: ShieldCheck, tone: 'teal', key: 'improveSelection' },
  { icon: Recycle, tone: 'amber', key: 'supportSustainability' },
]

const TONE_CLASSES = {
  brand: 'bg-brand-100 text-brand-700',
  teal: 'bg-teal-100 text-teal-700',
  amber: 'bg-amber-100 text-amber-700',
}

export function Impact() {
  const { t } = useTranslation()

  return (
    <section id="impact" className="py-20 sm:py-28">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <motion.h2
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.5 }}
          className="text-center font-display text-3xl font-extrabold text-ink-900 sm:text-4xl"
        >
          {t('landing.impact.heading')}
        </motion.h2>

        <div className="mt-16 grid grid-cols-1 gap-10 sm:grid-cols-3 sm:gap-8">
          {IDEAS.map((idea, i) => (
            <motion.div
              key={idea.key}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ duration: 0.45, delay: i * 0.1 }}
              className="text-center"
            >
              <span
                className={`mx-auto flex size-14 items-center justify-center rounded-2xl ${TONE_CLASSES[idea.tone]}`}
              >
                <idea.icon className="size-7" aria-hidden="true" />
              </span>
              <h3 className="mt-5 text-lg font-bold text-ink-900">{t(`landing.impact.${idea.key}Title`)}</h3>
              <p className="mt-2 text-sm text-ink-500">{t(`landing.impact.${idea.key}Body`)}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
