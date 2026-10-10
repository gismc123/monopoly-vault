import { api } from './api.js'

// Remembers which ready sets this person has already been told about, so a set
// completed by a vault-mate is announced once, the next time the app loads.

function key(userId) {
  return `mv.readySeen.${userId}`
}

function load(userId) {
  try { return new Set(JSON.parse(localStorage.getItem(key(userId))) ?? []) } catch { return new Set() }
}

function save(userId, seen) {
  try { localStorage.setItem(key(userId), JSON.stringify([...seen])) } catch { /* storage unavailable */ }
}

const id = (scope, setId) => `${scope}:${setId}`

export function markSeen(userId, sets) {
  const seen = load(userId)
  sets.forEach((s) => seen.add(id(s.scope, s.id)))
  save(userId, seen)
}

/** Ready sets (household and mine) not announced yet. Sets no longer ready are forgotten. */
export async function newlyReadySets(userId) {
  const results = await Promise.all(['household', 'mine'].map((scope) =>
    api(`/collection?scope=${scope}`).then((d) => d.sets.filter((s) => s.complete).map((s) => ({ ...s, scope })))))
  const ready = results.flat()
  const seen = load(userId)
  const fresh = ready.filter((s) => !seen.has(id(s.scope, s.id)))
  save(userId, new Set(ready.map((s) => id(s.scope, s.id))))
  return fresh
}
