import { clsx } from 'clsx'

export function cn(...inputs) {
  return clsx(inputs)
}

export function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function formatDateTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

export function titleCase(str) {
  if (!str) return ''
  return str.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

/** Picks the Hindi display name when Hindi is active and one exists, otherwise the
 * English name — the underlying id always stays English regardless of language,
 * this only affects what's shown to the viewer. Used for commodity/material names
 * everywhere they're rendered as a heading/label. */
export function localizedName(nameEn, nameHi, lang) {
  return lang === 'hi' && nameHi ? nameHi : nameEn
}

export const FIT_COLOR = {
  good: 'text-brand-700 bg-brand-100',
  partial: 'text-amber-700 bg-amber-100',
  poor: 'text-danger bg-danger-bg',
  not_applicable: 'text-ink-500 bg-ink-100',
}
