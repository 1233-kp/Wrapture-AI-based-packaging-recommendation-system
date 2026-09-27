import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import en from './locales/en.json'
import hi from './locales/hi.json'

export const SUPPORTED_LANGS = ['en', 'hi']
const STORAGE_KEY = 'psa_lang'

function getStoredLang() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return SUPPORTED_LANGS.includes(stored) ? stored : 'en'
  } catch {
    // localStorage can throw in private-browsing/blocked-storage contexts — fall back silently
    return 'en'
  }
}

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    hi: { translation: hi },
  },
  lng: getStoredLang(),
  fallbackLng: 'en',
  interpolation: { escapeValue: false }, // React already escapes
  returnEmptyString: false,
})

export function setLanguage(lang) {
  if (!SUPPORTED_LANGS.includes(lang)) return
  i18n.changeLanguage(lang)
  try {
    localStorage.setItem(STORAGE_KEY, lang)
  } catch {
    // per-viewer convenience only — losing the persisted choice isn't fatal
  }
}

export default i18n
