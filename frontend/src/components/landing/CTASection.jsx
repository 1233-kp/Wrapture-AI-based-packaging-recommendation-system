import { motion } from 'framer-motion'
import { ArrowRight } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { Button } from '../ui/Button'

export function CTASection() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()
  return (
    <section className="py-20 sm:py-28">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.5 }}
          className="relative overflow-hidden rounded-card bg-linear-to-br from-brand-700 via-brand-600 to-teal-600 px-6 py-14 text-center shadow-soft-xl sm:px-16"
        >
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-0 bg-grain opacity-20"
          />
          <h2 className="relative font-display text-3xl font-extrabold text-white sm:text-4xl">
            {t('landing.cta.heading')}
          </h2>
          <div className="relative mt-8">
            <Button
              size="lg"
              variant="accent"
              icon={ArrowRight}
              iconPosition="right"
              onClick={() => navigate(isAuthenticated ? '/app/recommend' : '/signin')}
            >
              {t('landing.cta.button')}
            </Button>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
