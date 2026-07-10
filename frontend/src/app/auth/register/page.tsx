'use client'

import * as React from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/utils/supabase/client'
import { Button } from '@/components/ui/button'
import { BrainCircuit } from 'lucide-react'
import { toast } from 'sonner'
import Link from 'next/link'

export default function RegisterPage() {
  const router = useRouter()
  const supabase = createClient()
  const [email, setEmail] = React.useState('')
  const [password, setPassword] = React.useState('')
  const [loading, setLoading] = React.useState(false)

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`,
      },
    })

    if (error) {
      toast.error(error.message)
      setLoading(false)
      return
    }

    toast.success('Check your email to confirm your account')
    router.push('/auth/login')
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background/50 p-4">
      <div className="w-full max-w-md bg-card border border-border p-8 rounded-2xl shadow-xl">
        <div className="flex items-center gap-2 mb-8 justify-center">
          <div className="bg-foreground text-background p-1.5 rounded-lg">
            <BrainCircuit className="h-6 w-6" />
          </div>
          <span className="font-bold text-xl tracking-tight">TalentIntel AI</span>
        </div>
        
        <h1 className="text-2xl font-bold text-center mb-6 text-foreground">Create an Account</h1>
        
        <form onSubmit={handleRegister} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full bg-background border border-border/60 hover:border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary"
              placeholder="you@example.com"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full bg-background border border-border/60 hover:border-border rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary"
              placeholder="••••••••"
            />
          </div>
          <Button type="submit" disabled={loading} className="w-full font-semibold mt-4 cursor-pointer">
            {loading ? 'Signing up...' : 'Sign Up'}
          </Button>
        </form>

        <div className="mt-6 text-center text-sm text-muted-foreground">
          Already have an account?{' '}
          <Link href="/auth/login" className="text-primary hover:underline font-medium">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  )
}
