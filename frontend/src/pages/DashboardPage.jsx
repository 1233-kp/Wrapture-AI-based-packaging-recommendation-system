import { motion } from 'framer-motion'
import { PackageSearch, Plus } from 'lucide-react'
import { useEffect, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { ActivityChart } from '../components/dashboard/ActivityChart'
import { ReportCard } from '../components/dashboard/ReportCard'
import { StatsGrid } from '../components/dashboard/StatsGrid'
import { Button } from '../components/ui/Button'
import { EmptyState } from '../components/ui/EmptyState'
import { FullPageSpinner } from '../components/ui/Spinner'
import { useAuth } from '../context/AuthContext'
import { buildWeeklyActivity, computeStats } from '../lib/dashboardHelpers'
import { useReports } from '../hooks/useReports'

export default function DashboardPage() {
  const { t } = useTranslation()
  const { user } = useAuth()
  const navigate = useNavigate()
  const { reports, loading, error, deleteReport } = useReports({ limit: 100 })

  useEffect(() => {
    document.title = t('dashboard.pageTitle')
  }, [t])

  const stats = useMemo(() => computeStats(reports, user), [reports, user])
  const activity = useMemo(() => buildWeeklyActivity(reports), [reports])
  const recent = reports.slice(0, 6)

  const displayName = user?.user_metadata?.full_name || user?.user_metadata?.name || user?.email?.split('@')[0]

  if (loading) return <FullPageSpinner label={t('dashboard.loadingDashboard')} />

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-12 lg:px-8">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-wrap items-center justify-between gap-4"
      >
        <div>
          <h1 className="font-display text-2xl font-extrabold text-ink-900 sm:text-3xl">
            {t('dashboard.welcomeBack', { name: displayName })}
          </h1>
          <p className="mt-1 text-sm text-ink-500">{t('dashboard.subhead')}</p>
        </div>
        <Button icon={Plus} onClick={() => navigate('/app/recommend')}>
          {t('common.newRecommendation')}
        </Button>
      </motion.div>

      {error && <p className="mt-4 text-sm font-medium text-danger">{error}</p>}

      <div className="mt-8">
        <StatsGrid {...stats} />
      </div>

      {reports.length === 0 ? (
        <div className="mt-8">
          <EmptyState
            icon={PackageSearch}
            title={t('dashboard.emptyTitle')}
            description={t('dashboard.emptyDescription')}
            action={<Button onClick={() => navigate('/app/recommend')}>{t('dashboard.getFirstRecommendation')}</Button>}
          />
        </div>
      ) : (
        <>
          <div className="mt-8">
            <ActivityChart data={activity} />
          </div>

          <div className="mt-8">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-ink-900">{t('dashboard.recentReports')}</h2>
              <button
                onClick={() => navigate('/app/history')}
                className="cursor-pointer text-sm font-semibold text-brand-700 hover:text-brand-800"
              >
                {t('dashboard.viewAll')}
              </button>
            </div>
            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {recent.map((report, i) => (
                <ReportCard key={report.id} report={report} index={i} onDelete={deleteReport} />
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
