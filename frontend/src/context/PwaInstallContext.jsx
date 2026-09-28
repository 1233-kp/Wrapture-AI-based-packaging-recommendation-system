import { createContext, useContext, useEffect, useState } from 'react'

const PwaInstallContext = createContext(null)

function isStandaloneDisplayMode() {
  // iOS Safari never supports the matchMedia query below — it exposes its
  // own non-standard `navigator.standalone` instead.
  return window.matchMedia?.('(display-mode: standalone)').matches || window.navigator.standalone === true
}

function detectIosSafari() {
  const ua = window.navigator.userAgent
  const isIos = /iPad|iPhone|iPod/.test(ua) && !window.MSStream
  // iOS forces every browser onto WebKit, but only Safari's own UI has the
  // Share -> "Add to Home Screen" affordance this instructional link points
  // at — Chrome/Firefox-on-iOS don't expose the same flow, so excluding
  // their UA tokens keeps the link from promising something those browsers
  // can't actually do.
  const isOtherIosBrowser = /CriOS|FxiOS|EdgiOS|OPiOS/.test(ua)
  return isIos && !isOtherIosBrowser
}

export function PwaInstallProvider({ children }) {
  const [deferredPrompt, setDeferredPrompt] = useState(null)
  const [isInstalled, setIsInstalled] = useState(false)

  useEffect(() => {
    setIsInstalled(isStandaloneDisplayMode())

    const handleBeforeInstallPrompt = (event) => {
      // Stops Chrome/Edge from showing their own mini-infobar so the app's
      // own "Install App" button is the only install entry point offered.
      event.preventDefault()
      setDeferredPrompt(event)
    }
    const handleAppInstalled = () => {
      setDeferredPrompt(null)
      setIsInstalled(true)
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
    window.addEventListener('appinstalled', handleAppInstalled)
    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
      window.removeEventListener('appinstalled', handleAppInstalled)
    }
  }, [])

  const promptInstall = async () => {
    if (!deferredPrompt) return null
    deferredPrompt.prompt()
    const choice = await deferredPrompt.userChoice
    // A captured beforeinstallprompt event can only be prompted once,
    // accepted or not — drop it either way so the button hides again
    // rather than firing a second, silently-ignored prompt() call.
    setDeferredPrompt(null)
    if (choice.outcome === 'accepted') setIsInstalled(true)
    return choice
  }

  const value = {
    canInstall: !!deferredPrompt && !isInstalled,
    isInstalled,
    isIosSafari: !isInstalled && detectIosSafari(),
    promptInstall,
  }

  return <PwaInstallContext.Provider value={value}>{children}</PwaInstallContext.Provider>
}

export function usePwaInstall() {
  const ctx = useContext(PwaInstallContext)
  if (!ctx) throw new Error('usePwaInstall must be used within PwaInstallProvider')
  return ctx
}
