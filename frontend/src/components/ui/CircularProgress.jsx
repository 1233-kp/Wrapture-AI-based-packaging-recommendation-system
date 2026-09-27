import { motion, useReducedMotion } from 'framer-motion'
import { cn } from '../../lib/utils'

/** Animated circular progress ring, e.g. for a 0-100 sustainability score. */
export function CircularProgress({
  value = 0,
  size = 128,
  strokeWidth = 10,
  color = 'var(--color-brand-600)',
  trackColor = 'var(--color-ink-200)',
  label,
  sublabel,
  className,
}) {
  const reduceMotion = useReducedMotion()
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const clamped = Math.max(0, Math.min(100, value))
  const offset = circumference - (clamped / 100) * circumference

  return (
    <div className={cn('relative inline-flex items-center justify-center', className)} style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} stroke={trackColor} strokeWidth={strokeWidth} fill="none" />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: reduceMotion ? offset : offset }}
          transition={{ duration: reduceMotion ? 0 : 1.1, ease: 'easeOut', delay: 0.15 }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-extrabold text-ink-900 font-display">{label ?? `${Math.round(clamped)}`}</span>
        {sublabel && <span className="text-[11px] font-medium text-ink-500 mt-0.5">{sublabel}</span>}
      </div>
    </div>
  )
}
