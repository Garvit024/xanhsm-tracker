'use client'

import { useState } from 'react'

const PLATFORM_COLORS: Record<string, string> = {
  uber: '#06b6d4',
  ola: '#f59e0b',
  rapido: '#f43f5e',
}

export function PriceTable({ data, loading }: { data: any[]; loading: boolean }) {
  const [sortCol, setSortCol] = useState<string>('price_min')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const [filterPlatform, setFilterPlatform] = useState('')

  const filtered = data.filter(d => !filterPlatform || d.platform === filterPlatform)
  const sorted = [...filtered].sort((a, b) => {
    const av = a[sortCol] ?? 0
    const bv = b[sortCol] ?? 0
    return sortDir === 'asc' ? (av > bv ? 1 : -1) : (av < bv ? 1 : -1)
  })

  const toggleSort = (col: string) => {
    if (sortCol === col) setDir(sortDir === 'asc' ? 'desc' : 'asc')
    else { setSortCol(col); setSortDir('asc') }
  }
  const setDir = setSortDir

  const SortBtn = ({ col, label }: { col: string; label: string }) => (
    <button
      onClick={() => toggleSort(col)}
      className="flex items-center gap-1 text-xs font-mono hover:opacity-100 transition-opacity"
      style={{ color: sortCol === col ? 'var(--xanh)' : 'var(--text-dim)', opacity: sortCol === col ? 1 : 0.7 }}
    >
      {label}
      {sortCol === col && <span>{sortDir === 'asc' ? '↑' : '↓'}</span>}
    </button>
  )

  return (
    <div className="card overflow-hidden">
      {/* Table header bar */}
      <div className="flex items-center justify-between px-5 py-4 border-b" style={{ borderColor: 'var(--border)' }}>
        <div>
          <h2 className="font-display font-bold text-base" style={{ color: 'var(--text)' }}>Latest Run</h2>
          <p className="text-xs font-mono" style={{ color: 'var(--text-muted)' }}>{sorted.length} fares</p>
        </div>
        {/* Platform filter */}
        <div className="flex gap-2">
          {['', 'uber', 'ola', 'rapido'].map(p => (
            <button
              key={p}
              onClick={() => setFilterPlatform(p)}
              className="px-2.5 py-1 rounded-md text-xs font-mono transition-all"
              style={{
                background: filterPlatform === p ? (p ? `${PLATFORM_COLORS[p]}22` : 'var(--bg-hover)') : 'transparent',
                color: filterPlatform === p ? (p ? PLATFORM_COLORS[p] : 'var(--text)') : 'var(--text-dim)',
                border: `1px solid ${filterPlatform === p ? (p ? PLATFORM_COLORS[p] + '55' : 'var(--border-hi)') : 'transparent'}`,
              }}
            >
              {p || 'All'}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border)', background: 'var(--bg-hover)' }}>
              {[
                { col: 'platform', label: 'Platform' },
                { col: 'od_label', label: 'Route' },
                { col: 'service_name', label: 'Service' },
                { col: 'price_min', label: 'Min ₹' },
                { col: 'price_max', label: 'Max ₹' },
                { col: 'eta_minutes', label: 'ETA' },
                { col: 'surge_active', label: 'Surge' },
              ].map(c => (
                <th key={c.col} className="text-left px-4 py-2.5">
                  <SortBtn col={c.col} label={c.label} />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <tr key={i}>
                  {Array.from({ length: 7 }).map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <div className="h-3 rounded animate-pulse" style={{ background: 'var(--bg-hover)', width: `${50 + Math.random() * 40}%` }} />
                    </td>
                  ))}
                </tr>
              ))
            ) : sorted.length === 0 ? (
              <tr>
                <td colSpan={7} className="text-center py-12">
                  <p className="text-sm font-mono" style={{ color: 'var(--text-dim)' }}>No data — run the scraper first</p>
                </td>
              </tr>
            ) : (
              sorted.map((row, i) => {
                const color = PLATFORM_COLORS[row.platform] || 'var(--text)'
                return (
                  <tr
                    key={i}
                    className="border-b transition-colors"
                    style={{
                      borderColor: 'var(--border)',
                      background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)',
                    }}
                  >
                    <td className="px-4 py-3">
                      <span
                        className="text-xs font-mono px-2 py-0.5 rounded-full"
                        style={{ color, background: `${color}1a`, border: `1px solid ${color}33` }}
                      >
                        {row.platform}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs font-mono max-w-[180px] truncate" style={{ color: 'var(--text-muted)' }}>
                      {row.od_label}
                    </td>
                    <td className="px-4 py-3 text-xs font-mono" style={{ color: 'var(--text)' }}>
                      {row.service_name}
                    </td>
                    <td className="px-4 py-3 font-display font-semibold text-sm" style={{ color: 'var(--text)' }}>
                      {row.price_min != null ? `₹${row.price_min}` : '—'}
                    </td>
                    <td className="px-4 py-3 text-sm font-mono" style={{ color: 'var(--text-muted)' }}>
                      {row.price_max != null ? `₹${row.price_max}` : '—'}
                    </td>
                    <td className="px-4 py-3 text-xs font-mono" style={{ color: 'var(--text-muted)' }}>
                      {row.eta_minutes != null ? `${row.eta_minutes}m` : '—'}
                    </td>
                    <td className="px-4 py-3">
                      {row.surge_active ? (
                        <span className="text-xs font-mono surge-glow" style={{ color: 'var(--surge)' }}>
                          ⚡ {row.surge_mult ? `${row.surge_mult}x` : 'Yes'}
                        </span>
                      ) : (
                        <span className="text-xs font-mono" style={{ color: 'var(--text-dim)' }}>—</span>
                      )}
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
