import { createClient } from "@supabase/supabase-js";

export const DEMO_WORKSPACE_ID = "11111111-1111-1111-1111-111111111111";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || "https://abxrlygkwribbfmfluly.supabase.co";
const supabasePublishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY || "sb_publishable_VIergH-NgPerMT5py9UwsA_JtLpSh1h";

export const supabase = createClient(supabaseUrl, supabasePublishableKey, {
  auth: { persistSession: false, autoRefreshToken: false },
});
