'use client'

const TIME_SLOTS = ['07:00','09:00','12:00','14:00','17:30','19:00','21:00','23:30']
const PLATFORMS = ['uber','ola','rapido']

const PLATFORM_COLORS: Record<string, string> = {
  uber: '#06b6d4',
  ola: '#f59e0b',
  rapido: '#f43f5e',
}

export function SurgeMap({ summary, loading }: { summary: any[]; loading: boolean }) {
  // Build surge% lookup: platform → avg surge_pct across services
  const surgeByPlatform: Record<string, number> = {}
  for (const p of PLATFORMS) {
    const rows = summary.filter(r => r.platform === p)
    if (rows.length) {
      surgeByPlatform[p] = Math.round(rows.reduce((a, r) => a + r.surge_pct, 0) / rows.length)
    }
  }

  return (
    <div className="card p-5" style={{ minHeight: 320 }}>
      <div className="mb-4">
        <h2 className="font-display font-bold text-base" style={{ color: 'var(--text)' }}>
          Surge Frequency
        </h2>
        <p className="text-xs font-mono mt-0.5" style={{ color: 'var(--text-muted)' }}>
          % of scrapes with surge detected
        </p>
      </div>

      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-12 rounded-lg animate-pulse" style={{ background: 'var(--bg-hover)' }} />
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {PLATFORMS.map(p => {
            const pct = surgeByPlatform[p] ?? 0
            const color = PLATFORM_COLORS[p]
            return (
              <div key={p}>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-mono uppercase" style={{ color }}>{p}</span>
                  <span className="text-xs font-mono" style={{ color: pct > 40 ? 'var(--surge)' : 'var(--text-muted)' }}>
                    {pct}%
                  </span>
                </div>
                <div className="h-2 rounded-full overflow-hidden" style={{ background: 'var(--bg-hover)' }}>
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${pct}%`,
                      background: pct > 50
                        ? 'var(--surge)'
                        : pct > 25
                          ? color
                          : `${color}88`,
                      boxShadow: pct > 50 ? '0 0 8px var(--surge)' : `0 0 6px ${color}66`,
                    }}
                  />
                </div>
              </div>
            )
          })}

          {/* Interpretation guide */}
          <div className="mt-4 pt-4 border-t space-y-1.5" style={{ borderColor: 'var(--border)' }}>
            <p className="text-xs font-mono font-semibold" style={{ color: 'var(--text-dim)' }}>GUIDE</p>
            {[
              { label: '> 50%', note: 'Heavy surge · avoid recommending', color: 'var(--surge)' },
              { label: '25–50%', note: 'Moderate surge · monitor', color: 'var(--ola)' },
              { label: '< 25%', note: 'Normal pricing', color: 'var(--xanh)' },
            ].map(g => (
              <div key={g.label} className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: g.color }} />
                <span className="text-xs font-mono" style={{ color: g.color }}>{g.label}</span>
                <span className="text-xs font-mono" style={{ color: 'var(--text-dim)' }}>— {g.note}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
