import { AnimatePresence, motion } from 'framer-motion'
import { Droplets, Wind } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { localizedName } from '../../lib/utils'
import { Badge } from '../ui/Badge'
import { Card } from '../ui/Card'
import { CircularProgress } from '../ui/CircularProgress'

// Real specs pulled directly from backend/data/packaging_materials.json — not
// invented. sustainability score is computed the same way the live app does,
// via rules.json's sustainability_score_by_recyclability_keyword table
// matched against each material's own recyclability_rating text.
const MATERIALS = [
  {
    id: 'ldpe',
    name: 'LDPE',
    nameHi: 'एलडीपीई (LDPE) फिल्म',
    fullName: 'Low-Density Polyethylene',
    otr: '7000-9000',
    wvtr: '15-20',
    costTier: 'low',
    sustainability: 40,
    useCases: ['Bread bags', 'Produce bags', 'Shrink wrap'],
  },
  {
    id: 'hdpe',
    name: 'HDPE',
    nameHi: 'एचडीपीई (HDPE)',
    fullName: 'High-Density Polyethylene',
    otr: '1500-3000',
    wvtr: '4-10',
    costTier: 'low',
    sustainability: 100,
    useCases: ['Milk jugs', 'Dry goods pouches', 'Rigid bottles'],
  },
  {
    id: 'pet',
    name: 'PET',
    nameHi: 'पीईटी (PET)',
    fullName: 'Polyethylene Terephthalate',
    otr: '50-150',
    wvtr: '15-40',
    costTier: 'medium',
    sustainability: 100,
    useCases: ['Beverage bottles', 'Clamshells', 'Produce trays'],
  },
  {
    id: 'aluminum_foil_laminate',
    name: 'Aluminum Laminate',
    nameHi: 'एल्युमिनियम फॉयल लैमिनेट',
    fullName: 'Multi-layer foil laminate',
    otr: '0-0.1',
    wvtr: '0-0.1',
    costTier: 'high',
    sustainability: 10,
    useCases: ['Retort pouches', 'Spice/sauce sachets', 'Long-life cartons'],
  },
  {
    id: 'pla_biodegradable_film',
    name: 'Biodegradable Film',
    nameHi: 'बायोडिग्रेडेबल (पीएलए) फिल्म',
    fullName: 'Polylactic acid film',
    otr: '100-300',
    wvtr: '10-30',
    costTier: 'high',
    sustainability: 80,
    useCases: ['Eco produce bags', 'Compostable wrap', 'Short-shelf-life snacks'],
  },
]

const COST_TONE = { low: 'brand', medium: 'amber', high: 'danger' }

export function MaterialExplorer() {
  const { t, i18n } = useTranslation()
  const [selectedId, setSelectedId] = useState(MATERIALS[0].id)
  const material = MATERIALS.find((m) => m.id === selectedId)

  return (
    <section id="materials" className="bg-ink-50 py-20 sm:py-28">
      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.5 }}
          className="mx-auto max-w-2xl text-center"
        >
          <h2 className="font-display text-3xl font-extrabold text-ink-900 sm:text-4xl">
            {t('landing.materials.heading')}
          </h2>
          <p className="mt-3 text-ink-500">{t('landing.materials.subhead')}</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-60px' }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="mt-10 flex flex-wrap items-center justify-center gap-2"
        >
          {MATERIALS.map((m) => (
            <button
              key={m.id}
              type="button"
              onClick={() => setSelectedId(m.id)}
              className={`rounded-pill border px-4 py-2 text-sm font-semibold transition-colors ${
                m.id === selectedId
                  ? 'border-brand-600 bg-brand-600 text-white shadow-soft-sm'
                  : 'border-ink-200 bg-white text-ink-600 hover:border-brand-300 hover:text-brand-700'
              }`}
            >
              {localizedName(m.name, m.nameHi, i18n.language)}
            </button>
          ))}
        </motion.div>

        <div className="mt-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={material.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.3 }}
            >
              <Card className="p-6 sm:p-8">
                <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <h3 className="font-display text-xl font-extrabold text-ink-900">
                      {localizedName(material.name, material.nameHi, i18n.language)}
                    </h3>
                    <p className="mt-0.5 text-sm text-ink-400">{material.fullName}</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <Badge tone={COST_TONE[material.costTier]}>
                      {t(`results.costTierValue.${material.costTier}`)}
                    </Badge>
                    <CircularProgress value={material.sustainability} size={64} strokeWidth={5} />
                  </div>
                </div>

                <div className="mt-6 grid grid-cols-1 gap-6 border-t border-ink-100 pt-6 sm:grid-cols-2">
                  <div className="space-y-2.5 text-sm text-ink-600">
                    <div className="flex items-center gap-2">
                      <Wind className="size-4 shrink-0 text-teal-600" aria-hidden="true" />
                      <span className="font-semibold text-ink-700">OTR</span> {material.otr}
                    </div>
                    <div className="flex items-center gap-2">
                      <Droplets className="size-4 shrink-0 text-brand-600" aria-hidden="true" />
                      <span className="font-semibold text-ink-700">WVTR</span> {material.wvtr}
                    </div>
                  </div>
                  <div>
                    <p className="text-xs font-bold uppercase tracking-wide text-ink-400">
                      {t('landing.materials.applications')}
                    </p>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {material.useCases.map((use) => (
                        <span
                          key={use}
                          className="rounded-pill bg-ink-100 px-2.5 py-1 text-xs font-medium text-ink-600"
                        >
                          {use}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </Card>
            </motion.div>
          </AnimatePresence>
        </div>

        <p className="mt-6 text-center text-xs text-ink-400">{t('landing.materials.footnote')}</p>
      </div>
    </section>
  )
}
