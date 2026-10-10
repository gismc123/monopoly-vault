import { useCallback, useEffect, useState } from 'react'
import { api, clearLogin, savedUser, timeZone } from './api.js'
import { textOn } from './colors.js'
import { formatDay } from './format.js'
import { HelpProvider, InfoButton } from './help.jsx'
import Modal from './components/Modal.jsx'
import { BoardIcon, CameraIcon, ListIcon, StarIcon, VaultIcon } from './components/icons.jsx'
import Login from './screens/Login.jsx'
import Board from './screens/Board.jsx'
import Codes from './screens/Codes.jsx'
import AddCode from './screens/AddCode.jsx'
import Vault from './screens/Vault.jsx'

export default function App() {
  const [user, setUser] = useState(savedUser)
  const [season, setSeason] = useState(null)

  useEffect(() => {
    api('/season').then(setSeason).catch(() => {})
    const onSignedOut = () => setUser(null)
    window.addEventListener('mv:signed-out', onSignedOut)
    return () => window.removeEventListener('mv:signed-out', onSignedOut)
  }, [])

  return (
    <HelpProvider season={season}>
      {!user && <Login onSignedIn={setUser} />}
      {user && season && <Shell user={user} season={season} onSignOut={() => { clearLogin(); setUser(null) }} />}
      {user && !season && <p className="loading">Loading…</p>}
    </HelpProvider>
  )
}

const TABS = [
  { id: 'board', label: 'Board', Icon: BoardIcon },
  { id: 'codes', label: 'Codes', Icon: ListIcon },
  { id: 'add', label: 'Add code', Icon: CameraIcon, primary: true },
  { id: 'vault', label: 'Vault', Icon: VaultIcon },
]

function Shell({ user, season, onSignOut }) {
  const [tab, setTab] = useState('board')
  const [version, setVersion] = useState(0) // bump to make screens reload their data
  const [today, setToday] = useState(null)
  const [toast, setToast] = useState(null)
  const [completedSets, setCompletedSets] = useState([])

  const onChanged = useCallback(() => setVersion((v) => v + 1), [])

  const onToast = useCallback((message, kind = 'ok') => {
    const id = Date.now()
    setToast({ id, message, kind })
    setTimeout(() => setToast((t) => (t?.id === id ? null : t)), 3500)
  }, [])

  useEffect(() => {
    api(`/season/today?tz=${encodeURIComponent(timeZone())}`).then(setToday).catch(() => {})
  }, [version])

  function onSaved(result) {
    onChanged()
    // One alert per set, even if it completed for both "mine" and "household".
    const unique = [...new Map(result.completed_sets.map((s) => [s.id, s])).values()]
    if (unique.length) setCompletedSets(unique)
  }

  const screenProps = { season, me: user, version, onChanged, onToast }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <img src="/icons/icon-192.png" alt="" width="28" height="28" />
          <span>Monopoly Vault</span>
        </div>
        <div className="season-chip">
          {season.year} season
          <InfoButton topic="season" />
        </div>
      </header>

      <ReminderBar season={season} today={today} />

      <main className="content">
        {tab === 'board' && <Board {...screenProps} onGoToVault={() => setTab('vault')} />}
        {tab === 'codes' && <Codes {...screenProps} />}
        {tab === 'add' && <AddCode {...screenProps} onSaved={onSaved} />}
        {tab === 'vault' && <Vault {...screenProps} onSignOut={onSignOut} />}
      </main>

      <nav className="tabbar" aria-label="Main">
        {TABS.map(({ id, label, Icon, primary }) => (
          <button key={id} type="button" className={`tab ${primary ? 'tab-primary' : ''}`}
            aria-current={tab === id ? 'page' : undefined} onClick={() => setTab(id)}>
            <span className="tab-icon"><Icon size={primary ? 28 : 24} /></span>
            <span className="tab-label">{label}</span>
          </button>
        ))}
      </nav>

      {toast && <div className={`toast toast-${toast.kind}`} role="status">{toast.message}</div>}

      {completedSets.length > 0 && (
        <Modal title="Set complete!" onClose={() => setCompletedSets([])} className="celebrate">
          <StarIcon size={40} />
          <p>That code completed {completedSets.length === 1 ? 'a set' : 'these sets'}:</p>
          <div className="ready-chips">
            {completedSets.map((s) => (
              <span key={s.id} className="set-chip" style={{ background: s.color, color: textOn(s.color) }}>
                {s.name}{s.scope === 'mine' ? ' (yours)' : ''}
              </span>
            ))}
          </div>
          <p className="muted small">It's ready to redeem. Decide together who redeems it.</p>
          <button type="button" className="btn btn-primary btn-block"
            onClick={() => { setCompletedSets([]); setTab('board') }}>See the board</button>
        </Modal>
      )}
    </div>
  )
}

/** McDonald's limits: 8 entries a day per account, and the prize claim deadline. */
function ReminderBar({ season, today }) {
  const used = today?.entries_today ?? 0
  const limit = season.daily_entry_limit
  return (
    <div className={`reminder ${used >= limit ? 'reminder-warn' : ''}`}>
      <span>Today: <strong>{used}/{limit}</strong> entries</span>
      <span aria-hidden="true">·</span>
      <span>Claims close {formatDay(season.claim_deadline, { month: 'short', day: 'numeric' })}</span>
      <InfoButton topic="limits" />
    </div>
  )
}
