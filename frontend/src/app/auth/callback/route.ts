import { NextResponse } from 'next/server'
import { createClient } from '@/utils/supabase/server'

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url)
  const code = searchParams.get('code')
  const error_description = searchParams.get('error_description')
  
  // if "next" is in param, use it as the redirect URL
  const next = searchParams.get('next') ?? '/jd-analysis'

  // If Supabase returned an error in the callback URL
  if (error_description) {
    return NextResponse.redirect(`${origin}/auth/login?error=${encodeURIComponent(error_description)}`)
  }

  if (code) {
    const supabase = await createClient()
    const { error } = await supabase.auth.exchangeCodeForSession(code)
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`)
    }
  }

  // Return the user to an error page if no code was found or exchange failed
  return NextResponse.redirect(`${origin}/auth/login?error=Authentication failed`)
}
