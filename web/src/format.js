// Date helpers. Season dates like "2026-11-22" are calendar days, so parse them as local dates.

export function formatDay(isoDate, options = { month: 'long', day: 'numeric', year: 'numeric' }) {
  const [y, m, d] = isoDate.split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString(undefined, options)
}

export function formatDateTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
}
