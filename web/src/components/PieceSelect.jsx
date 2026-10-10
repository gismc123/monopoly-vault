/** Native select grouped by color set: the most usable picker on a phone. */
export default function PieceSelect({ season, value, onChange, id }) {
  return (
    <select id={id} value={value} onChange={(e) => onChange(e.target.value)} required>
      <option value="">Choose a piece…</option>
      {season.sets.map((set) => (
        <optgroup key={set.id} label={set.name}>
          {set.pieces.map((p) => (
            <option key={p.number} value={p.number}>#{p.number} {p.name}</option>
          ))}
        </optgroup>
      ))}
    </select>
  )
}
