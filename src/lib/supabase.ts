import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    "Missing NEXT_PUBLIC_SUPABASE_URL / NEXT_PUBLIC_SUPABASE_ANON_KEY. Copy .env.local.example to .env.local and fill in values from the Supabase dashboard (Settings -> API).",
  );
}

// Anon key only — read-only per RLS policies. Never import the service_role
// key here: it belongs to the Python pipeline's environment (CLAUDE.md, A02).
export const supabase = createClient(supabaseUrl, supabaseAnonKey);
