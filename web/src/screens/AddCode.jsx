import { useState } from 'react'
import { api } from '../api.js'
import { InfoButton, SectionTitle } from '../help.jsx'
import PieceSelect from '../components/PieceSelect.jsx'

/** Add a code: photo capture (phase 6) or typing it in. */
export default function AddCode({ season, onSaved, onToast }) {
  const [form, setForm] = useState({ code_text: '', piece_number: '', private: false })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function save(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const result = await api('/codes', {
        method: 'POST',
        body: {
          code_text: form.code_text,
          piece_number: Number(form.piece_number),
          visibility: form.private ? 'private' : 'shared',
        },
      })
      setForm({ code_text: '', piece_number: '', private: false })
      onToast(`Saved ${result.code.piece_name}`)
      onSaved(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="screen">
      <SectionTitle topic="codeEntry">Add a code</SectionTitle>

      <form className="card form" onSubmit={save}>
        <label htmlFor="code-text">Code</label>
        <input id="code-text" className="code-input" value={form.code_text}
          onChange={(e) => setForm({ ...form, code_text: e.target.value })}
          autoCapitalize="characters" autoCorrect="off" autoComplete="off" spellCheck="false"
          placeholder="e.g. ABCD 1234 EFGH" required />

        <label htmlFor="piece">Game piece</label>
        <PieceSelect id="piece" season={season} value={form.piece_number}
          onChange={(piece_number) => setForm({ ...form, piece_number })} />

        <div className="field-row">
          <label className="check">
            <input type="checkbox" checked={form.private} onChange={(e) => setForm({ ...form, private: e.target.checked })} />
            Keep this code private
          </label>
          <InfoButton topic="privacy" />
        </div>

        {error && <p className="error" role="alert">{error}</p>}
        <button className="btn btn-primary btn-block" disabled={busy}>{busy ? 'Saving…' : 'Save code'}</button>
      </form>
    </div>
  )
}
