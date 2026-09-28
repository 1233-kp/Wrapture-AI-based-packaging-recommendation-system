import { AnimatePresence, motion } from 'framer-motion'
import { Download, Share, X } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { usePwaInstall } from '../../context/PwaInstallContext'
import { Button } from './Button'

function IosInstructionsModal({ onClose }) {
  const { t } = useTranslation()
  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[100] flex items-end justify-center bg-ink-900/40 p-4 sm:items-center"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, y: 20, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 20, scale: 0.97 }}
          transition={{ duration: 0.2 }}
          className="w-full max-w-sm rounded-2xl bg-white p-5 shadow-soft-md"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-start justify-between gap-3">
            <h2 className="text-base font-bold text-ink-900">{t('pwa.iosInstructionsTitle')}</h2>
            <button
              onClick={onClose}
              aria-label={t('common.close')}
              className="flex size-8 shrink-0 items-center justify-center rounded-lg text-ink-400 hover:bg-ink-100 hover:text-ink-700 cursor-pointer"
            >
              <X className="size-4" aria-hidden="true" />
            </button>
          </div>
          <p className="mt-2 flex items-start gap-2 text-sm text-ink-600">
            <Share className="mt-0.5 size-4 shrink-0 text-brand-600" aria-hidden="true" />
            {t('pwa.iosInstructionsBody')}
          </p>
          <Button className="mt-4 w-full" size="sm" onClick={onClose}>
            {t('pwa.iosInstructionsClose')}
          </Button>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}

export function InstallAppButton({ size = 'sm', variant = 'ghost', className }) {
  const { t } = useTranslation()
  const { canInstall, isIosSafari, promptInstall } = usePwaInstall()
  const [showIosModal, setShowIosModal] = useState(false)

  if (canInstall) {
    return (
      <Button size={size} variant={variant} icon={Download} className={className} onClick={promptInstall}>
        {t('pwa.install')}
      </Button>
    )
  }

  if (isIosSafari) {
    return (
      <>
        <Button size={size} variant={variant} icon={Share} className={className} onClick={() => setShowIosModal(true)}>
          {t('pwa.iosAddToHomeScreen')}
        </Button>
        {showIosModal && <IosInstructionsModal onClose={() => setShowIosModal(false)} />}
      </>
    )
  }

  return null
}
