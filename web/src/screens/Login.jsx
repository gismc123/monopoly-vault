import { useEffect, useState } from 'react'
import { api, saveLogin } from '../api.js'

export default function Login({ onSignedIn }) {
  const [mode, setMode] = useState('signin')
  const [allowSignup, setAllowSignup] = useState(false)
  const [form, setForm] = useState({ name: '', username: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    api('/auth/config').then((c) => setAllowSignup(c.allow_signup)).catch(() => {})
  }, [])

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const result = mode === 'signin'
        ? await api('/auth/login', { method: 'POST', body: { username: form.username, password: form.password } })
        : await api('/auth/register', { method: 'POST', body: form })
      saveLogin(result)
      onSignedIn(result.user)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const signingUp = mode === 'signup'
  return (
    <main className="login">
      <div className="login-brand">
        <img src="/icons/icon-192.png" alt="" width="72" height="72" />
        <h1>Monopoly Vault</h1>
        <p>Pool your household's Monopoly codes and redeem complete sets.</p>
      </div>

      <form className="card form" onSubmit={submit}>
        <h2>{signingUp ? 'Create your account' : 'Sign in'}</h2>
        {signingUp && (
          <label>
            Your name
            <input value={form.name} onChange={update('name')} autoComplete="name" required maxLength={80} />
          </label>
        )}
        <label>
          Username
          <input value={form.username} onChange={update('username')} autoComplete="username"
            autoCapitalize="none" autoCorrect="off" spellCheck="false" required minLength={3} maxLength={40} />
        </label>
        <label>
          Password
          <input type="password" value={form.password} onChange={update('password')} required
            autoComplete={signingUp ? 'new-password' : 'current-password'} minLength={signingUp ? 8 : 1} />
          {signingUp && <span className="hint">At least 8 characters.</span>}
        </label>
        {error && <p className="error" role="alert">{error}</p>}
        <button className="btn btn-primary btn-block" disabled={busy}>
          {busy ? 'Please wait…' : signingUp ? 'Create account' : 'Sign in'}
        </button>
        {allowSignup && (
          <button type="button" className="btn btn-link" onClick={() => { setMode(signingUp ? 'signin' : 'signup'); setError('') }}>
            {signingUp ? 'I already have an account' : 'New here? Create an account'}
          </button>
        )}
      </form>
    </main>
  )
}
