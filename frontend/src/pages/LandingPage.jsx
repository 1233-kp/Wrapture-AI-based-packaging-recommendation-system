import Lenis from 'lenis'
import 'lenis/dist/lenis.css'
import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { AIAnalysisFlow } from '../components/landing/AIAnalysisFlow'
import { CTASection } from '../components/landing/CTASection'
import { Hero } from '../components/landing/Hero'
import { Impact } from '../components/landing/Impact'
import { MaterialExplorer } from '../components/landing/MaterialExplorer'
import { RecommendationSimulation } from '../components/landing/RecommendationSimulation'
import { StatsStrip } from '../components/landing/StatsStrip'
import { Footer } from '../components/layout/Footer'
import { Navbar } from '../components/layout/Navbar'

export default function LandingPage() {
  const { t } = useTranslation()
  useEffect(() => {
    document.title = t('landing.pageTitle')
  }, [t])

  // Scoped to this page only — mounted on entry, destroyed on exit — so the
  // authenticated /app/* routes keep their native scroll untouched.
  // `anchors: true` makes Lenis handle the existing `<a href="#section">`
  // nav/CTA links itself; `respectReducedMotion` (default true) makes it
  // honor prefers-reduced-motion on its own.
  useEffect(() => {
    const lenis = new Lenis({ autoRaf: true, anchors: true, duration: 1.1 })
    return () => lenis.destroy()
  }, [])

  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      <main>
        <Hero />
        <StatsStrip />
        <AIAnalysisFlow />
        <RecommendationSimulation />
        <MaterialExplorer />
        <Impact />
        <CTASection />
      </main>
      <Footer />
    </div>
  )
}
