'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'

export default function SignupPage() {
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const supabase = createClient()

  async function handleSignup() {
    setLoading(true)
    setError(null)
    if (username.trim().length < 3) {
      setError('Username must be at least 3 characters')
      setLoading(false)
      return
    }
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { username: username.trim() } },
    })
    if (error) { setError(error.message); setLoading(false); return }
    router.push('/dashboard')
    router.refresh()
  }

  return (
    <main className="min-h-screen bg-zinc-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-widest text-zinc-100 uppercase">⚔ The Crucible</h1>
          <p className="text-zinc-500 text-sm mt-2 tracking-widest uppercase">Forge your identity</p>
        </div>
        <div className="border border-zinc-800 rounded-lg p-8 bg-zinc-900/40 space-y-6">
          <div className="space-y-4">
            <div>
              <label className="text-xs text-zinc-500 uppercase tracking-widest block mb-1.5">Username</label>
              <input
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-3 text-sm text-zinc-200 focus:outline-none focus:border-orange-700 transition-colors"
                placeholder="your_callsign"
              />
            </div>
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
                onKeyDown={e => e.key === 'Enter' && handleSignup()}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-3 text-sm text-zinc-200 focus:outline-none focus:border-orange-700 transition-colors"
                placeholder="min 6 characters"
              />
            </div>
          </div>
          {error && (
            <p className="text-sm text-red-400 border border-red-900/50 rounded px-3 py-2 bg-red-950/20">✗ {error}</p>
          )}
          <button
            onClick={handleSignup}
            disabled={loading}
            className="w-full py-3 bg-orange-600 hover:bg-orange-500 disabled:bg-zinc-800 disabled:text-zinc-600 text-white font-bold uppercase tracking-widest rounded-lg transition-colors text-sm"
          >
            {loading ? 'ENLISTING...' : 'BEGIN TRAINING'}
          </button>
          <p className="text-center text-xs text-zinc-600">
            Already enlisted?{' '}
            <Link href="/login" className="text-orange-500 hover:text-orange-400 uppercase tracking-widest">
              Enter
            </Link>
          </p>
        </div>
      </div>
    </main>
  )
}
