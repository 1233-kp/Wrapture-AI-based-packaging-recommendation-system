import { motion } from 'framer-motion'
import { Flame, Snowflake, Sun, Thermometer } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { cn } from '../../lib/utils'

export function StorageTypeCards({ value, onChange }) {
  const { t } = useTranslation()

  const STORAGE_TYPES = [
    { id: 'refrigerated', label: t('recommend.storageRefrigerated'), temp: 4, icon: Snowflake },
    { id: 'cool', label: t('recommend.storageCoolRoom'), temp: 15, icon: Thermometer },
    { id: 'ambient', label: t('recommend.storageRoomTemp'), temp: 25, icon: Sun },
    { id: 'hot', label: t('recommend.storageHotClimate'), temp: 36, icon: Flame },
  ]

  return (
    <div>
      <label className="mb-2 block text-sm font-semibold text-ink-800">{t('recommend.storageLabel')}</label>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {STORAGE_TYPES.map((type) => {
          const active = value === type.temp
          return (
            <motion.button
              key={type.id}
              type="button"
              whileTap={{ scale: 0.96 }}
              onClick={() => onChange(type.temp)}
              className={cn(
                'flex min-h-20 flex-col items-center justify-center gap-1.5 rounded-xl border px-3 py-3 text-center transition-colors cursor-pointer',
                active
                  ? 'border-brand-500 bg-brand-50 shadow-soft-sm'
                  : 'border-ink-200 bg-white hover:border-brand-200'
              )}
            >
              <type.icon className={cn('size-5', active ? 'text-brand-600' : 'text-ink-400')} aria-hidden="true" />
              <span className={cn('text-xs font-semibold', active ? 'text-brand-700' : 'text-ink-600')}>
                {type.label}
              </span>
              <span className="text-[10px] text-ink-400">~{type.temp}°C</span>
            </motion.button>
          )
        })}
      </div>
    </div>
  )
}
