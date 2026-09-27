import { AnimatePresence, motion } from 'framer-motion'
import { ChevronDown } from 'lucide-react'
import { useState } from 'react'
import { Card } from '../ui/Card'

export function FaqAccordionItem({ question, answer }) {
  const [open, setOpen] = useState(false)

  return (
    <Card className="overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex w-full cursor-pointer items-center justify-between gap-3 p-4 text-left"
      >
        <span className="text-sm font-bold text-ink-900">{question}</span>
        <ChevronDown
          className={`size-4 shrink-0 text-ink-400 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
          aria-hidden="true"
        />
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <p className="px-4 pb-4 text-sm text-ink-500">{answer}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  )
}
