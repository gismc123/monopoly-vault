import { useEffect, useState } from 'react'
import { api } from '../api.js'

// Plain-language Terms of Service and Privacy Policy, shown at /terms and /privacy.
// Each copy of Monopoly Vault is run by its own operator; their name and contact
// come from OPERATOR_NAME and OPERATOR_CONTACT in .env.

const EFFECTIVE_DATE = 'October 10, 2026'

export default function Legal({ page }) {
  const [info, setInfo] = useState({ operator_name: '', operator_contact: '', unclaimed_photo_hours: 24 })

  useEffect(() => {
    document.title = `${page === 'terms' ? 'Terms of Service' : 'Privacy Policy'} · Monopoly Vault`
    api('/legal').then(setInfo).catch(() => {})
  }, [page])

  return (
    <main className="legal">
      <a className="btn-link" href="/">← Back to Monopoly Vault</a>
      {page === 'terms' ? <Terms info={info} /> : <Privacy info={info} />}
      <footer className="legal-footer">
        <a href="/terms">Terms of Service</a> · <a href="/privacy">Privacy Policy</a>
      </footer>
    </main>
  )
}

function Operator({ info }) {
  return info.operator_name
    ? <>This copy of Monopoly Vault is run by <strong>{info.operator_name}</strong> (the "operator").</>
    : <>This copy of Monopoly Vault is run by the person or household who set it up and invited you
      (the "operator").</>
}

