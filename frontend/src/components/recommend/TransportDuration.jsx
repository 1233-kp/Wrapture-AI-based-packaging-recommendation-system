import { useTranslation } from 'react-i18next'
import { Slider } from '../ui/Slider'

function formatDays(days, t) {
  if (days < 1) return t('common.hoursShort', { n: Math.round(days * 24) })
  if (days === 1) return t('common.oneDay')
  return t('common.daysCount', { n: days })
}

export function TransportDuration({ value, onChange }) {
  const { t } = useTranslation()

  const PRESETS = [
    { label: t('recommend.transportSameDay'), days: 0.5 },
    { label: t('recommend.transport2to3Days'), days: 3 },
    { label: t('recommend.transport1Week'), days: 7 },
    { label: t('recommend.transport2Weeks'), days: 14 },
    { label: t('recommend.transport1MonthPlus'), days: 35 },
  ]

  return (
    <div>
      <Slider
        id="transport-days"
        label={t('recommend.transportLabel')}
        valueLabel={formatDays(value, t)}
        min={0}
        max={45}
        step={0.5}
        value={value}
        onChange={onChange}
      />
      <div className="mt-3 flex flex-wrap gap-2">
        {PRESETS.map((preset) => (
          <button
            key={preset.label}
            type="button"
            onClick={() => onChange(preset.days)}
            className="rounded-pill border border-ink-200 bg-white px-3 py-1.5 text-xs font-semibold text-ink-600 transition-colors hover:border-brand-300 hover:text-brand-700 cursor-pointer"
          >
            {preset.label}
          </button>
        ))}
      </div>
    </div>
  )
}
