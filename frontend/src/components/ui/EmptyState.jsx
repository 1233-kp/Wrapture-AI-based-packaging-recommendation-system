import { motion } from 'framer-motion'

export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="flex flex-col items-center justify-center text-center py-16 px-6 rounded-card border border-dashed border-ink-200 bg-ink-50/50"
    >
      {Icon && (
        <div className="mb-4 flex size-14 items-center justify-center rounded-2xl bg-brand-100 text-brand-600">
          <Icon className="size-7" aria-hidden="true" />
        </div>
      )}
      <h3 className="text-base font-bold text-ink-900">{title}</h3>
      {description && <p className="mt-1.5 max-w-sm text-sm text-ink-500">{description}</p>}
      {action && <div className="mt-5">{action}</div>}
    </motion.div>
  )
}
