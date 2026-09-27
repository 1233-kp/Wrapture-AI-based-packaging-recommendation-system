import { motion } from 'framer-motion'
import { cn } from '../../lib/utils'

export function Card({ className, children, hover = false, as: Comp = 'div', ...props }) {
  const El = hover ? motion.create(Comp) : Comp
  const hoverProps = hover
    ? { whileHover: { y: -4, boxShadow: '0 20px 45px -12px rgb(6 95 70 / 0.18)' }, transition: { duration: 0.2 } }
    : {}
  return (
    <El
      className={cn(
        'rounded-card bg-white border border-ink-200/70 shadow-soft-md',
        className
      )}
      {...hoverProps}
      {...props}
    >
      {children}
    </El>
  )
}

export function CardHeader({ className, children, ...props }) {
  return (
    <div className={cn('p-6 pb-4', className)} {...props}>
      {children}
    </div>
  )
}

export function CardBody({ className, children, ...props }) {
  return (
    <div className={cn('px-6 pb-6', className)} {...props}>
      {children}
    </div>
  )
}

export function CardTitle({ className, children, ...props }) {
  return (
    <h3 className={cn('text-lg font-bold text-ink-900', className)} {...props}>
      {children}
    </h3>
  )
}

export function CardDescription({ className, children, ...props }) {
  return (
    <p className={cn('text-sm text-ink-500 mt-1', className)} {...props}>
      {children}
    </p>
  )
}
