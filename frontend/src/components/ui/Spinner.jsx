import { Loader2 } from 'lucide-react'
import { cn } from '../../lib/utils'

export function Spinner({ className, size = 'size-6' }) {
  return <Loader2 className={cn(size, 'animate-spin text-brand-600', className)} aria-hidden="true" />
}

export function FullPageSpinner({ label = 'Loading…' }) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 text-ink-500">
      <Spinner size="size-8" />
      <p className="text-sm font-medium">{label}</p>
    </div>
  )
}
