// Small fetch wrapper for the Monopoly Vault API. The JWT is kept in localStorage.

const TOKEN_KEY = 'mv.token'
const USER_KEY = 'mv.user'

export class ApiError extends Error {
  constructor(status, message) {
    super(message)
    this.status = status
  }
}

function read(key) {
  try { return localStorage.getItem(key) } catch { return null }
}

function write(key, value) {
  try {
    if (value == null) localStorage.removeItem(key)
    else localStorage.setItem(key, value)
  } catch { /* storage unavailable (private mode); stay signed in for this tab only */ }
}

let memoryToken = read(TOKEN_KEY)

export function savedUser() {
  try { return memoryToken ? JSON.parse(read(USER_KEY)) : null } catch { return null }
}

export function saveLogin({ access_token, user }) {
  memoryToken = access_token
  write(TOKEN_KEY, access_token)
  write(USER_KEY, JSON.stringify(user))
}

export function clearLogin() {
  memoryToken = null
  write(TOKEN_KEY, null)
  write(USER_KEY, null)
}

export async function api(path, { method = 'GET', body, form } = {}) {
  const headers = {}
  if (memoryToken) headers.Authorization = `Bearer ${memoryToken}`
  let payload
  if (form) payload = form
  else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }

  let res
  try {
    res = await fetch(`/api${path}`, { method, headers, body: payload })
  } catch {
    throw new ApiError(0, "Can't reach the server. Check your connection.")
  }

  if (res.status === 401 && memoryToken) {
    clearLogin()
    window.dispatchEvent(new Event('mv:signed-out'))
  }
  if (res.status === 204) return null
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const detail = typeof data?.detail === 'string' ? data.detail : 'Something went wrong. Please try again.'
    throw new ApiError(res.status, detail)
  }
  return data
}

export function timeZone() {
  try { return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC' } catch { return 'UTC' }
}
