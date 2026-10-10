import { SectionTitle } from '../help.jsx'

/** Vault membership (phase 5) and account. */
export default function Vault({ me, onSignOut }) {
  return (
    <div className="screen">
      <SectionTitle topic="vault">Your vault</SectionTitle>
      <p className="muted">Coming in the next phase.</p>

      <h2 className="spaced">Account</h2>
      <div className="card">
        <p>Signed in as <strong>{me.name}</strong> <span className="muted">(@{me.username})</span></p>
        <button type="button" className="btn btn-secondary btn-block" onClick={onSignOut}>Sign out</button>
      </div>
    </div>
  )
}
