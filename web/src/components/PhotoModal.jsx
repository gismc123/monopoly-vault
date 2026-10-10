import { useEffect, useState } from 'react'
import { apiObjectUrl } from '../api.js'
import Modal from './Modal.jsx'

/** The original sticker photo saved with a code. */
export default function PhotoModal({ code, onClose }) {
  const [url, setUrl] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let objectUrl
    apiObjectUrl(`/codes/${code.id}/photo`)
      .then((u) => { objectUrl = u; setUrl(u) })
      .catch((e) => setError(e.message))
    return () => objectUrl && URL.revokeObjectURL(objectUrl)
  }, [code.id])

  return (
    <Modal title={`Photo: ${code.piece_name}`} onClose={onClose}>
      {error && <p className="error">{error}</p>}
      {!url && !error && <p className="muted">Loading…</p>}
      {url && <img className="sticker-photo" src={url} alt={`Original sticker photo for ${code.piece_name}`} />}
    </Modal>
  )
}
