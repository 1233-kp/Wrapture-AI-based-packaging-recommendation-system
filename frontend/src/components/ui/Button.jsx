import { motion } from 'framer-motion'
import { Loader2 } from 'lucide-react'
import { cn } from '../../lib/utils'

const VARIANTS = {
  primary:
    'bg-brand-600 text-white shadow-soft-md hover:bg-brand-700 focus-visible:outline-brand-600',
  accent:
    'bg-amber-600 text-white shadow-soft-md hover:bg-amber-700 focus-visible:outline-amber-600',
  teal: 'bg-teal-600 text-white shadow-soft-md hover:bg-teal-700 focus-visible:outline-teal-600',
  secondary:
    'bg-white text-ink-800 border border-ink-200 hover:border-brand-300 hover:bg-brand-50 shadow-soft-sm',
  ghost: 'bg-transparent text-ink-700 hover:bg-ink-100',
  destructive: 'bg-danger text-white hover:bg-red-700 shadow-soft-md',
  outline: 'bg-transparent border border-white/40 text-white hover:bg-white/10',
}

const SIZES = {
  sm: 'text-sm px-3.5 py-2 gap-1.5 rounded-xl',
  md: 'text-sm px-5 py-2.5 gap-2 rounded-xl',
  lg: 'text-base px-7 py-3.5 gap-2.5 rounded-2xl',
}

export function Button({
  as: Comp = 'button',
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  icon: Icon,
  iconPosition = 'left',
  className,
  children,
  ...props
}) {
  const MotionComp = motion.create ? motion.create(Comp) : motion(Comp)
  return (
    <MotionComp
      whileTap={{ scale: 0.97 }}
      whileHover={{ y: -1 }}
      transition={{ type: 'spring', stiffness: 400, damping: 25 }}
      disabled={disabled || loading}
      className={cn(
        'inline-flex items-center justify-center font-semibold cursor-pointer select-none transition-colors duration-200',
        'disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none',
        VARIANTS[variant],
        SIZES[size],
        className
      )}
      {...props}
    >
      {loading ? (
        <Loader2 className="size-4 animate-spin" aria-hidden="true" />
      ) : (
        Icon && iconPosition === 'left' && <Icon className="size-4" aria-hidden="true" />
      )}
      {children}
      {!loading && Icon && iconPosition === 'right' && <Icon className="size-4" aria-hidden="true" />}
    </MotionComp>
  )
}
