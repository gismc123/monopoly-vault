import { useEffect, useRef, useState } from 'react'
import { api } from '../api.js'
import { InfoButton, SectionTitle } from '../help.jsx'
import PieceSelect from '../components/PieceSelect.jsx'
import { CameraIcon, KeyboardIcon, UploadIcon } from '../components/icons.jsx'

const EMPTY = { code_text: '', piece_number: '', private: false }

/**
 * Add a code. Photo first: take or upload a picture, the server reads it,
 * and the user confirms or corrects the result. Typing is the fallback.
 */
export default function AddCode({ season, onSaved, onToast }) {
  const [step, setStep] = useState('choose') // choose | reading | confirm | type
  const [photoUrl, setPhotoUrl] = useState(null)
  const [scan, setScan] = useState(null) // { photo_token, candidates, piece_number }
  const cameraInput = useRef(null)
  const uploadInput = useRef(null)
  const unsavedToken = useRef(null) // uploaded photo not yet saved with a code

  useEffect(() => () => photoUrl && URL.revokeObjectURL(photoUrl), [photoUrl])

  // Delete the uploaded photo if the user retakes, cancels, or leaves this screen without saving.
  function discardPhoto() {
    const token = unsavedToken.current
    unsavedToken.current = null
    if (token) api(`/ocr/${token}`, { method: 'DELETE' }).catch(() => {})
  }
  useEffect(() => discardPhoto, [])

  async function onPhoto(e) {
    const file = e.target.files?.[0]
    e.target.value = '' // so choosing the same file again still triggers
    if (!file) return
    setPhotoUrl(URL.createObjectURL(file))
    setStep('reading')
    const form = new FormData()
    form.append('image', file)
    try {
      const result = await api('/ocr', { method: 'POST', form })
      unsavedToken.current = result.photo_token
      setScan(result)
      setStep('confirm')
    } catch (err) {
      onToast(err.message, 'error')
      reset()
    }
  }

  function reset() {
    discardPhoto()
    setPhotoUrl(null)
    setScan(null)
    setStep('choose')
  }

  return (
    <div className="screen">
      <SectionTitle topic="codeEntry">Add a code</SectionTitle>

      {/* Hidden file inputs; the big buttons open them. */}
      <input ref={cameraInput} type="file" accept="image/*" capture="environment" hidden onChange={onPhoto} />
      <input ref={uploadInput} type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={onPhoto} />

      {step === 'choose' && (
        <>
          <button type="button" className="capture-btn" onClick={() => cameraInput.current.click()}>
            <CameraIcon size={44} />
            <span className="capture-title">Take a photo of the sticker</span>
            <span className="capture-sub">The app reads the code for you</span>
          </button>
          <div className="capture-alt">
            <button type="button" className="btn btn-secondary" onClick={() => uploadInput.current.click()}>
              <UploadIcon size={20} /> Upload photo
            </button>
            <button type="button" className="btn btn-secondary" onClick={() => setStep('type')}>
              <KeyboardIcon size={20} /> Type it
            </button>
          </div>
          <div className="section-title">
            <p className="muted small">Tips for a clear photo</p>
            <InfoButton topic="ocr" />
          </div>
        </>
      )}

      {step === 'reading' && (
        <div className="card reading">
          {photoUrl && <img className="sticker-photo" src={photoUrl} alt="Your sticker photo" />}
          <p aria-live="polite"><span className="spinner" aria-hidden="true" /> Reading the code…</p>
        </div>
      )}

      {step === 'confirm' && scan && (
        <CodeForm
          key={scan.photo_token}
          season={season}
          photoUrl={photoUrl}
          scan={scan}
          onCancel={reset}
          onSaved={(result) => { unsavedToken.current = null; reset(); onSaved(result) }}
          onToast={onToast}
        />
      )}

      {step === 'type' && (
        <CodeForm season={season} onCancel={reset} onSaved={(result) => { reset(); onSaved(result) }} onToast={onToast} />
      )}
    </div>
  )
}

/** The confirm step: check the code, pick the piece, choose shared or private. */
function CodeForm({ season, photoUrl, scan, onCancel, onSaved, onToast }) {
  const candidates = scan?.candidates ?? []
  const [form, setForm] = useState({
    ...EMPTY,
    code_text: candidates[0] ?? '',
    piece_number: scan?.piece_number ? String(scan.piece_number) : '',
  })
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
          photo_token: scan?.photo_token ?? null,
        },
      })
      onToast(`Saved ${result.code.piece_name}`)
      onSaved(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="card form" onSubmit={save}>
      {photoUrl && <img className="sticker-photo" src={photoUrl} alt="Your sticker photo" />}
      {scan && (
        <p className={candidates.length ? 'hint' : 'notice'}>
          {candidates.length
            ? 'Check the code against the photo and fix anything misread.'
            : "We couldn't read a code from this photo. Type it from the picture, or retake it."}
        </p>
      )}

      <label htmlFor="code-text">Code</label>
      <input id="code-text" className="code-input" value={form.code_text}
        onChange={(e) => setForm({ ...form, code_text: e.target.value })}
        autoCapitalize="characters" autoCorrect="off" autoComplete="off" spellCheck="false"
        placeholder="e.g. ABCD 1234 EFGH" required autoFocus={!scan} />

      {candidates.length > 1 && (
        <div className="chips" role="group" aria-label="Other possible readings">
          {candidates.map((c) => (
            <button key={c} type="button" className="chip" aria-pressed={form.code_text === c}
              onClick={() => setForm({ ...form, code_text: c })}>{c}</button>
          ))}
        </div>
      )}

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
      <button type="button" className="btn btn-secondary btn-block" onClick={onCancel} disabled={busy}>
        {photoUrl ? 'Retake photo' : 'Cancel'}
      </button>
    </form>
  )
}
