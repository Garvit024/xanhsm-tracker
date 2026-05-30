'use client'

const PLATFORM_COLORS: Record<string, string> = {
  uber: 'var(--uber)',
  ola: 'var(--ola)',
  rapido: 'var(--rapido)',
}

function Skeleton() {
  return <div className="h-24 rounded-xl animate-pulse" style={{ background: 'var(--bg-card)' }} />
}

export function SummaryCards({ summary, loading }: { summary: any[]; loading: boolean }) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
        {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} />)}
      </div>
    )
  }

  // Group by platform, take cheapest service per platform for headline
  const byPlatform: Record<string, any> = {}
  for (const row of summary) {
    if (!byPlatform[row.platform]) byPlatform[row.platform] = []
    byPlatform[row.platform].push(row)
  }

  const cards = Object.entries(byPlatform).flatMap(([platform, rows]: [string, any[]]) => {
    // Take top 2 services by observations for this platform
    const top = rows.sort((a, b) => b.observations - a.observations).slice(0, 2)
    return top.map((r: any) => ({ ...r, platform }))
  })

  if (!cards.length) {
    return (
      <div className="card p-6 text-center" style={{ color: 'var(--text-muted)' }}>
        <p className="font-mono text-sm">No data yet. Run the scraper to populate.</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
      {cards.map((c, i) => {
        const color = PLATFORM_COLORS[c.platform] || 'var(--xanh)'
        return (
          <div
            key={i}
            className="card p-4 space-y-2 transition-all hover:translate-y-[-2px] animate-slide-up"
            style={{ animationDelay: `${i * 60}ms`, animationFillMode: 'both' }}
          >
            <div className="flex items-center justify-between">
              <span
                className="text-xs font-mono px-2 py-0.5 rounded-full"
                style={{ color, background: `${color}22`, border: `1px solid ${color}44` }}
              >
                {c.platform}
              </span>
              {c.surge_pct > 30 && (
                <span className="text-xs font-mono surge-glow px-1.5 py-0.5 rounded" style={{ color: 'var(--surge)', background: '#fb923c1a' }}>
                  ⚡ {c.surge_pct}%
                </span>
              )}
            </div>
            <div>
              <div className="font-display font-bold text-xl" style={{ color: 'var(--text)' }}>
                {c.avg_price != null ? `₹${c.avg_price}` : '—'}
              </div>
              <div className="text-xs font-mono mt-0.5" style={{ color: 'var(--text-muted)' }}>
                {c.service_name}
              </div>
            </div>
            <div className="text-xs font-mono" style={{ color: 'var(--text-dim)' }}>
              ₹{c.min_price}–{c.max_price} · {c.observations} obs
            </div>
          </div>
        )
      })}
    </div>
  )
}
