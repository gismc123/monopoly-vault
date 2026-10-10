import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { InfoButton, SectionTitle } from '../help.jsx'
import CodeCard from '../components/CodeCard.jsx'

const FILTERS = [['', 'All'], ['available', 'Available'], ['pending', 'Pending'], ['used', 'Used']]

/** Every code I can see: mine plus my vault-mates' shared codes. */
export default function Codes({ season, me, version, onChanged, onToast }) {
  const [status, setStatus] = useState('available')
  const [onlyMine, setOnlyMine] = useState(false)
  const [codes, setCodes] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const params = new URLSearchParams({ scope: onlyMine ? 'mine' : 'all' })
    if (status) params.set('status', status)
    api(`/codes?${params}`)
      .then((c) => { setCodes(c); setError('') })
      .catch((e) => setError(e.message))
  }, [status, onlyMine, version])

  const colorOf = Object.fromEntries(season.sets.map((s) => [s.id, s.color]))

  return (
    <div className="screen">
      <SectionTitle topic="copy">Codes</SectionTitle>

      <div className="filter-row">
        <div className="chips" role="group" aria-label="Filter by status">
          {FILTERS.map(([value, label]) => (
            <button key={value} type="button" className="chip" aria-pressed={status === value} onClick={() => setStatus(value)}>
              {label}
            </button>
          ))}
        </div>
        <InfoButton topic="status" />
      </div>

      <div className="filter-row">
        <label className="check">
          <input type="checkbox" checked={onlyMine} onChange={(e) => setOnlyMine(e.target.checked)} />
          Only my codes
        </label>
        <InfoButton topic="privacy" />
      </div>

      {error && <p className="error" role="alert">{error}</p>}
      {codes?.length === 0 && <p className="empty">No codes here yet.</p>}
      <div className="code-list">
        {codes?.map((c) => (
          <CodeCard key={c.id} code={c} color={colorOf[c.set_id]} me={me.id} onChanged={onChanged} onToast={onToast} />
        ))}
      </div>
    </div>
  )
}
