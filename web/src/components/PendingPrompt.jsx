import { useState } from 'react'
import { api } from '../api.js'
import { formatDateTime } from '../format.js'
import { InfoButton } from '../help.jsx'
import Modal from './Modal.jsx'
import { prettyCode } from './CodeCard.jsx'

/**
 * "In your last session you copied this code. Did you submit it?"
 * Asks about one code at a time. "Ask me later" keeps them Pending.
 */
export default function PendingPrompt({ codes, season, onDone, onToast }) {
  const [index, setIndex] = useState(0)
  const [busy, setBusy] = useState(false)
  const code = codes[index]
  const color = season.sets.find((s) => s.id === code.set_id)?.color

  async function answer(submitted) {
    setBusy(true)
    try {
      await api(`/codes/${code.id}/confirm`, { method: 'POST', body: { submitted } })
      if (index + 1 < codes.length) setIndex(index + 1)
      else onDone(true)
    } catch (err) {
      onToast(err.message, 'error')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal title="Did you submit it?" onClose={() => onDone(index > 0)}>
      {codes.length > 1 && <p className="prompt-progress">Code {index + 1} of {codes.length}</p>}
      <p>In your last session you copied this code. Did you submit it?</p>
      <div className="prompt-code" style={{ '--set-color': color }}>
        <div className="piece-name">{code.piece_name} <span className="muted">#{code.piece_number}</span></div>
        <div className="code-text">{prettyCode(code.code_text)}</div>
        <div className="meta">Copied {formatDateTime(code.copied_at)}</div>
      </div>
      <div className="prompt-actions">
        <button type="button" className="btn btn-primary" disabled={busy} onClick={() => answer(true)}>
          Yes, I submitted it
        </button>
        <button type="button" className="btn btn-secondary" disabled={busy} onClick={() => answer(false)}>
          No, make it Available again
        </button>
        <div className="section-title">
          <button type="button" className="btn-link" onClick={() => onDone(index > 0)}>Ask me later</button>
          <InfoButton topic="status" />
        </div>
      </div>
    </Modal>
  )
}
