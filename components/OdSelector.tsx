'use client'

type Pair = { id: string; label: string }

export function OdSelector({ pairs, selected, onChange }: {
  pairs: Pair[]
  selected: string
  onChange: (id: string) => void
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {pairs.map(p => (
        <button
          key={p.id}
          onClick={() => onChange(p.id)}
          className="px-3 py-1.5 rounded-full text-xs font-mono transition-all"
          style={{
            background: selected === p.id ? 'var(--xanh)' : 'var(--bg-card)',
            color: selected === p.id ? '#000' : 'var(--text-muted)',
            border: `1px solid ${selected === p.id ? 'var(--xanh)' : 'var(--border)'}`,
            fontWeight: selected === p.id ? 700 : 400,
          }}
        >
          {p.label}
        </button>
      ))}
    </div>
  )
}
