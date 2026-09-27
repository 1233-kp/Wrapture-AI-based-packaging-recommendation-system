import { motion } from 'framer-motion'
import { ArrowRight, PlayCircle } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import logoMark from '../../assets/wrapture-mark.png'
import { useAuth } from '../../context/AuthContext'
import { Button } from '../ui/Button'
import { HeroVisual } from './HeroVisual'

const containerVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.15, delayChildren: 0.1 } },
}
const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } },
}

/**
 * Structure adapted from 21st.dev "Animated Hero Section" (ravikatiyar162, id
 * 8110): staggered containerVariants/itemVariants driving h1/p/CTA reveal,
 * kept as the animation backbone. Swapped their background-photo layout for a
 * two-column layout (copy + RotatingMaterialShowcase) since a stock photo
 * doesn't represent this product's explainable-reasoning value prop as well
 * as a live demo of the thing itself.
 */
export function Hero() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()

  return (
    <section className="relative overflow-hidden bg-linear-to-b from-brand-50 via-white to-white pt-32 pb-20 sm:pt-40 sm:pb-28">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 bg-grain opacity-60"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -left-32 top-24 size-96 rounded-full bg-teal-200/40 blur-3xl"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-24 top-64 size-96 rounded-full bg-amber-200/40 blur-3xl"
      />
      {/* Large, centered brand-mark watermark — fixed to the viewport (not
          the section), so it holds still while the page scrolls past/over
          it, rather than scrolling away with the hero. Lenis (mounted below)
          drives native scroll with no CSS transform on any ancestor, so
          `fixed` here is genuinely viewport-anchored, not just section-
          anchored. Explicit z-0 vs the content wrapper's z-10 below removes
          any ambiguity about paint order — this must never cover the text/
          cards, and never intercepts clicks/taps either way. */}
      <img
        src={logoMark}
        alt=""
        aria-hidden="true"
        className="pointer-events-none fixed left-1/2 top-1/2 z-0 w-180 max-w-[130vw] -translate-x-1/2 -translate-y-1/2 select-none opacity-[0.06]"
      />

      <div className="relative z-10 mx-auto grid max-w-7xl grid-cols-1 items-center gap-16 px-4 sm:px-6 lg:grid-cols-2 lg:px-8">
        <motion.div variants={containerVariants} initial="hidden" animate="visible">
          <motion.h1
            variants={itemVariants}
            className="text-balance font-display text-4xl font-extrabold leading-[1.1] text-ink-900 sm:text-5xl lg:text-6xl"
          >
            {t('landing.hero.titleLine1')}
            <br />
            <span className="text-brand-600">{t('landing.hero.titleLine2')}</span>
          </motion.h1>

          <motion.p variants={itemVariants} className="mt-6 max-w-lg text-lg text-ink-600">
            {t('landing.hero.body')}
          </motion.p>

          <motion.div variants={itemVariants} className="mt-9 flex flex-col gap-3 sm:flex-row">
            <Button
              size="lg"
              icon={ArrowRight}
              iconPosition="right"
              onClick={() => navigate(isAuthenticated ? '/app/recommend' : '/signin')}
            >
              {t('landing.hero.ctaPrimary')}
            </Button>
            <Button as="a" href="#how-it-works" size="lg" variant="secondary" icon={PlayCircle}>
              {t('landing.hero.ctaSecondary')}
            </Button>
          </motion.div>

          <motion.p variants={itemVariants} className="mt-6 text-xs text-ink-400">
            {t('landing.hero.finePrint')}
          </motion.p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.3, ease: 'easeOut' }}
        >
          <HeroVisual />
        </motion.div>
      </div>
    </section>
  )
}
