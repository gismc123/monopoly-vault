import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { textOn } from '../colors.js'
import { InfoButton, SectionTitle } from '../help.jsx'
import Modal from '../components/Modal.jsx'
import CodeCard from '../components/CodeCard.jsx'
import { CheckIcon, StarIcon } from '../components/icons.jsx'

/** The collection board: every color set and piece, for the household or just me. */
export default function Board({ season, me, version, onChanged, onToast, onGoToVault }) {
  const [scope, setScope] = useState('household')
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [openPiece, setOpenPiece] = useState(null)

  useEffect(() => {
    api(`/collection?scope=${scope}`)
      .then((d) => { setData(d); setError('') })
      .catch((e) => setError(e.message))
  }, [scope, version])

  const ready = data?.sets.filter((s) => s.complete) ?? []
  const totalHeld = data?.sets.reduce((n, s) => n + s.held_count, 0) ?? 0
  const totalPieces = season.sets.reduce((n, s) => n + s.pieces.length, 0)

  return (
    <div className="screen">
      <div className="scope-row">
        <div className="segmented" role="tablist" aria-label="Whose codes to count">
          {[['household', 'Household'], ['mine', 'Mine']].map(([value, label]) => (
            <button key={value} role="tab" aria-selected={scope === value} onClick={() => setScope(value)}>
              {label}
            </button>
          ))}
        </div>
        <InfoButton topic="pooling" />
      </div>

      {data && scope === 'household' && !data.has_vault && (
        <div className="notice">
          You're not in a vault yet, so this shows only your shared codes.{' '}
          <button type="button" className="btn-link inline" onClick={onGoToVault}>Create or join a vault</button>
        </div>
      )}

      {ready.length > 0 && (
        <section className="ready-banner" aria-live="polite">
          <div className="section-title">
            <h2><StarIcon size={20} /> {ready.length === 1 ? '1 set' : `${ready.length} sets`} ready to redeem</h2>
            <InfoButton topic="readyAlert" />
          </div>
          <div className="ready-chips">
            {ready.map((s) => (
              <span key={s.id} className="set-chip" style={{ background: s.color, color: textOn(s.color) }}>{s.name}</span>
            ))}
          </div>
        </section>
      )}

      <SectionTitle topic="collection">
        Collection <span className="muted small">{totalHeld} of {totalPieces} pieces</span>
      </SectionTitle>

      {error && <p className="error" role="alert">{error}</p>}
      {!data && !error && <p className="muted">Loading…</p>}

      <div className="sets">
        {data?.sets.map((set) => (
          <section key={set.id} className={`set-card ${set.complete ? 'is-complete' : ''}`} style={{ '--set-color': set.color }}>
            <header className="set-head" style={{ background: set.color, color: textOn(set.color) }}>
              <h3>{set.name}</h3>
              <span className="set-count">
                {set.complete ? <><CheckIcon size={16} /> Ready</> : `${set.held_count}/${set.pieces.length}`}
              </span>
            </header>
            <ul className="pieces">
              {set.pieces.map((p) => (
                <li key={p.number}>
                  <button type="button" className={`piece ${p.held ? 'held' : 'missing'}`}
                    onClick={() => setOpenPiece({ ...p, color: set.color })}
                    aria-label={`${p.name}: ${p.held ? `${p.available + p.pending} code(s)` : 'missing'}`}>
                    <span className="piece-check" aria-hidden="true">{p.held ? <CheckIcon size={16} /> : null}</span>
                    <span className="piece-label">
                      <span className="piece-title">{p.name}</span>
                      <span className="piece-sub">
                        #{p.number}
                        {p.available > 0 && ` · ${p.available} available`}
                        {p.pending > 0 && ` · ${p.pending} pending`}
                        {p.used > 0 && ` · ${p.used} used`}
                      </span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
            {!set.complete && <p className="missing-line">Missing: {set.missing.join(', ')}</p>}
          </section>
        ))}
      </div>

      {openPiece && (
        <PieceSheet piece={openPiece} scope={scope} me={me} version={version}
          onClose={() => setOpenPiece(null)} onChanged={onChanged} onToast={onToast} />
      )}
    </div>
  )
}

/** Tap a piece: see the codes that cover it. */
function PieceSheet({ piece, scope, me, version, onClose, onChanged, onToast }) {
  const [codes, setCodes] = useState(null)

  useEffect(() => {
    api(`/codes?scope=${scope === 'mine' ? 'mine' : 'all'}`)
      .then((all) => setCodes(all.filter((c) => c.piece_number === piece.number
        && (scope === 'mine' || c.visibility === 'shared'))))
      .catch((e) => onToast(e.message, 'error'))
  }, [piece.number, scope, version])

  return (
    <Modal title={`${piece.name} #${piece.number}`} onClose={onClose}>
      {!codes && <p className="muted">Loading…</p>}
      {codes?.length === 0 && <p>Nobody {scope === 'mine' ? 'in your codes ' : ''}holds this piece yet.</p>}
      <div className="code-list">
        {codes?.map((c) => (
          <CodeCard key={c.id} code={c} color={piece.color} me={me.id} onChanged={onChanged} onToast={onToast} />
        ))}
      </div>
    </Modal>
  )
}
