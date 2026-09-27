import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { FaqContent } from '../components/faq/FaqContent'
import { Footer } from '../components/layout/Footer'
import { Navbar } from '../components/layout/Navbar'

/**
 * Public marketing-site page (Navbar/Footer chrome, like the landing page) —
 * FAQ content is aimed at prospective users/judges deciding whether to sign
 * up. The same content/widget is also reachable from inside the app shell
 * at /app/faq (see AppFaqPage.jsx) — both render the shared <FaqContent />,
 * nothing is duplicated between them.
 */
export default function FaqPage() {
  const { t } = useTranslation()
  useEffect(() => {
    document.title = t('faq.pageTitle')
  }, [t])

  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      <main className="mx-auto max-w-3xl px-4 pt-28 pb-20 sm:px-6 sm:pt-32 lg:px-8">
        <FaqContent />
      </main>
      <Footer />
    </div>
  )
}
