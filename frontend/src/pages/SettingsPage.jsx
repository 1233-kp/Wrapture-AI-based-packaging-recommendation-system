import { motion } from 'framer-motion'
import { CheckCircle2, LogOut, Mail } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { Card, CardBody, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'
import { FullPageSpinner } from '../components/ui/Spinner'
import { SegmentedControl } from '../components/ui/SegmentedControl'
import { Toggle } from '../components/ui/Toggle'
import { GithubIcon, GoogleIcon } from '../components/ui/BrandIcons'
import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'

export default function SettingsPage() {
  const { t } = useTranslation()
  const { user, accessToken, signOut } = useAuth()
  const navigate = useNavigate()

  const BUDGET_OPTIONS = [
    { value: 'low', label: t('recommend.budgetEconomy') },
    { value: 'medium', label: t('recommend.budgetStandard') },
    { value: 'high', label: t('recommend.budgetPremium') },
  ]

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState(null)

  const [displayName, setDisplayName] = useState('')
  const [budgetTier, setBudgetTier] = useState('medium')
  const [prioritizeSustainability, setPrioritizeSustainability] = useState(false)

  useEffect(() => {
    document.title = t('settings.pageTitle')
    if (!accessToken) return
    api
      .getProfile(accessToken)
      .then((profile) => {
        setDisplayName(profile.display_name || '')
        setBudgetTier(profile.preferred_budget_tier || 'medium')
        setPrioritizeSustainability(!!profile.prioritize_sustainability)
      })
      .catch((err) => setError(err.message || t('settings.loadError')))
      .finally(() => setLoading(false))
  }, [accessToken, t])

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    setSaved(false)
    try {
      await api.updateProfile(accessToken, {
        display_name: displayName || null,
        preferred_budget_tier: budgetTier,
        prioritize_sustainability: prioritizeSustainability,
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch (err) {
      setError(err.message || t('settings.saveError'))
    } finally {
      setSaving(false)
    }
  }

  const handleSignOut = async () => {
    await signOut()
    navigate('/')
  }

  const provider = user?.app_metadata?.provider

  if (loading) return <FullPageSpinner label={t('settings.loadingSettings')} />

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6 sm:py-12 lg:px-8">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-display text-2xl font-extrabold text-ink-900 sm:text-3xl">{t('settings.heading')}</h1>
        <p className="mt-1 text-sm text-ink-500">{t('settings.subhead')}</p>
      </motion.div>

      <div className="mt-8 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>{t('settings.profile')}</CardTitle>
            <CardDescription>{t('settings.profileDescription')}</CardDescription>
          </CardHeader>
          <CardBody className="space-y-6">
            <div>
              <label htmlFor="display-name" className="mb-2 block text-sm font-semibold text-ink-800">
                {t('settings.displayName')}
              </label>
              <input
                id="display-name"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder={t('settings.displayNamePlaceholder')}
                className="min-h-11 w-full rounded-xl border border-ink-200 px-3.5 text-sm focus:border-brand-400 focus:outline-none"
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-semibold text-ink-800">{t('settings.defaultBudgetTier')}</label>
              <SegmentedControl
                name="default-budget-tier"
                options={BUDGET_OPTIONS}
                value={budgetTier}
                onChange={setBudgetTier}
              />
            </div>

            <div className="rounded-xl border border-ink-100 bg-ink-50 p-4">
              <Toggle
                id="default-sustainability"
                checked={prioritizeSustainability}
                onChange={setPrioritizeSustainability}
                label={t('settings.prioritizeSustainabilityDefault')}
                description={t('settings.prioritizeSustainabilityDefaultDesc')}
              />
            </div>

            <div className="flex items-center gap-3">
              <Button loading={saving} onClick={handleSave}>
                {t('settings.saveChanges')}
              </Button>
              {saved && (
                <motion.span
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-center gap-1.5 text-sm font-semibold text-brand-700"
                >
                  <CheckCircle2 className="size-4" aria-hidden="true" /> {t('settings.saved')}
                </motion.span>
              )}
              {error && <span className="text-sm font-medium text-danger">{error}</span>}
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t('settings.account')}</CardTitle>
          </CardHeader>
          <CardBody className="space-y-3">
            <div className="flex items-center gap-3 text-sm">
              <Mail className="size-4 text-ink-400" aria-hidden="true" />
              <span className="text-ink-700">{user?.email}</span>
            </div>
            <div className="flex items-center gap-3 text-sm">
              {provider === 'github' ? (
                <GithubIcon className="size-4 text-ink-400" aria-hidden="true" />
              ) : (
                <GoogleIcon />
              )}
              <span className="text-ink-700">
                {t('settings.connectedVia', { provider: provider || 'OAuth' })}
              </span>
            </div>
          </CardBody>
        </Card>

        <Button variant="destructive" icon={LogOut} onClick={handleSignOut}>
          {t('settings.signOut')}
        </Button>
      </div>
    </div>
  )
}
