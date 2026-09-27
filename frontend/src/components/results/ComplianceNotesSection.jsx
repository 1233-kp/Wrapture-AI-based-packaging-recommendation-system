import { AnimatePresence, motion } from 'framer-motion'
import { ChevronDown, Scale, ShieldAlert } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Badge } from '../ui/Badge'
import { Card } from '../ui/Card'

const CONFIDENCE_TONE = { high: 'brand', medium: 'amber', low: 'amber' }

/**
 * "Regulatory Considerations" — collapsible, omitted entirely when there's
 * nothing to show (compliance_notes is commonly empty, e.g. for glass).
 * Purely informational flags from a small rule set (backend/data/
 * compliance_rules.json) — not a certified compliance check. Note the rule
 * text itself (description/reference/disclaimer) comes from the backend and
 * is currently English-only regardless of the UI language toggle; only this
 * section's own chrome (heading, counts) is translated.
 */
export function ComplianceNotesSection({ notes, disclaimer, defaultOpen = false }) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(defaultOpen)

  if (!notes || notes.length === 0) return null

  return (
    <Card>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full cursor-pointer items-center justify-between p-6 text-left"
      >
        <div className="flex items-center gap-3">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-amber-100 text-amber-700">
            <Scale className="size-4.5" aria-hidden="true" />
          </div>
          <div>
            <h3 className="text-base font-bold text-ink-900">{t('results.complianceHeading')}</h3>
            <p className="mt-0.5 text-xs text-ink-500">{t('results.complianceCount', { count: notes.length })}</p>
          </div>
        </div>
        <ChevronDown className={`size-5 shrink-0 text-ink-400 transition-transform ${open ? 'rotate-180' : ''}`} aria-hidden="true" />
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="overflow-hidden"
          >
            <div className="px-6 pb-6">
              <div className="divide-y divide-ink-100">
                {notes.map((note) => (
                  <div key={note.rule_id} className="py-3.5">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge tone={CONFIDENCE_TONE[note.confidence] ?? 'neutral'}>
                        {t(`results.confidence.${note.confidence}`, { defaultValue: note.confidence })}
                      </Badge>
                    </div>
                    <p className="mt-1.5 text-sm text-ink-700">{note.description}</p>
                    <p className="mt-1 text-xs text-ink-400">
                      {t('results.complianceReference', { reference: note.general_reference })}
                    </p>
                  </div>
                ))}
              </div>

              {disclaimer && (
                <div className="mt-4 flex items-start gap-2.5 rounded-xl border border-amber-200 bg-amber-50 p-4">
                  <ShieldAlert className="mt-0.5 size-4 shrink-0 text-amber-600" aria-hidden="true" />
                  <p className="text-xs leading-relaxed text-amber-800">{disclaimer}</p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  )
}
