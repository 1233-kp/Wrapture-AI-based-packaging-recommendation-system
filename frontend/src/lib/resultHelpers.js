import { Droplets, Leaf, Package, PiggyBank, Recycle, Sprout, Wind } from 'lucide-react'

export const DIMENSION_ICON = {
  moisture_barrier: Droplets,
  oxygen_barrier: Wind,
  respiration_compatibility: Sprout,
  respiration_packaging_boost: Leaf,
  category_fit: Package,
  cost: PiggyBank,
  sustainability: Recycle,
}

const FIT_SCORE = { good: 100, partial: 60, poor: 20, not_applicable: 75 }
const COST_TIER_SCORE = { low: 100, medium: 60, high: 30 }

/** Builds 0-100 axes for a Recharts radar comparing up to 3 recommendation options.
 * `t` is an i18next translation function — axis labels are translated here since
 * they become object keys in the chart data, not JSX, so they can't be translated
 * at render time the way a label prop can. Pass recommendations with `material_name`
 * already set to whichever display name (English or Hindi) the caller wants shown. */
export function buildRadarData(recommendations, t) {
  const barrierDims = new Set(['moisture_barrier', 'oxygen_barrier', 'respiration_compatibility'])
  const maxShelfLife = Math.max(
    ...recommendations.map((r) => r.estimated_shelf_life_days ?? 0),
    0.0001
  )

  const perOption = recommendations.map((rec) => {
    const barrierFits = rec.match_breakdown.filter((m) => barrierDims.has(m.dimension) && m.fit !== 'not_applicable')
    const barrierAvg = barrierFits.length
      ? barrierFits.reduce((sum, m) => sum + FIT_SCORE[m.fit], 0) / barrierFits.length
      : 75
    return {
      material_name: rec.material_name,
      barrier: Math.round(barrierAvg),
      cost: COST_TIER_SCORE[rec.cost_tier] ?? 50,
      sustainability: Math.round(rec.sustainability_score),
      durability: Math.round(((rec.estimated_shelf_life_days ?? 0) / maxShelfLife) * 100),
    }
  })

  const axes = [
    t('results.radarAxis.barrier'),
    t('results.radarAxis.cost'),
    t('results.radarAxis.sustainability'),
    t('results.radarAxis.durability'),
  ]
  const keys = ['barrier', 'cost', 'sustainability', 'durability']

  return axes.map((axis, i) => {
    const row = { axis }
    perOption.forEach((opt) => {
      row[opt.material_name] = opt[keys[i]]
    })
    return row
  })
}

export const RADAR_COLORS = ['var(--color-brand-600)', 'var(--color-teal-600)', 'var(--color-amber-600)']
