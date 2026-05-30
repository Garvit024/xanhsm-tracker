'use client'

const PLATFORMS = [
  { key: 'uber',   label: 'Uber',   color: 'var(--uber)' },
  { key: 'ola',    label: 'Ola',    color: 'var(--ola)' },
  { key: 'rapido', label: 'Rapido', color: 'var(--rapido)' },
]

export function PlatformLegend() {
  return (
    <div className="flex items-center gap-4">
      {PLATFORMS.map(p => (
        <div key={p.key} className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full" style={{ background: p.color, boxShadow: `0 0 6px ${p.color}` }} />
          <span className="text-xs font-mono" style={{ color: 'var(--text-muted)' }}>{p.label}</span>
        </div>
      ))}
    </div>
  )
}