function Contact({ info }) {
  const contact = info.operator_contact
  if (!contact) return <>the person who invited you to this app</>
  if (/^\S+@\S+\.\S+$/.test(contact)) return <a href={`mailto:${contact}`}>{contact}</a>
  if (/^https?:\/\//.test(contact)) return <a href={contact} rel="noreferrer">{contact}</a>
  return <>{contact}</>
}

function Terms({ info }) {
  return (
    <article>
      <h1>Terms of Service</h1>
      <p className="muted">Effective {EFFECTIVE_DATE}</p>

      <p><Operator info={info} /> By creating an account or using the app, you agree to these terms. If you
        don't agree, please don't use it.</p>

      <h2>What Monopoly Vault is</h2>
      <p>Monopoly Vault is a free, open-source tool that helps a household keep track of their McDonald's Monopoly
        game codes in one place. It stores codes, shows which color sets are complete, and gives you a button to
        copy a code.</p>
      <p>Monopoly Vault is <strong>not affiliated with, endorsed by, or sponsored by McDonald's or Hasbro</strong>.
        McDonald's is a trademark of McDonald's Corporation. MONOPOLY is a trademark of Hasbro. These names are
        used only to describe the game the app helps you track.</p>

      <h2>The game's Official Rules come first</h2>
      <p>Monopoly Vault never signs in to, automates, or submits anything to the McDonald's app or website. You
        enter codes into McDonald's yourself, and you are responsible for following the promotion's Official
        Rules, including that:</p>
      <ul>
        <li>each person plays with their own McDonald's account and redeems from that account;</li>
        <li>game pieces may not be consolidated into one account or transferred between participants except as the
          rules allow;</li>
        <li>daily code entry limits and prize claim deadlines apply;</li>
        <li>original physical game pieces must be kept where the rules require them, such as for Collect to Win
          prizes.</li>
      </ul>
      <p>The reminders shown in the app are a convenience and may be incomplete or out of date. Always check the
        current Official Rules.</p>

      <h2>Your account</h2>
      <ul>
        <li>Keep your password private. You are responsible for what happens under your account.</li>
        <li>Use one account per person, and use a name your household will recognize.</li>
        <li>Too many failed sign-in attempts will pause sign-in for a while to protect your account.</li>
      </ul>

      <h2>Your codes and photos</h2>
      <p>The codes and sticker photos you add stay yours. You allow the operator to store them and show them as the
        app describes: shared codes and their photos to members of your vault, private codes only to you. Only
        upload photos of your own game pieces, and avoid capturing other people's personal information.</p>

      <h2>Acceptable use</h2>
      <p>Don't use Monopoly Vault to:</p>
      <ul>
        <li>buy, sell, or trade codes;</li>
        <li>try to access other people's accounts or codes, guess passwords, or get around security or rate
          limits;</li>
        <li>overload, scrape, or disrupt the service;</li>
        <li>break the law or the promotion's Official Rules.</li>
      </ul>

      <h2>How code status works and its limits</h2>
      <p>Statuses (Available, Pending, Used) depend on vault members answering honestly. The app cannot see whether
        McDonald's accepted a code. The operator and the authors of Monopoly Vault are not responsible for codes
        that are lost, mistyped, misread by OCR, already used, rejected, or expired, or for prizes that are missed.
        Keep your physical stickers until the promotion ends.</p>

      <h2>No warranty</h2>
      <p>The app is provided "as is" and "as available," without warranties of any kind. It may be unavailable,
        contain errors, or lose data. To the fullest extent the law allows, the operator and the authors of
        Monopoly Vault are not liable for any indirect, incidental, or consequential damages, or for any loss
        arising from your use of the app.</p>

      <h2>Ending your use</h2>
      <p>You can stop using the app at any time and ask the operator to delete your account (see the Privacy
        Policy). The operator may suspend or remove accounts that break these terms.</p>

      <h2>The software</h2>
      <p>Monopoly Vault's source code is released under the MIT License. That license covers the software. These
        terms cover your use of this copy of the app.</p>

      <h2>Changes</h2>
      <p>The operator may update these terms. The effective date above will change when they do. If you keep using
        the app after a change, you accept the updated terms.</p>

      <h2>Contact</h2>
      <p>Questions? Contact <Contact info={info} />.</p>
    </article>
  )
}

function Privacy({ info }) {
  return (
    <article>
      <h1>Privacy Policy</h1>
      <p className="muted">Effective {EFFECTIVE_DATE}</p>

      <p><Operator info={info} /> This policy explains what the app stores, who can see it, and how to remove
        it. Monopoly Vault is open-source software that each operator runs on their own server. The authors of the
        software do not receive any data from this copy.</p>

      <h2>The short version</h2>
      <ul>
        <li>The app stores only what it needs to track your household's codes.</li>
        <li>No ads, no analytics, no tracking, and no cookies.</li>
        <li>Your data is not sold or shared with anyone, including McDonald's.</li>
        <li>Photos are read (OCR) on the operator's own server, not by an outside service.</li>
      </ul>

      <h2>What is stored on the server</h2>
      <ul>
        <li><strong>Account:</strong> your display name, username, and password. The password is stored only as a
          one-way hash, so nobody can read it.</li>
        <li><strong>Codes:</strong> the code text, the game piece, whether it is shared or private, its status, when
          it was added, copied, and confirmed, and who copied or used it.</li>
        <li><strong>Sticker photos:</strong> the original image you take or upload, kept with its code as a record.
          A photo can include anything else in the frame, plus details your phone saves in the file, which may
          include the date and, if location tagging is turned on, where it was taken.</li>
        <li><strong>Vault:</strong> its name, invite code, members, and when each person joined.</li>
        <li><strong>Session time:</strong> when you last opened the app, so it can ask about codes you copied
          before.</li>
      </ul>

      <h2>Information used but not stored in the database</h2>
      <ul>
        <li><strong>IP address:</strong> kept briefly in memory to limit repeated sign-in attempts. It may also
          appear in the server's technical logs, depending on how the operator runs the app.</li>
        <li><strong>Time zone:</strong> your device's time zone, used to count today's code entries.</li>
      </ul>

      <h2>What is stored on your device</h2>
      <p>The app uses your browser's local storage, not cookies, to keep you signed in (a sign-in token, plus your
        name and username), to remember which completed sets it has already told you about, and to know when a new
        session starts. The installable app also saves its own files so it opens quickly. Signing out removes your
        sign-in token. Clearing your browser's site data removes everything.</p>

      <h2>Who can see your information</h2>
      <ul>
        <li><strong>Shared codes</strong> (the default) and their photos are visible to members of your vault,
          along with your name.</li>
        <li><strong>Private codes</strong> and their photos are visible only to you.</li>
        <li>Members of your vault see who copied or used a shared code, and when.</li>
        <li>The <strong>operator</strong> runs the server and can technically access everything stored on it.</li>
      </ul>
      <p>Monopoly Vault does not connect to McDonald's. When you paste a code into the McDonald's app, McDonald's
        own privacy policy applies to what you share there.</p>

      <h2>How long information is kept</h2>
      <ul>
        <li>Codes, photos, and accounts are kept until they are deleted.</li>
        <li>You can delete your own Available codes at any time. Their photos are deleted with them.</li>
        <li>A photo you take but don't save is deleted when you retake it, cancel, or leave the screen. Any that
          remain are deleted automatically after {info.unclaimed_photo_hours} hours.</li>
        <li>Leaving a vault stops sharing your codes with its members.</li>
        <li>Each October season starts fresh in the app. Past seasons' data stays on the server until the operator
          removes it.</li>
      </ul>

      <h2>Your choices</h2>
      <p>You can view your information in the app, make any code private, delete Available codes, and leave your
        vault. To get a copy of your data, or to delete your account and everything linked to it, contact{' '}
        <Contact info={info} />.</p>

      <h2>Security</h2>
      <p>Passwords are hashed, sign-in attempts are rate limited, and each person can see only their own codes and
        their vault's shared codes. The operator is responsible for the server, backups, and for serving the app
        over HTTPS. No system is perfectly secure.</p>

      <h2>Children</h2>
      <p>Monopoly Vault is not directed to children under 13, and they should not create accounts. The promotion's
        Official Rules set their own age requirements.</p>

      <h2>Changes</h2>
      <p>The operator may update this policy. The effective date above will change when they do.</p>

      <h2>Contact</h2>
      <p>Privacy questions or requests: <Contact info={info} />.</p>
    </article>
  )
}
