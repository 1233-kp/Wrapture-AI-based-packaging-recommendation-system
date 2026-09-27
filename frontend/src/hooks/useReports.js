import { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'

export function useReports({ limit = 100 } = {}) {
  const { t } = useTranslation()
  const { accessToken } = useAuth()
  const [reports, setReports] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const refetch = useCallback(() => {
    if (!accessToken) return
    setLoading(true)
    api
      .listReports(accessToken, { limit, offset: 0 })
      .then((data) => {
        setReports(data.reports)
        setTotal(data.total)
        setError(null)
      })
      .catch((err) => setError(err.message || t('common.loadReportsError')))
      .finally(() => setLoading(false))
  }, [accessToken, limit, t])

  useEffect(() => {
    refetch()
  }, [refetch])

  const deleteReport = useCallback(
    async (reportId) => {
      // Optimistic removal — snappier than waiting on a refetch, and reverted
      // if the delete call actually fails.
      const previous = reports
      setReports((rs) => rs.filter((r) => r.id !== reportId))
      setTotal((t) => Math.max(0, t - 1))
      try {
        await api.deleteReport(accessToken, reportId)
      } catch (err) {
        setReports(previous)
        setTotal(previous.length)
        throw err
      }
    },
    [accessToken, reports]
  )

  return { reports, total, loading, error, refetch, deleteReport }
}
