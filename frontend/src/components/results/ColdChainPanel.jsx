import { motion } from 'framer-motion'
import { AlertTriangle, CheckCircle2, Snowflake, Thermometer } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../../context/AuthContext'
import { api } from '../../lib/api'
import { formatDateTime } from '../../lib/utils'
import { StorageTypeCards } from '../recommend/StorageTypeCards'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Card } from '../ui/Card'

/**
 * Manual entry only — no IoT/sensor integration. Logs a temperature
 * excursion against this saved report and shows the recalculated remaining
 * shelf life, reusing the same Q10 model as the rest of the app
 * (engine/shelf_life.py via engine/cold_chain.py on the backend). Every
 * submission creates a new record — it never overwrites report history.
 */
export function ColdChainPanel({ reportId }) {
  const { t, i18n } = useTranslation()
  const { accessToken } = useAuth()
  const [temperature, setTemperature] = useState(25)
  const [duration, setDuration] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [events, setEvents] = useState([])
  const [loadingEvents, setLoadingEvents] = useState(true)

  useEffect(() => {
    api
      .listColdChainEvents(accessToken, reportId)
      .then((data) => setEvents(data.events))
      .catch(() => {})
      .finally(() => setLoadingEvents(false))
  }, [accessToken, reportId])

  const handleSubmit = async (e) => {
    e.preventDefault()
    const durationHours = Number(duration)
    if (!duration || Number.isNaN(durationHours) || durationHours < 0) return

    setSubmitting(true)
    setError(null)
    try {
      const data = await api.logColdChainEvent(accessToken, reportId, {
        temperature_reached_c: temperature,
        duration_hours: durationHours,
        lang: i18n.language,
      })
      setResult(data)
      setEvents((prev) => [data.event, ...prev])
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Card className="p-6">
      <div className="flex items-center gap-2">
        <span className="flex size-9 items-center justify-center rounded-xl bg-teal-100 text-teal-700">
          <Snowflake className="size-4" aria-hidden="true" />
        </span>
        <div>
          <h2 className="text-base font-bold text-ink-900">{t('results.coldChainTitle')}</h2>
          <p className="text-xs text-ink-400">{t('results.coldChainSubhead')}</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="mt-5">
        <StorageTypeCards value={temperature} onChange={setTemperature} />

        <div className="mt-4">
          <label htmlFor="excursion-duration" className="mb-2 block text-sm font-semibold text-ink-800">
            {t('results.coldChainDurationLabel')}
          </label>
          <input
            id="excursion-duration"
            type="number"
            min="0"
            step="0.5"
            value={duration}
            onChange={(e) => setDuration(e.target.value)}
            placeholder={t('results.coldChainDurationPlaceholder')}
            className="min-h-11 w-full max-w-xs rounded-xl border border-ink-200 bg-white px-4 text-sm shadow-soft-sm focus:border-brand-400 focus:outline-none"
          />
        </div>

        <Button type="submit" icon={Thermometer} loading={submitting} disabled={!duration} className="mt-4">
          {t('results.coldChainSubmit')}
        </Button>
      </form>

      {error && <p className="mt-3 text-sm font-medium text-danger">{error}</p>}

      {result && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className={`mt-5 rounded-xl border p-4 ${
            result.event.action_urgent ? 'border-danger bg-danger-bg' : 'border-brand-200 bg-brand-50'
          }`}
        >
          <div className="flex items-center gap-2">
            {result.event.action_urgent ? (
              <AlertTriangle className="size-4 shrink-0 text-danger" aria-hidden="true" />
            ) : (
              <CheckCircle2 className="size-4 shrink-0 text-brand-600" aria-hidden="true" />
            )}
            <p className={`text-sm font-bold ${result.event.action_urgent ? 'text-danger' : 'text-brand-800'}`}>
              {result.action_message}
            </p>
          </div>
          <p className="mt-2 text-xs text-ink-600">
            {t('results.coldChainRemaining', {
              days: result.event.remaining_shelf_life_days,
            })}
          </p>
          <p className="mt-2 text-xs text-ink-500">{result.explanation}</p>
          <p className="mt-2 text-[11px] text-ink-400">{result.disclaimer}</p>
        </motion.div>
      )}

      {!loadingEvents && events.length > 0 && (
        <div className="mt-6 border-t border-ink-100 pt-4">
          <p className="text-xs font-bold uppercase tracking-wide text-ink-400">{t('results.coldChainHistory')}</p>
          <ul className="mt-3 space-y-2">
            {events.map((ev) => (
              <li
                key={ev.id}
                className="flex items-center justify-between gap-3 rounded-lg border border-ink-100 bg-ink-50 px-3 py-2 text-xs"
              >
                <span className="text-ink-600">
                  {t('results.coldChainEventSummary', { temp: ev.temperature_reached_c, hours: ev.duration_hours })}
                </span>
                <div className="flex shrink-0 items-center gap-2">
                  <Badge tone={ev.action_urgent ? 'danger' : 'brand'}>
                    {ev.remaining_shelf_life_days}
                    {t('results.coldChainDaysShort')}
                  </Badge>
                  <span className="text-[10px] text-ink-400">{formatDateTime(ev.created_at)}</span>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  )
}
