import { lazy, Suspense, useState } from 'react'
import { Hero3DErrorBoundary } from './Hero3DErrorBoundary'
import { RotatingMaterialShowcase } from './RotatingMaterialShowcase'

// Code-split so the ~600kb three.js/R3F chunk never blocks the initial
// landing-page load — it's fetched in the background only after the static
// card has already painted, and only on devices that report WebGL support.
const HeroScene = lazy(() => import('./HeroScene'))

function supportsWebGL() {
  try {
    const canvas = document.createElement('canvas')
    return !!(canvas.getContext('webgl2') || canvas.getContext('webgl'))
  } catch {
    return false
  }
}

// Matches the `sm` breakpoint used everywhere else in this design system —
// below it, the scene drops particles/antialiasing and caps dpr at 1.
function isMobileViewport() {
  return window.matchMedia('(max-width: 640px)').matches
}

/**
 * Progressive-enhancement wrapper for the hero visual. Always paints the
 * static RotatingMaterialShowcase first (fast, zero extra JS), then swaps in
 * the 3D scene only if: the browser reports WebGL support, the lazy chunk
 * loads successfully, and it doesn't throw while mounting. Any failure at
 * any stage — including on real mobile browsers this couldn't be tested on
 * directly — resolves back to the exact same static card, so there's no
 * scenario where this regresses the Phase 1 hero.
 */
export function HeroVisual() {
  const [canUse3D] = useState(() => supportsWebGL())
  const [simplified] = useState(() => isMobileViewport())

  return (
    <div className="mx-auto flex min-h-70 w-full max-w-sm items-center justify-center sm:min-h-75">
      {canUse3D ? (
        <Hero3DErrorBoundary fallback={<RotatingMaterialShowcase />}>
          <Suspense fallback={<RotatingMaterialShowcase />}>
            <HeroScene simplified={simplified} />
          </Suspense>
        </Hero3DErrorBoundary>
      ) : (
        <RotatingMaterialShowcase />
      )}
    </div>
  )
}
