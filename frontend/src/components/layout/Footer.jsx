import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { BrandMark } from '../ui/BrandMark'

export function Footer() {
  const { t } = useTranslation()
  return (
    <footer className="border-t border-ink-200 bg-white">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="flex flex-col items-start justify-between gap-8 sm:flex-row">
          <div>
            <div className="flex items-center gap-2">
              <BrandMark size="size-8" />
              <span className="font-display text-base font-extrabold text-ink-900">{t('common.brand')}</span>
            </div>
            <p className="mt-3 max-w-xs text-sm text-ink-500">{t('landing.footer.tagline')}</p>
          </div>
          <div className="grid grid-cols-2 gap-8 sm:gap-16">
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wide text-ink-400">{t('landing.footer.product')}</h4>
              <ul className="mt-3 space-y-2 text-sm text-ink-600">
                <li><a href="/#how-it-works" className="hover:text-brand-700">{t('nav.howItWorks')}</a></li>
                <li><a href="/#impact" className="hover:text-brand-700">{t('nav.impact')}</a></li>
                <li><Link to="/faq" className="hover:text-brand-700">{t('nav.faq')}</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wide text-ink-400">{t('landing.footer.legal')}</h4>
              <ul className="mt-3 space-y-2 text-sm text-ink-600">
                <li>{t('landing.footer.heuristicNotice')}</li>
              </ul>
            </div>
          </div>
        </div>
        <div className="mt-10 border-t border-ink-100 pt-6 text-xs text-ink-400">
          {t('landing.footer.copyright', { year: new Date().getFullYear() })}
        </div>
      </div>
    </footer>
  )
}
