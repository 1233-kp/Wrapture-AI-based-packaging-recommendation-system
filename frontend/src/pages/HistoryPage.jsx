import { motion } from 'framer-motion'
import { PackageSearch, Search } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { ReportCard } from '../components/dashboard/ReportCard'
import { Button } from '../components/ui/Button'
import { EmptyState } from '../components/ui/EmptyState'
import { FullPageSpinner } from '../components/ui/Spinner'
import { useReports } from '../hooks/useReports'

export default function HistoryPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { reports, loading, error, deleteReport } = useReports({ limit: 100 })
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('all')

  useEffect(() => {
    document.title = t('history.pageTitle')
  }, [t])

  const categories = useMemo(() => {
    const set = new Set(reports.map((r) => r.recommendation?.commodity?.category).filter(Boolean))
    return ['all', ...Array.from(set)]
  }, [reports])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return reports.filter((r) => {
      const matchesQuery = !q || r.commodity_name.toLowerCase().includes(q)
      const matchesCategory = category === 'all' || r.recommendation?.commodity?.category === category
      return matchesQuery && matchesCategory
    })
  }, [reports, query, category])

  if (loading) return <FullPageSpinner label={t('history.loadingReports')} />

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-12 lg:px-8">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="font-display text-2xl font-extrabold text-ink-900 sm:text-3xl">{t('history.heading')}</h1>
        <p className="mt-1 text-sm text-ink-500">{t('history.savedCount', { count: reports.length })}</p>
      </motion.div>

      {error && <p className="mt-4 text-sm font-medium text-danger">{error}</p>}

      {reports.length === 0 ? (
        <div className="mt-8">
          <EmptyState
            icon={PackageSearch}
            title={t('history.emptyTitle')}
            description={t('history.emptyDescription')}
            action={<Button onClick={() => navigate('/app/recommend')}>{t('common.newRecommendation')}</Button>}
          />
        </div>
      ) : (
        <>
          <div className="mt-6 flex flex-col gap-3 sm:flex-row">
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-ink-400" aria-hidden="true" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={t('history.searchPlaceholder')}
                className="min-h-11 w-full rounded-xl border border-ink-200 bg-white py-2.5 pl-10 pr-4 text-sm shadow-soft-sm focus:border-brand-400 focus:outline-none"
              />
            </div>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="min-h-11 rounded-xl border border-ink-200 bg-white px-3.5 text-sm font-medium text-ink-700 shadow-soft-sm focus:border-brand-400 focus:outline-none"
            >
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c === 'all' ? t('history.allCategories') : t(`results.category.${c}`, { defaultValue: c })}
                </option>
              ))}
            </select>
          </div>

          {filtered.length === 0 ? (
            <p className="mt-10 text-center text-sm text-ink-400">{t('history.noMatch')}</p>
          ) : (
            <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {filtered.map((report, i) => (
                <ReportCard key={report.id} report={report} index={i} onDelete={deleteReport} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
