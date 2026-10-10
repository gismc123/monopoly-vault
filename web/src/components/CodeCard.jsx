import { useState } from 'react'
import { api } from '../api.js'
import { claimAndCopy } from '../clipboard.js'
import { formatDateTime } from '../format.js'
import Modal from './Modal.jsx'
import { CopyIcon, LockIcon, TrashIcon } from './icons.jsx'

const STATUS_LABEL = { available: 'Available', pending: 'Pending', used: 'Used' }

export function StatusBadge({ status }) {
  return <span className={`status status-${status}`}>{STATUS_LABEL[status]}</span>
}

/** Codes are shown in groups of four so they're easier to read aloud or check. */
export function prettyCode(text) {
  return text.match(/.{1,4}/g).join(' ')
}

function whoName(person, me) {
  return person.id === me ? 'you' : person.name
}

export default function CodeCard({ code, color, me, onChanged, onToast }) {
  const [busy, setBusy] = useState(false)
  const [manualCopy, setManualCopy] = useState(null)

  async function run(action, successMessage) {
    setBusy(true)
    try {
      await action()
      if (successMessage) onToast(successMessage)
      onChanged()
    } catch (err) {
      onToast(err.message, 'error')
    } finally {
      setBusy(false)
    }
  }

  const copy = () => run(async () => {
    const { code: claimed, copied } = await claimAndCopy(code.id)
    if (copied) onToast('Copied. Paste it in the McDonald\'s app. It\'s now Pending.')
    else setManualCopy(claimed.code_text)
  })

  const answer = (submitted) => run(
    () => api(`/codes/${code.id}/confirm`, { method: 'POST', body: { submitted } }),
    submitted ? 'Marked as used' : 'Back to Available',
  )

  const togglePrivate = () => {
    const visibility = code.visibility === 'private' ? 'shared' : 'private'
    run(() => api(`/codes/${code.id}`, { method: 'PATCH', body: { visibility } }),
      visibility === 'private' ? 'Code is now private' : 'Code is now shared with your vault')
  }

  const remove = () => {
    if (!window.confirm(`Delete code ${prettyCode(code.code_text)}? This can't be undone.`)) return
    run(() => api(`/codes/${code.id}`, { method: 'DELETE' }), 'Code deleted')
  }

  return (
    <article className={`code-card is-${code.status}`} style={{ '--set-color': color }}>
      <header className="code-card-head">
        <div>
          <div className="piece-name">
            {code.piece_name} <span className="muted">#{code.piece_number}</span>
          </div>
          <div className="meta">
            {code.is_mine ? 'Yours' : `${code.owner.name}'s`}
            {code.visibility === 'private' && <span className="private-tag"><LockIcon size={14} /> Private</span>}
          </div>
        </div>
        <StatusBadge status={code.status} />
      </header>

      <div className="code-text" aria-label={`Code ${code.code_text.split('').join(' ')}`}>{prettyCode(code.code_text)}</div>

      {code.status === 'pending' && code.copied_by && (
        <p className="meta">Copied by {whoName(code.copied_by, me)} · {formatDateTime(code.copied_at)}</p>
      )}
      {code.status === 'used' && code.used_by && (
        <p className="meta">Used by {whoName(code.used_by, me)} · {formatDateTime(code.confirmed_at)}</p>
      )}

      <div className="code-actions">
        {code.can_copy && (
          <button type="button" className="btn btn-primary btn-copy" onClick={copy} disabled={busy}>
            <CopyIcon size={20} /> {code.status === 'pending' ? 'Copy again' : 'Copy'}
          </button>
        )}
        {code.is_mine && (
          <button type="button" role="switch" aria-checked={code.visibility === 'private'}
            className="switch" onClick={togglePrivate} disabled={busy}>
            <span className="switch-track" aria-hidden="true"><span className="switch-thumb" /></span>
            Private
          </button>
        )}
        {code.is_mine && code.status === 'available' && (
          <button type="button" className="icon-btn" onClick={remove} disabled={busy} aria-label="Delete code">
            <TrashIcon size={20} />
          </button>
        )}
      </div>

      {code.status === 'pending' && code.copied_by?.id === me && (
        <div className="answer-row">
          <span className="meta">Did you submit it?</span>
          <button type="button" className="btn btn-secondary" onClick={() => answer(true)} disabled={busy}>Yes</button>
          <button type="button" className="btn btn-secondary" onClick={() => answer(false)} disabled={busy}>No</button>
        </div>
      )}

      {manualCopy && (
        <Modal title="Copy this code" onClose={() => setManualCopy(null)}>
          <p>Your browser didn't allow automatic copying. Press and hold the code to copy it.
            It's marked Pending for you.</p>
          <input className="manual-copy code-input" readOnly value={manualCopy} onFocus={(e) => e.target.select()} autoFocus />
          <button type="button" className="btn btn-secondary btn-block" onClick={() => setManualCopy(null)}>Done</button>
        </Modal>
      )}
    </article>
  )
}
