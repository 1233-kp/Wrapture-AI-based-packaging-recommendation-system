import { cn } from '../../lib/utils'

const TONES = {
  brand: 'bg-brand-100 text-brand-700',
  teal: 'bg-teal-100 text-teal-700',
  amber: 'bg-amber-100 text-amber-700',
  danger: 'bg-danger-bg text-danger',
  neutral: 'bg-ink-100 text-ink-600',
}

export function Badge({ tone = 'neutral', className, children, icon: Icon, ...props }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-pill px-2.5 py-1 text-xs font-semibold',
        TONES[tone],
        className
      )}
      {...props}
    >
      {Icon && <Icon className="size-3" aria-hidden="true" />}
      {children}
    </span>
  )
}
