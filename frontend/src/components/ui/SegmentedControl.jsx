import { motion } from 'framer-motion'
import { cn } from '../../lib/utils'

export function SegmentedControl({ options, value, onChange, className, name }) {
  return (
    <div
      role="radiogroup"
      aria-label={name}
      className={cn(
        'relative inline-flex w-full rounded-2xl bg-ink-100 p-1 gap-1',
        className
      )}
    >
      {options.map((opt) => {
        const active = opt.value === value
        return (
          <button
            key={opt.value}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(opt.value)}
            className={cn(
              'relative flex-1 rounded-xl px-3 py-2.5 text-sm font-semibold transition-colors cursor-pointer min-h-11',
              active ? 'text-white' : 'text-ink-600 hover:text-ink-900'
            )}
          >
            {active && (
              <motion.span
                layoutId={`segment-active-${name}`}
                className="absolute inset-0 rounded-xl bg-brand-600 shadow-soft-sm"
                transition={{ type: 'spring', stiffness: 500, damping: 35 }}
              />
            )}
            <span className="relative z-10 flex items-center justify-center gap-1.5">
              {opt.icon && <opt.icon className="size-4" aria-hidden="true" />}
              {opt.label}
            </span>
          </button>
        )
      })}
    </div>
  )
}
