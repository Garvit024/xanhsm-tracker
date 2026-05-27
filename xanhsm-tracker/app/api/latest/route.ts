import { NextResponse } from 'next/server'
import { supabase } from '@/lib/supabase'

export const revalidate = 60

export async function GET() {
  // Get the most recent scrape_run_id
  const { data: latest } = await supabase
    .from('price_snapshots')
    .select('scrape_run_id, scraped_at')
    .eq('status', 'ok')
    .order('scraped_at', { ascending: false })
    .limit(1)

  if (!latest?.length) return NextResponse.json({ data: [], run_id: null, scraped_at: null })

  const run_id = latest[0].scrape_run_id

  const { data, error } = await supabase
    .from('price_snapshots')
    .select('*')
    .eq('scrape_run_id', run_id)
    .eq('status', 'ok')
    .order('platform')

  if (error) return NextResponse.json({ error: error.message }, { status: 500 })

  return NextResponse.json({
    data: data || [],
    run_id,
    scraped_at: latest[0].scraped_at,
  })
}
