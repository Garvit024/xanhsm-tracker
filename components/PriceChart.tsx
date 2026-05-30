'use client'

import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, ReferenceLine,
} from 'recharts'
import { useMemo } from 'react'

const PLATFORM_COLORS: Record<string, string> = {
  uber: '#06b6d4',
  ola: '#f59e0b',
  rapido: '#f43f5e',
}

const BUDGET_SERVICES = ['UberGo', 'Mini', 'Bike', 'Auto', 'Cab Economy']

export function PriceChart({ data, loading, selectedOd }: {
  data: any[]
  loading: boolean
  selectedOd: string
}) {
  // Build time-bucketed series: group by scraped_at_ist → platform avg
  const chartData = useMemo(() => {
    // Filter to budget-tier services for a fair comparison
    const filtered = data.filter(d =>
      BUDGET_SERVICES.some(s => d.service_name?.toLowerCase().includes(s.toLowerCase()))
    )

    const byTime: Record<string, Record<string, number[]>> = {}
    for (const d of filtered) {
      const t = d.scraped_at_ist || d.scraped_at?.slice(11, 16)
      if (!t || d.price_min == null) continue
      if (!byTime[t]) byTime[t] = {}
      if (!byTime[t][d.platform]) byTime[t][d.platform] = []
      byTime[t][d.platform].push(d.price_min)
    }

    return Object.entries(byTime)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([time, platforms]) => ({
        time,
        ...Object.fromEntries(
          Object.entries(platforms).map(([p, prices]) => [
            p, Math.round(prices.reduce((a, b) => a + b, 0) / prices.length)
          ])
        ),
      }))
  }, [data])

  const platforms = ['uber', 'ola', 'rapido']

  return (
    <div className="card p-5 h-full" style={{ minHeight: 320 }}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="font-display font-bold text-base" style={{ color: 'var(--text)' }}>
            Price Over Time
          </h2>
          <p className="text-xs font-mono mt-0.5" style={{ color: 'var(--text-muted)' }}>
            Budget category · avg fare by time slot
          </p>
        </div>
        <div className="text-xs font-mono px-2 py-1 rounded" style={{ background: 'var(--bg-hover)', color: 'var(--text-dim)' }}>
          {chartData.length} data points
        </div>
      </div>

      {loading ? (
        <div className="animate-pulse rounded-xl h-52" style={{ background: 'var(--bg-hover)' }} />
      ) : chartData.length === 0 ? (
        <div className="flex items-center justify-center h-52">
          <p className="text-sm font-mono" style={{ color: 'var(--text-dim)' }}>No chart data yet</p>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={chartData} margin={{ top: 4, right: 4, bottom: 4, left: -8 }}>
            <XAxis
              dataKey="time"
              tick={{ fontSize: 10, fill: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}
              axisLine={{ stroke: 'var(--border)' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 10, fill: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}
              axisLine={false}
              tickLine={false}
              tickFormatter={v => `₹${v}`}
            />
            <Tooltip
              contentStyle={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border)',
                borderRadius: 8,
                fontFamily: 'var(--font-mono)',
                fontSize: 12,
                color: 'var(--text)',
              }}
              formatter={(val: any, name: string) => [`₹${val}`, name.toUpperCase()]}
              labelStyle={{ color: 'var(--text-muted)', marginBottom: 4 }}
            />
            {platforms.map(p => (
              <Line
                key={p}
                type="monotone"
                dataKey={p}
                stroke={PLATFORM_COLORS[p]}
                strokeWidth={2}
                dot={{ r: 3, fill: PLATFORM_COLORS[p], strokeWidth: 0 }}
                activeDot={{ r: 5, strokeWidth: 0 }}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
