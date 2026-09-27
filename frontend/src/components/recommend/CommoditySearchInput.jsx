import { Check, ChevronDown, Search } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { cn, localizedName } from '../../lib/utils'

export function CommoditySearchInput({ commodities, value, onChange, loading }) {
  const { t, i18n } = useTranslation()
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const containerRef = useRef(null)

  useEffect(() => {
    function handleClick(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return commodities
    return commodities.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        c.name_hi?.includes(query.trim()) ||
        c.category.toLowerCase().includes(q)
    )
  }, [commodities, query])

  const grouped = useMemo(() => {
    const groups = {}
    for (const c of filtered) {
      const key = c.category
      groups[key] = groups[key] || []
      groups[key].push(c)
    }
    return groups
  }, [filtered])

  const selected = commodities.find((c) => c.id === value)

  return (
    <div className="relative" ref={containerRef}>
      <label className="mb-2 block text-sm font-semibold text-ink-800">{t('recommend.commodityLabel')}</label>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex min-h-12 w-full cursor-pointer items-center justify-between rounded-xl border border-ink-200 bg-white px-4 py-3 text-left shadow-soft-sm transition-colors hover:border-brand-300"
      >
        <span className={cn('text-sm font-medium', selected ? 'text-ink-900' : 'text-ink-400')}>
          {loading
            ? t('recommend.loadingCommodities')
            : selected
              ? localizedName(selected.name, selected.name_hi, i18n.language)
              : t('recommend.searchCommodities')}
        </span>
        <ChevronDown className={cn('size-4 text-ink-400 transition-transform', open && 'rotate-180')} aria-hidden="true" />
      </button>

      {open && (
        <div className="absolute z-20 mt-2 w-full overflow-hidden rounded-xl border border-ink-200 bg-white shadow-soft-lg">
          <div className="flex items-center gap-2 border-b border-ink-100 px-3.5 py-2.5">
            <Search className="size-4 shrink-0 text-ink-400" aria-hidden="true" />
            <input
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t('recommend.searchPlaceholder')}
              className="w-full text-sm text-ink-800 placeholder:text-ink-400 focus:outline-none"
            />
          </div>
          <div className="max-h-72 overflow-y-auto py-1.5">
            {Object.keys(grouped).length === 0 && (
              <p className="px-4 py-6 text-center text-sm text-ink-400">
                {t('recommend.noCommodityMatch', { query })}
              </p>
            )}
            {Object.entries(grouped).map(([category, items]) => (
              <div key={category}>
                <p className="px-4 pb-1 pt-2.5 text-[11px] font-bold uppercase tracking-wide text-ink-400">
                  {t(`results.category.${category}`, { defaultValue: category })}
                </p>
                {items.map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => {
                      onChange(c.id)
                      setOpen(false)
                      setQuery('')
                    }}
                    className="flex w-full cursor-pointer items-center justify-between px-4 py-2.5 text-left text-sm font-medium text-ink-700 hover:bg-brand-50 hover:text-brand-700"
                  >
                    {localizedName(c.name, c.name_hi, i18n.language)}
                    {c.id === value && <Check className="size-4 text-brand-600" aria-hidden="true" />}
                  </button>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
