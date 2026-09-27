import { motion } from 'framer-motion'
import { Apple, ArrowRight, Cpu, Leaf, PackageCheck, Timer } from 'lucide-react'
import { useTranslation } from 'react-i18next'

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.15 } },
}
const stepVariants = {
  hidden: { opacity: 0, y: 24, scale: 0.95 },
  visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.5, ease: 'easeOut' } },
}
const lineVariants = {
  hidden: { scaleX: 0 },
  visible: { scaleX: 1, transition: { duration: 0.5, ease: 'easeOut' } },
}

const STEP_ICONS = [Apple, Cpu, PackageCheck, Timer, Leaf]
const STEP_TONES = ['brand', 'teal', 'amber', 'teal', 'brand']

const TONE_CLASSES = {
  brand: 'bg-brand-100 text-brand-700 border-brand-200',
  teal: 'bg-teal-100 text-teal-700 border-teal-200',
  amber: 'bg-amber-100 text-amber-700 border-amber-200',
}

export function AIAnalysisFlow() {
  const { t } = useTranslation()

  const steps = [0, 1, 2, 3, 4].map((i) => ({
    icon: STEP_ICONS[i],
    tone: STEP_TONES[i],
    title: t(`landing.flow.step${i + 1}Title`),
    description: t(`landing.flow.step${i + 1}Body`),
  }))

  return (
    <section id="how-it-works" className="relative overflow-hidden bg-ink-50 py-16 sm:py-20">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 bg-grain opacity-40"
      />
      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-2xl text-center"
        >
          <h2 className="font-display text-3xl font-extrabold text-ink-900 sm:text-4xl">
            {t('landing.flow.heading')}
          </h2>
          <p className="mt-3 text-ink-500">{t('landing.flow.subhead')}</p>
        </motion.div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-80px' }}
          className="mt-16 flex flex-col items-stretch gap-3 lg:flex-row lg:items-center lg:gap-0"
        >
          {steps.map((step, i) => (
            <div key={step.title} className="flex flex-1 flex-col items-center lg:flex-row">
              <motion.div
                variants={stepVariants}
                className="flex w-full flex-col items-center rounded-card border border-ink-200/70 bg-white p-4 text-center shadow-soft-md sm:p-5"
              >
                <span
                  className={`flex size-14 items-center justify-center rounded-2xl border ${TONE_CLASSES[step.tone]}`}
                >
                  <step.icon className="size-7" aria-hidden="true" />
                </span>
                <span className="mt-3 font-display text-xs font-bold tracking-wide text-ink-300">
                  {String(i + 1).padStart(2, '0')}
                </span>
                <h3 className="mt-1 text-sm font-bold text-ink-900 sm:text-base">{step.title}</h3>
                <p className="mt-1.5 text-xs text-ink-500 sm:text-sm">{step.description}</p>
              </motion.div>

              {i < steps.length - 1 && (
                <>
                  {/* Horizontal connector, desktop only */}
                  <motion.div
                    variants={lineVariants}
                    style={{ transformOrigin: 'left' }}
                    className="hidden h-0.5 w-8 shrink-0 bg-linear-to-r from-brand-300 to-teal-300 lg:block xl:w-12"
                  />
                  {/* Vertical connector, mobile only */}
                  <div className="flex h-6 items-center justify-center lg:hidden">
                    <ArrowRight className="size-4 rotate-90 text-ink-300" aria-hidden="true" />
                  </div>
                </>
              )}
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}
