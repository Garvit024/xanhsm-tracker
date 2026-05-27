import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

export const revalidate = 300 // 5 min cache

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const od = searchParams.get('od') || ''
  const hours = parseInt(searchParams.get('hours') || '24')

  const since = new Date(Date.now() - hours * 60 * 60 * 1000).toISOString()

  let query = supabase
    .from('price_snapshots')
    .select('platform, service_name, od_pair_id, od_label, price_min, price_max, scraped_at_ist, surge_active, surge_mult, scrape_run_id')
    .eq('status', 'ok')
    .gte('scraped_at', since)
    .order('scraped_at', { ascending: false })

  if (od) query = query.eq('od_pair_id', od)

  const { data, error } = await query.limit(2000)
  if (error) return NextResponse.json({ error: error.message }, { status: 500 })

  // Aggregate: group by platform × service
  const grouped: Record<string, any> = {}
  for (const row of data || []) {
    const key = `${row.platform}||${row.service_name}||${row.od_pair_id}`
    if (!grouped[key]) {
      grouped[key] = {
        platform: row.platform,
        service_name: row.service_name,
        od_pair_id: row.od_pair_id,
        od_label: row.od_label,
        prices: [],
        surge_count: 0,
        total: 0,
      }
    }
    const g = grouped[key]
    if (row.price_min) g.prices.push(row.price_min)
    if (row.surge_active) g.surge_count++
    g.total++
  }

  const summary = Object.values(grouped).map((g: any) => ({
    platform: g.platform,
    service_name: g.service_name,
    od_pair_id: g.od_pair_id,
    od_label: g.od_label,
    avg_price: g.prices.length ? Math.round(g.prices.reduce((a: number, b: number) => a + b, 0) / g.prices.length) : null,
    min_price: g.prices.length ? Math.round(Math.min(...g.prices)) : null,
    max_price: g.prices.length ? Math.round(Math.max(...g.prices)) : null,
    surge_pct: g.total > 0 ? Math.round((g.surge_count / g.total) * 100) : 0,
    observations: g.total,
  }))

  return NextResponse.json({ summary, since, total_records: data?.length || 0 })
}
