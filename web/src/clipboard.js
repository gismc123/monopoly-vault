import { api } from './api.js'

/**
 * Claim a code (Available -> Pending) and put it on the clipboard.
 *
 * The claim happens first so two people can't copy the same code. Safari only
 * allows clipboard writes during the tap itself, so where supported we hand the
 * clipboard a promise that resolves once the server agrees.
 * Returns { code, copied }. Throws ApiError if someone else already has it.
 */
export async function claimAndCopy(codeId) {
  const claim = api(`/codes/${codeId}/copy`, { method: 'POST' })
  let copied = false

  if (window.ClipboardItem && navigator.clipboard?.write) {
    try {
      const blob = claim.then((c) => new Blob([c.code_text], { type: 'text/plain' }))
      await navigator.clipboard.write([new ClipboardItem({ 'text/plain': blob })])
      copied = true
    } catch { /* fall back below */ }
  }

  const code = await claim
  if (!copied) copied = await writeText(code.code_text)
  return { code, copied }
}

async function writeText(text) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch { /* not allowed on plain http:// pages */ }

  const area = document.createElement('textarea')
  area.value = text
  area.setAttribute('readonly', '')
  area.style.cssText = 'position:fixed;top:0;left:0;opacity:0'
  document.body.appendChild(area)
  area.select()
  area.setSelectionRange(0, text.length)
  let ok = false
  try { ok = document.execCommand('copy') } catch { /* unsupported */ }
  area.remove()
  return ok
}
