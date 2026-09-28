import { AnimatePresence, motion } from 'framer-motion'
import { Menu, X } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { BrandMark } from '../ui/BrandMark'
import { Button } from '../ui/Button'
import { InstallAppButton } from '../ui/InstallAppButton'
import { LanguageToggle } from '../ui/LanguageToggle'

export function Navbar() {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()

  // Section links are prefixed with "/" (not bare "#...") so they resolve
  // correctly from any page that renders this Navbar, not just the landing
  // page itself — the browser navigates to "/" first if needed, then jumps
  // to the section. FAQ is a real route, not a section, so it's rendered as
  // a router Link instead of a plain anchor (see LINKS.map below).
  const LINKS = [
    { href: '/#how-it-works', label: t('nav.howItWorks') },
    { href: '/#materials', label: t('nav.materials') },
    { href: '/#impact', label: t('nav.impact') },
    { href: '/faq', label: t('nav.faq'), isRoute: true },
  ]

  return (
    <motion.header
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className="fixed inset-x-0 top-0 z-50 border-b border-white/20 bg-white/70 backdrop-blur-lg"
    >
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3.5 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-2">
          <BrandMark size="size-9" />
          <span className="font-display text-lg font-extrabold text-ink-900">{t('common.brand')}</span>
        </Link>

        <div className="hidden items-center gap-8 md:flex">
          {LINKS.map((link) =>
            link.isRoute ? (
              <Link
                key={link.href}
                to={link.href}
                className="text-sm font-semibold text-ink-600 transition-colors hover:text-brand-700"
              >
                {link.label}
              </Link>
            ) : (
              <a
                key={link.href}
                href={link.href}
                className="text-sm font-semibold text-ink-600 transition-colors hover:text-brand-700"
              >
                {link.label}
              </a>
            )
          )}
        </div>

        <div className="hidden items-center gap-3 md:flex">
          <InstallAppButton />
          <LanguageToggle />
          {isAuthenticated ? (
            <Button size="sm" onClick={() => navigate('/app/recommend')}>
              {t('nav.goToApp')}
            </Button>
          ) : (
            <>
              <Button variant="ghost" size="sm" onClick={() => navigate('/signin')}>
                {t('nav.signIn')}
              </Button>
              <Button size="sm" onClick={() => navigate('/signin')}>
                {t('nav.getStarted')}
              </Button>
            </>
          )}
        </div>

        <div className="flex items-center gap-2 md:hidden">
          <LanguageToggle />
          <button
            className="flex size-10 items-center justify-center rounded-xl text-ink-700 hover:bg-ink-100 cursor-pointer"
            onClick={() => setOpen((v) => !v)}
            aria-label={open ? t('nav.closeMenu') : t('nav.openMenu')}
            aria-expanded={open}
          >
            {open ? <X className="size-5" /> : <Menu className="size-5" />}
          </button>
        </div>
      </nav>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden border-t border-ink-200 bg-white md:hidden"
          >
            <div className="flex flex-col gap-1 px-4 py-4">
              {LINKS.map((link) =>
                link.isRoute ? (
                  <Link
                    key={link.href}
                    to={link.href}
                    onClick={() => setOpen(false)}
                    className="rounded-xl px-3 py-2.5 text-sm font-semibold text-ink-700 hover:bg-ink-100"
                  >
                    {link.label}
                  </Link>
                ) : (
                  <a
                    key={link.href}
                    href={link.href}
                    onClick={() => setOpen(false)}
                    className="rounded-xl px-3 py-2.5 text-sm font-semibold text-ink-700 hover:bg-ink-100"
                  >
                    {link.label}
                  </a>
                )
              )}
              <div className="mt-2 flex flex-col gap-2 border-t border-ink-100 pt-3">
                <InstallAppButton size="md" variant="secondary" className="w-full" />
                {isAuthenticated ? (
                  <Button onClick={() => navigate('/app/recommend')}>{t('nav.goToApp')}</Button>
                ) : (
                  <>
                    <Button variant="secondary" onClick={() => navigate('/signin')}>
                      {t('nav.signIn')}
                    </Button>
                    <Button onClick={() => navigate('/signin')}>{t('nav.getStarted')}</Button>
                  </>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  )
}
