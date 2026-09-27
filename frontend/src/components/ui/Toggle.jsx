import { motion } from 'framer-motion'
import { cn } from '../../lib/utils'

export function Toggle({ checked, onChange, label, description, id }) {
  return (
    <label htmlFor={id} className="flex items-center justify-between gap-4 cursor-pointer">
      {(label || description) && (
        <span className="flex flex-col">
          {label && <span className="text-sm font-semibold text-ink-800">{label}</span>}
          {description && <span className="text-xs text-ink-500">{description}</span>}
        </span>
      )}
      <button
        id={id}
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={cn(
          'relative inline-flex h-7 w-12 shrink-0 items-center rounded-pill transition-colors duration-200 cursor-pointer',
          checked ? 'bg-brand-600' : 'bg-ink-300'
        )}
      >
        <motion.span
          layout
          transition={{ type: 'spring', stiffness: 500, damping: 30 }}
          className="size-5 rounded-full bg-white shadow-soft-sm"
          style={{ marginLeft: checked ? 26 : 4 }}
        />
      </button>
    </label>
  )
}
