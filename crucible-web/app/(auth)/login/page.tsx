'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [unconfirmed, setUnconfirmed] = useState(false)
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const supabase = createClient()

  async function handleLogin() {
    setLoading(true)
    setError(null)
    setUnconfirmed(false)
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) {
      if (error.message.toLowerCase().includes('email not confirmed')) {
        setUnconfirmed(true)
      } else {
        setError(error.message)
      }
      setLoading(false)
      return
    }
    router.push('/dashboard')
    router.refresh()
  }

  return (
    <main className="min-h-screen bg-zinc-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-widest text-zinc-100 uppercase">⚔ The Crucible</h1>
          <p className="text-zinc-500 text-sm mt-2 tracking-widest uppercase">Prove you belong here</p>
        </div>
        <div className="border border-zinc-800 rounded-lg p-8 bg-zinc-900/40 space-y-6">
          <div className="space-y-4">
            <div>
              <label className="text-xs text-zinc-500 uppercase tracking-widest block mb-1.5">Email</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-3 text-sm text-zinc-200 focus:outline-none focus:border-orange-700 transition-colors"
                placeholder="operator@crucible.io"
              />
            </div>
            <div>
              <label className="text-xs text-zinc-500 uppercase tracking-widest block mb-1.5">Password</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleLogin()}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-3 text-sm text-zinc-200 focus:outline-none focus:border-orange-700 transition-colors"
                placeholder="••••••••"
              />
            </div>
          </div>
          {unconfirmed && (
            <div className="text-sm border border-yellow-800/60 rounded px-3 py-3 bg-yellow-950/20 space-y-1">
              <p className="text-yellow-400 font-bold uppercase tracking-wide text-xs">⚠ Email Not Confirmed</p>
              <p className="text-yellow-200/70">Check your inbox and click the confirmation link before logging in.</p>
            </div>
          )}
          {error && (
            <p className="text-sm text-red-400 border border-red-900/50 rounded px-3 py-2 bg-red-950/20">✗ {error}</p>
          )}
          <button
            onClick={handleLogin}
            disabled={loading}
            className="w-full py-3 bg-orange-600 hover:bg-orange-500 disabled:bg-zinc-800 disabled:text-zinc-600 text-white font-bold uppercase tracking-widest rounded-lg transition-colors text-sm"
          >
            {loading ? 'AUTHENTICATING...' : 'ENTER THE CRUCIBLE'}
          </button>
          <p className="text-center text-xs text-zinc-600">
            No account?{' '}
            <Link href="/signup" className="text-orange-500 hover:text-orange-400 uppercase tracking-widest">
              Enlist
            </Link>
          </p>
        </div>
      </div>
    </main>
  )
}
