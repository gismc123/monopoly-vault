import { createContext, useContext, useState } from 'react'
import Modal from './components/Modal.jsx'
import { InfoIcon } from './components/icons.jsx'
import { formatDay } from './format.js'

// Shown wherever redeeming is explained (McDonald's 2026 Official Rules).
function RulesNote() {
  return (
    <p className="rules-note">
      Monopoly Vault only keeps track of codes. It never signs in to or submits anything to the
      McDonald's app. Each person redeems from their own McDonald's account. Keep your original
      physical stickers, because Collect to Win prizes require them.
    </p>
  )
}

// One entry per section or feature. Keep each short enough to read on a phone.
export const HELP = {
  codeEntry: {
    title: 'Adding a code',
    body: (
      <>
        <p>Take a photo of the sticker and the app reads the code for you. You can also type it.</p>
        <p>Before saving, check the code and pick the game piece it came with. If the photo was misread, fix the
          text in the box. Spaces and dashes don't matter.</p>
      </>
    ),
  },
  ocr: {
    title: 'Photo capture',
    body: (
      <>
        <p>For a clear read: lay the sticker flat, use good light, fill the frame with the code, and avoid glare.</p>
        <p>You always get to confirm or correct the code before it is saved. The original photo is kept with the
          code as a backup record, in case of a misread or a dispute.</p>
      </>
    ),
  },
  collection: {
    title: 'Collection board',
    body: (
      <>
        <p>Every color set and its pieces are listed. A piece is checked off when someone holds an Available or
          Pending code for it.</p>
        <p><strong>Missing</strong> lists the pieces nobody holds yet, so you know exactly what's left in a set.
          Tap a piece to see its codes.</p>
      </>
    ),
  },
  pooling: {
    title: 'Household and Mine',
    body: (
      <>
        <p><strong>Household</strong> combines the shared codes of everyone in your vault. Sets are counted
          across the whole household.</p>
        <p><strong>Mine</strong> counts only your own codes, including private ones.</p>
        <p>To link with someone, create a vault and share its invite code, or join theirs on the Vault tab.</p>
      </>
    ),
  },
  vault: {
    title: 'Your vault',
    body: (
      <>
        <p>A vault is your household's shared space. Everyone in it sees each other's shared codes, and set
          progress is combined. You can be in one vault per season.</p>
        <p>Create a vault and send the invite code to your family, or enter theirs to join.</p>
        <RulesNote />
      </>
    ),
  },
  privacy: {
    title: 'Shared or private',
    body: (
      <>
        <p>New codes are <strong>Shared</strong>: everyone in your vault can see and use them.</p>
        <p>Turn on <strong>Private</strong> to keep a code to yourself. A private code counts toward your own
          sets only and never shows in the household view. It only changes when you change it.</p>
      </>
    ),
  },
  readyAlert: {
    title: 'Ready to redeem',
    body: (
      <>
        <p>A set is ready when every piece in it has an Available or Pending code. The app tells you as soon as a
          code completes a set, and ready sets are listed at the top of the board.</p>
        <p>Then agree on who redeems which set.</p>
        <RulesNote />
      </>
    ),
  },
  copy: {
    title: 'Copy to redeem',
    body: (
      <>
        <p>Tap <strong>Copy</strong> and paste the code into the McDonald's app yourself.</p>
        <p>Copying marks the code <strong>Pending</strong> so nobody else copies it too. Next time you open
          Monopoly Vault, it asks whether you submitted it.</p>
        <RulesNote />
      </>
    ),
  },
  status: {
    title: 'Code status',
    body: (
      <>
        <p><span className="status status-available">Available</span> Collected and not copied yet.</p>
        <p><span className="status status-pending">Pending</span> Copied, not confirmed. Only the person who copied
          it can copy it again.</p>
        <p><span className="status status-used">Used</span> Confirmed submitted, with the date and who used it.</p>
        <p>Next time you open the app you'll be asked: "Did you submit it?" <strong>Yes</strong> marks it Used.
          <strong> No</strong> makes it Available again. It stays Pending until you answer.</p>
      </>
    ),
  },
  season: {
    title: 'One season per year',
    body: (
      <>
        <p>McDonald's Monopoly runs each October. Every campaign is its own season and starts fresh. Codes from
          past years are not carried over.</p>
      </>
    ),
  },
  limits: {
    title: 'Daily limit and deadline',
    body: (season) => (
      <>
        <p>McDonald's allows {season?.daily_entry_limit ?? 8} code entries per day per account. The count here is
          how many codes you've copied today.</p>
        {season && <p>Prize claims close {formatDay(season.claim_deadline)}.</p>}
      </>
    ),
  },
}

const HelpContext = createContext(() => {})

export function HelpProvider({ season, children }) {
  const [topic, setTopic] = useState(null)
  const help = topic && HELP[topic]
  return (
    <HelpContext.Provider value={setTopic}>
      {children}
      {help && (
        <Modal title={help.title} onClose={() => setTopic(null)} className="help-modal">
          {typeof help.body === 'function' ? help.body(season) : help.body}
          <button type="button" className="btn btn-secondary btn-block" onClick={() => setTopic(null)}>
            Got it
          </button>
        </Modal>
      )}
    </HelpContext.Provider>
  )
}

/** The (i) button that opens the help modal for one section or feature. */
export function InfoButton({ topic }) {
  const showHelp = useContext(HelpContext)
  return (
    <button type="button" className="info-btn" onClick={() => showHelp(topic)} aria-label={`Help: ${HELP[topic].title}`}>
      <InfoIcon size={20} />
    </button>
  )
}

/** A section title with its info button. */
export function SectionTitle({ topic, children, as: Tag = 'h2' }) {
  return (
    <div className="section-title">
      <Tag>{children}</Tag>
      <InfoButton topic={topic} />
    </div>
  )
}
