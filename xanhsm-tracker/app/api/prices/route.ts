import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

export const revalidate = 300

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const od = searchParams.get('od') || ''
  const platform = searchParams.get('platform') || ''
  const service = searchParams.get('service') || ''
  const hours = parseInt(searchParams.get('hours') || '48')

  const since = new Date(Date.now() - hours * 60 * 60 * 1000).toISOString()

  let query = supabase
    .from('price_snapshots')
    .select('platform, service_name, od_pair_id, od_label, price_min, scraped_at, scraped_at_ist, surge_active, eta_minutes')
    .eq('status', 'ok')
    .gte('scraped_at', since)
    .order('scraped_at', { ascending: true })

  if (od) query = query.eq('od_pair_id', od)
  if (platform) query = query.eq('platform', platform)
  if (service) query = query.eq('service_name', service)

  const { data, error } = await query.limit(5000)
  if (error) return NextResponse.json({ error: error.message }, { status: 500 })

  return NextResponse.json({ data: data || [] })
}
