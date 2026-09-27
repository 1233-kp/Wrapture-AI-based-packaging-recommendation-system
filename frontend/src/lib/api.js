const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

async function request(path, { method = 'GET', body, token, params } = {}) {
  const url = new URL(API_BASE_URL + path)
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') url.searchParams.set(key, value)
    })
  }

  const headers = { 'Content-Type': 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(url, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  let data = null
  try {
    data = await res.json()
  } catch {
    // no/invalid JSON body — fine for e.g. 204s
  }

  if (!res.ok) {
    const detail = data?.detail
    const message =
      typeof detail === 'string' ? detail : detail?.message || res.statusText || 'Request failed'
    const error = new Error(message)
    error.status = res.status
    error.data = data
    throw error
  }

  return data
}

export const api = {
  // -- public --
  recommendDetailed: (payload) => request('/recommend/detailed', { method: 'POST', body: payload }),
  commodities: () => request('/commodities'),
  materials: () => request('/materials'),
  faqs: () => request('/faq'),
  matchFaq: (query) => request('/faq/match', { method: 'POST', body: { query } }),
  searchCommodities: (q) => request('/commodities/search', { params: { q } }),
  matchCommodity: (query) => request('/commodities/match', { method: 'POST', body: { query } }),
  estimateTransportDays: (source, destination) =>
    request('/logistics/estimate-transport-days', { method: 'POST', body: { source, destination } }),
  publicReport: (reportId) => request(`/reports/${reportId}/public`),
  qrCodeUrl: (reportId) => `${API_BASE_URL}/reports/${reportId}/qrcode`,

  // -- protected (require a Supabase access token) --
  me: (token) => request('/me', { token }),
  getProfile: (token) => request('/profile', { token }),
  updateProfile: (token, patch) => request('/profile', { method: 'PATCH', body: patch, token }),
  listReports: (token, { limit = 20, offset = 0 } = {}) =>
    request('/reports', { token, params: { limit, offset } }),
  saveReport: (token, payload) => request('/reports', { method: 'POST', body: payload, token }),
  deleteReport: (token, reportId) => request(`/reports/${reportId}`, { method: 'DELETE', token }),
  submitReportFeedback: (token, reportId, outcome) =>
    request(`/reports/${reportId}/feedback`, { method: 'PATCH', body: { outcome }, token }),
  logColdChainEvent: (token, reportId, { temperature_reached_c, duration_hours, lang }) =>
    request(`/reports/${reportId}/cold-chain-event`, {
      method: 'POST',
      body: { temperature_reached_c, duration_hours, lang },
      token,
    }),
  listColdChainEvents: (token, reportId) => request(`/reports/${reportId}/cold-chain-events`, { token }),

  async downloadReportPdf(token, reportId, filename) {
    const res = await fetch(`${API_BASE_URL}/reports/${reportId}/export`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!res.ok) throw new Error(`Export failed (HTTP ${res.status})`)
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename || `wrapture-report-${reportId}.pdf`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  },
}

export { API_BASE_URL }
