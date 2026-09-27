import { cn } from '../../lib/utils'

export function Slider({ value, onChange, min = 0, max = 100, step = 1, label, valueLabel, id }) {
  const pct = ((value - min) / (max - min)) * 100
  return (
    <div>
      {label && (
        <div className="mb-2 flex items-center justify-between">
          <label htmlFor={id} className="text-sm font-semibold text-ink-800">
            {label}
          </label>
          <span className="text-sm font-bold text-brand-700">{valueLabel ?? value}</span>
        </div>
      )}
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className={cn('h-2 w-full cursor-pointer appearance-none rounded-pill bg-ink-200 accent-brand-600')}
        style={{
          background: `linear-gradient(to right, var(--color-brand-600) ${pct}%, var(--color-ink-200) ${pct}%)`,
        }}
      />
    </div>
  )
}
