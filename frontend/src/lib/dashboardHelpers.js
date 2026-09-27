export function computeStats(reports, user) {
  const totalReports = reports.length

  const categoryCounts = {}
  let sustainabilitySum = 0
  let sustainabilityCount = 0

  for (const report of reports) {
    const category = report.recommendation?.commodity?.category
    if (category) categoryCounts[category] = (categoryCounts[category] || 0) + 1

    const top = report.recommendation?.recommendations?.[0]
    if (top?.sustainability_score != null) {
      sustainabilitySum += top.sustainability_score
      sustainabilityCount += 1
    }
  }

  const topCategoryEntry = Object.entries(categoryCounts).sort((a, b) => b[1] - a[1])[0]

  const memberSinceDate = user?.created_at ? new Date(user.created_at) : null

  return {
    totalReports,
    // Raw category key — StatsGrid translates it via results.category.<key> at render time.
    topCategory: topCategoryEntry ? topCategoryEntry[0] : null,
    avgSustainability: sustainabilityCount ? Math.round(sustainabilitySum / sustainabilityCount) : 0,
    memberSince: memberSinceDate
      ? memberSinceDate.toLocaleDateString(undefined, { month: 'short', year: 'numeric' })
      : '—',
  }
}

/** Buckets reports by their top pick's already-computed sustainability_score
 * — a >=60 display threshold, not a new score. The gap between this app's
 * real scores (10/40 for laminates and non-curbside plastics vs. 80/100 for
 * widely-recyclable and compostable options) falls cleanly around there. */
export function computeRecyclabilityBreakdown(reports) {
  let widelyRecyclable = 0
  let lowerRecyclability = 0

  for (const report of reports) {
    const score = report.recommendation?.recommendations?.[0]?.sustainability_score
    if (score == null) continue
    if (score >= 60) widelyRecyclable += 1
    else lowerRecyclability += 1
  }

  return { widelyRecyclable, lowerRecyclability }
}

/** Buckets reports into the last N weeks (oldest -> newest), filling zero-weeks. */
export function buildWeeklyActivity(reports, weeks = 8) {
  const now = new Date()
  const buckets = []
  for (let i = weeks - 1; i >= 0; i--) {
    const end = new Date(now)
    end.setDate(now.getDate() - i * 7)
    const start = new Date(end)
    start.setDate(end.getDate() - 6)
    buckets.push({ start, end, count: 0 })
  }

  for (const report of reports) {
    const created = new Date(report.created_at)
    const bucket = buckets.find((b) => created >= b.start && created <= b.end)
    if (bucket) bucket.count += 1
  }

  return buckets.map((b) => ({
    label: b.start.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
    count: b.count,
  }))
}
