import { useEffect, useId, useRef } from 'react'
import { CloseIcon } from './icons.jsx'

// Open modals, top-most last. Only the top one reacts to the back gesture.
const stack = []
let ignoredPops = 0

window.addEventListener('popstate', () => {
  if (ignoredPops > 0) {
    ignoredPops -= 1
    return
  }
  const top = stack[stack.length - 1]
  if (top) {
    top.popped = true
    top.close()
  }
})

/**
 * A centered dialog. Closes with the close button, a tap outside, Escape,
 * or the phone's back gesture. Render it only while open: {open && <Modal …/>}
 */
export default function Modal({ title, onClose, children, className = '' }) {
  const titleId = useId()
  const dialogRef = useRef(null)
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose

  useEffect(() => {
    const entry = { popped: false, close: () => onCloseRef.current() }
    stack.push(entry)
    window.history.pushState({ mvModal: true }, '')

    const previousFocus = document.activeElement
    dialogRef.current?.focus()
    const onKey = (e) => {
      if (e.key === 'Escape' && stack[stack.length - 1] === entry) onCloseRef.current()
    }
    document.addEventListener('keydown', onKey)
    document.body.classList.add('modal-open')

    return () => {
      document.removeEventListener('keydown', onKey)
      stack.splice(stack.indexOf(entry), 1)
      if (stack.length === 0) document.body.classList.remove('modal-open')
      // Closed by button/backdrop: drop the history entry we added.
      if (!entry.popped) {
        ignoredPops += 1
        window.history.back()
      }
      previousFocus?.focus?.()
    }
  }, [])

  return (
    <div className="modal-backdrop" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div
        className={`modal ${className}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        ref={dialogRef}
      >
        <div className="modal-head">
          <h2 id={titleId}>{title}</h2>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close">
            <CloseIcon />
          </button>
        </div>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  )
}
