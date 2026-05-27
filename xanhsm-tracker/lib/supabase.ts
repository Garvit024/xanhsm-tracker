import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseKey)

export type PriceSnapshot = {
  id: number
  scraped_at: string
  scraped_at_ist: string
  platform: string
  od_pair_id: string
  od_label: string
  service_name: string
  price_min: number | null
  price_max: number | null
  price_raw: string | null
  eta_minutes: number | null
  surge_active: number
  surge_mult: number | null
  status: string
  error_msg: string | null
  scrape_run_id: string
}
