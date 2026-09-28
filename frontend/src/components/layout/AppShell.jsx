import { CircleHelp, LayoutDashboard, Library, LogOut, Package, QrCode, Recycle, Settings, Sparkles } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { cn } from '../../lib/utils'
import { BrandMark } from '../ui/BrandMark'
import { Button } from '../ui/Button'
import { InstallAppButton } from '../ui/InstallAppButton'
import { LanguageToggle } from '../ui/LanguageToggle'

function useNavItems() {
  const { t } = useTranslation()
  return [
    { to: '/app/recommend', label: t('nav.recommend'), icon: Sparkles },
    { to: '/app/dashboard', label: t('nav.dashboard'), icon: LayoutDashboard },
    { to: '/app/history', label: t('nav.history'), icon: Package },
    { to: '/app/settings', label: t('nav.settings'), icon: Settings },
  ]
}

// Shown only in the desktop sidebar, as a separate group below the primary
// items — kept out of the mobile bottom nav so it doesn't get cramped down
// to 8 tiny icons. Packaging Library and FAQ need no login (see their
// /app/library and /app/faq routes in App.jsx, deliberately outside
// ProtectedRoute); Sustainability and Traceability still require one.
function useLibraryNavItems() {
  const { t } = useTranslation()
  return [
    { to: '/app/library', label: t('nav.library'), icon: Library },
    { to: '/app/sustainability', label: t('nav.sustainability'), icon: Recycle },
    { to: '/app/traceability', label: t('nav.traceability'), icon: QrCode },
    { to: '/app/faq', label: t('nav.faq'), icon: CircleHelp },
  ]
}

function UserAvatar({ user, size = 'size-9' }) {
  const meta = user?.user_metadata ?? {}
  const avatarUrl = meta.avatar_url || meta.picture
  const name = meta.full_name || meta.name || user?.email || 'User'
  const initials = name
    .split(' ')
    .map((s) => s[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()

  if (avatarUrl) {
    return <img src={avatarUrl} alt="" className={cn(size, 'rounded-full object-cover')} />
  }
  return (
    <div className={cn(size, 'flex items-center justify-center rounded-full bg-brand-100 text-brand-700 font-bold text-sm')}>
      {initials}
    </div>
  )
}

function NavItem({ to, label, icon: Icon, className }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-semibold transition-colors',
          isActive ? 'bg-brand-600 text-white shadow-soft-sm' : 'text-ink-600 hover:bg-brand-50 hover:text-brand-700',
          className
        )
      }
    >
      <Icon className="size-5 shrink-0" aria-hidden="true" />
      {label}
    </NavLink>
  )
}

export function AppShell() {
  const { t } = useTranslation()
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const navItems = useNavItems()
  const libraryNavItems = useLibraryNavItems()

  const handleSignOut = async () => {
    await signOut()
    navigate('/')
  }

  const displayName = user?.user_metadata?.full_name || user?.user_metadata?.name || user?.email

  return (
    <div className="min-h-screen bg-ink-50 md:flex">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex md:w-64 md:flex-col md:border-r md:border-ink-200 md:bg-white md:px-4 md:py-6">
        <Link to="/app/dashboard" className="mb-6 flex items-center gap-2 px-2">
          <BrandMark size="size-9" />
          <span className="font-display text-lg font-extrabold text-ink-900">{t('common.brand')}</span>
        </Link>

        <div className="mb-4 flex items-center gap-2 px-2">
          <LanguageToggle />
          <InstallAppButton size="sm" variant="secondary" />
        </div>

        <nav className="flex flex-1 flex-col gap-1">
          {navItems.map((item) => (
            <NavItem key={item.to} {...item} />
          ))}

          <p className="mb-1 mt-5 px-3.5 text-[11px] font-bold uppercase tracking-wide text-ink-400">
            {t('nav.libraryGroup')}
          </p>
          {libraryNavItems.map((item) => (
            <NavItem key={item.to} {...item} />
          ))}
        </nav>

        {user ? (
          <div className="mt-4 flex items-center gap-3 rounded-xl border border-ink-100 bg-ink-50 p-3">
            <UserAvatar user={user} />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-ink-900">{displayName}</p>
              <p className="truncate text-xs text-ink-500">{user?.email}</p>
            </div>
            <button
              onClick={handleSignOut}
              aria-label={t('common.signOut')}
              className="flex size-9 shrink-0 items-center justify-center rounded-lg text-ink-500 hover:bg-danger-bg hover:text-danger cursor-pointer"
            >
              <LogOut className="size-4" aria-hidden="true" />
            </button>
          </div>
        ) : (
          <div className="mt-4 rounded-xl border border-ink-100 bg-ink-50 p-3">
            <p className="text-xs text-ink-500">{t('nav.signInPrompt')}</p>
            <Button size="sm" className="mt-2 w-full" onClick={() => navigate('/signin')}>
              {t('nav.signIn')}
            </Button>
          </div>
        )}
      </aside>

      {/* Mobile top bar */}
      <header className="flex items-center justify-between border-b border-ink-200 bg-white px-4 py-3 md:hidden">
        <Link to="/app/dashboard" className="flex items-center gap-2">
          <BrandMark size="size-8" />
          <span className="font-display text-base font-extrabold text-ink-900">{t('common.brand')}</span>
        </Link>
        <div className="flex items-center gap-2">
          <LanguageToggle />
          {user ? (
            <button onClick={handleSignOut} aria-label={t('common.signOut')} className="flex items-center gap-2">
              <UserAvatar user={user} size="size-8" />
            </button>
          ) : (
            <Button size="sm" onClick={() => navigate('/signin')}>
              {t('nav.signIn')}
            </Button>
          )}
        </div>
      </header>

      <div className="flex-1 pb-20 md:pb-0">
        <Outlet />
      </div>

      {/* Mobile bottom nav */}
      <nav className="fixed inset-x-0 bottom-0 z-40 flex border-t border-ink-200 bg-white/95 backdrop-blur md:hidden">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                'flex flex-1 flex-col items-center gap-1 py-2.5 text-[11px] font-semibold min-h-14 justify-center',
                isActive ? 'text-brand-700' : 'text-ink-400'
              )
            }
          >
            <Icon className="size-5" aria-hidden="true" />
            {label}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
