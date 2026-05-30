'use client'

import { useEffect, useState, useCallback } from 'react'
import { PriceTable } from '@/components/PriceTable'
import { PriceChart } from '@/components/PriceChart'
import { SummaryCards } from '@/components/SummaryCards'
import { OdSelector } from '@/components/OdSelector'
import { PlatformLegend } from '@/components/PlatformLegend'
import { SurgeMap } from '@/components/SurgeMap'

const OD_PAIRS = [
  { id: '', label: 'All Routes' },
  { id: 'cp_to_airport', label: 'CP → IGI Airport' },
  { id: 'gurgaon_cyber_to_dlf', label: 'Cyber City → DLF' },
  { id: 'noida_sec18_to_cp', label: 'Noida Sec 18 → CP' },
  { id: 'lajpat_to_gurgaon_huda', label: 'Lajpat → HUDA' },
]

export default function Dashboard() {
  const [selectedOd, setSelectedOd] = useState('')
  const [hours, setHours] = useState(24)
  const [latest, setLatest] = useState<any>(null)
  const [summary, setSummary] = useState<any>(null)
  const [timeSeries, setTimeSeries] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    setLoading(true)
    const [latestRes, summaryRes, pricesRes] = await Promise.all([
      fetch('/api/latest'),
      fetch(`/api/summary?od=${selectedOd}&hours=${hours}`),
      fetch(`/api/prices?od=${selectedOd}&hours=${hours}`),
    ])
    setLatest(await latestRes.json())
    setSummary(await summaryRes.json())
    const pricesData = await pricesRes.json()
    setTimeSeries(pricesData.data || [])
    setLoading(false)
  }, [selectedOd, hours])

  useEffect(() => { fetchData() }, [fetchData])

  const lastScrapeTime = latest?.scraped_at
    ? new Date(latest.scraped_at).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Kolkata' }) + ' IST'
    : '—'

  return (
    <div className="min-h-screen" style={{ background: 'var(--bg)' }}>
      {/* Header */}
      <header className="border-b sticky top-0 z-40 backdrop-blur-md" style={{ borderColor: 'var(--border)', background: 'rgba(8,14,10,0.92)' }}>
        <div className="max-w-screen-xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Xanh SM wordmark */}
            <div className="relative">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'var(--xanh)', boxShadow: '0 0 20px #00d47866' }}>
                <span className="text-black font-black text-xs">X</span>
              </div>
            </div>
            <div>
              <h1 className="font-display font-extrabold text-lg leading-none tracking-tight" style={{ color: 'var(--text)' }}>
                XANH SM
              </h1>
              <p className="text-xs font-mono" style={{ color: 'var(--text-muted)' }}>PRICE INTELLIGENCE</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Last scrape indicator */}
            <div className="hidden sm:flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full animate-pulse-slow" style={{ background: 'var(--xanh)' }} />
              <span className="text-xs font-mono" style={{ color: 'var(--text-muted)' }}>
                Last run: {lastScrapeTime}
              </span>
            </div>

            {/* Hours filter */}
            <div className="flex rounded-lg overflow-hidden border" style={{ borderColor: 'var(--border)' }}>
              {[12, 24, 48].map(h => (
                <button
                  key={h}
                  onClick={() => setHours(h)}
                  className="px-3 py-1.5 text-xs font-mono transition-colors"
                  style={{
                    background: hours === h ? 'var(--xanh-dim)' : 'var(--bg-card)',
                    color: hours === h ? 'var(--xanh)' : 'var(--text-muted)',
                    borderRight: h !== 48 ? `1px solid var(--border)` : 'none',
                  }}
                >
                  {h}h
                </button>
              ))}
            </div>

            <button
              onClick={fetchData}
              className="px-3 py-1.5 rounded-lg text-xs font-mono transition-all active:scale-95"
              style={{ background: 'var(--xanh-dim)', color: 'var(--xanh)', border: '1px solid var(--border-hi)' }}
            >
              ↻ Refresh
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-screen-xl mx-auto px-6 py-8 space-y-8">
        {/* OD Selector + Platform Legend */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <OdSelector pairs={OD_PAIRS} selected={selectedOd} onChange={setSelectedOd} />
          <PlatformLegend />
        </div>

        {/* Summary KPI Cards */}
        <SummaryCards summary={summary?.summary || []} loading={loading} />

        {/* Main grid: chart + table */}
        <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
          {/* Time series chart — wider */}
          <div className="xl:col-span-3">
            <PriceChart data={timeSeries} loading={loading} selectedOd={selectedOd} />
          </div>

          {/* Surge heatmap */}
          <div className="xl:col-span-2">
            <SurgeMap summary={summary?.summary || []} loading={loading} />
          </div>
        </div>

        {/* Latest prices table */}
        <PriceTable data={latest?.data || []} loading={loading} />
      </main>
    </div>
  )
}
