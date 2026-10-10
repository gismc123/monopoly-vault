import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { SectionTitle } from '../help.jsx'
import { CopyIcon, UsersIcon } from '../components/icons.jsx'

/** Create or join the household vault, and the signed-in account. */
export default function Vault({ me, season, version, onChanged, onToast, onSignOut }) {
  const [vault, setVault] = useState(undefined) // undefined = loading, null = not in one

  useEffect(() => {
    api('/vault').then(setVault).catch((e) => onToast(e.message, 'error'))
  }, [version])

  return (
    <div className="screen">
      <SectionTitle topic="vault">Your vault</SectionTitle>

      {vault === undefined && <p className="muted">Loading…</p>}
      {vault === null && <NoVault season={season} onJoined={(v) => { setVault(v); onChanged() }} onToast={onToast} />}
      {vault && <VaultDetails vault={vault} me={me} onLeft={() => { setVault(null); onChanged() }} onToast={onToast} />}

      <h2 className="spaced">Account</h2>
      <div className="card">
        <p>Signed in as <strong>{me.name}</strong> <span className="muted">(@{me.username})</span></p>
        <button type="button" className="btn btn-secondary btn-block" onClick={onSignOut}>Sign out</button>
      </div>
    </div>
  )
}

function NoVault({ season, onJoined, onToast }) {
  const [name, setName] = useState('')
  const [invite, setInvite] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e, request) {
    e.preventDefault()
    setBusy(true)
    try {
      onJoined(await request())
    } catch (err) {
      onToast(err.message, 'error')
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <p>You're not in a vault for the {season.year} season. Create one for your household, or join one with an
        invite code.</p>

      <form className="card form" onSubmit={(e) => submit(e, () => api('/vault', { method: 'POST', body: { name } }))}>
        <h3>Create a vault</h3>
        <label>
          Vault name
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Santos family" required maxLength={80} />
        </label>
        <button className="btn btn-primary btn-block" disabled={busy}>Create vault</button>
      </form>

      <form className="card form"
        onSubmit={(e) => submit(e, () => api('/vault/join', { method: 'POST', body: { invite_code: invite } }))}>
        <h3>Join a vault</h3>
        <label>
          Invite code
          <input className="code-input" value={invite} onChange={(e) => setInvite(e.target.value)}
            autoCapitalize="characters" autoCorrect="off" autoComplete="off" spellCheck="false"
            required minLength={4} maxLength={12} />
        </label>
        <button className="btn btn-primary btn-block" disabled={busy}>Join vault</button>
      </form>
    </>
  )
}

function VaultDetails({ vault, me, onLeft, onToast }) {
  async function copyInvite() {
    try {
      await navigator.clipboard.writeText(vault.invite_code)
      onToast('Invite code copied')
    } catch {
      onToast('Press and hold the code to copy it', 'error')
    }
  }

  async function leave() {
    if (!window.confirm(`Leave "${vault.name}"? Your codes will no longer be shared with its members.`)) return
    try {
      await api('/vault/leave', { method: 'POST' })
      onToast('You left the vault')
      onLeft()
    } catch (err) {
      onToast(err.message, 'error')
    }
  }

  return (
    <>
      <div className="card vault-card">
        <h3>{vault.name}</h3>
        <p className="muted small">{vault.campaign_year} season</p>

        <p className="label">Invite code</p>
        <div className="invite-row">
          <span className="code-text invite-code">{vault.invite_code}</span>
          <button type="button" className="btn btn-secondary" onClick={copyInvite}><CopyIcon size={18} /> Copy</button>
        </div>
        <p className="hint">Send this to family members so they can join.</p>
      </div>

      <div className="card">
        <h3 className="with-icon"><UsersIcon size={20} /> Members</h3>
        <ul className="members">
          {vault.members.map((m) => (
            <li key={m.id}>{m.name}{m.id === me.id && <span className="muted"> (you)</span>}</li>
          ))}
        </ul>
      </div>

      <button type="button" className="btn btn-danger btn-block" onClick={leave}>Leave vault</button>
    </>
  )
}
