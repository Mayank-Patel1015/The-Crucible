'use client'

import { useState, useTransition } from 'react'
import { useRouter } from 'next/navigation'

export default function SubmissionForm({
  missionId,
  missionDay,
  userId,
}: {
  missionId: string
  missionDay: number
  userId: string
}) {
  const [prompt, setPrompt] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isPending, startTransition] = useTransition()
  const router = useRouter()
  const wordCount = prompt.trim() ? prompt.trim().split(/\s+/).length : 0
  const MIN_WORDS = 15

  async function handleSubmit() {
    if (wordCount < MIN_WORDS) {
      setError(`Minimum ${MIN_WORDS} words required. This is The Crucible, not a tweet.`)
      return
    }
    setError(null)
    startTransition(async () => {
      const res = await fetch('/api/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ missionId, missionDay, userId, promptText: prompt }),
      })
      const data = await res.json()
      if (!res.ok) { setError(data.error ?? 'Submission failed. Try again.'); return }
      router.refresh()
    })
  }

  return (
    <div className="border border-zinc-800 rounded-lg p-6 space-y-4 bg-zinc-900/30">
      <div className="flex items-center justify-between">
        <p className="text-xs text-zinc-500 uppercase tracking-widest">Your Prompt</p>
        <span className={`text-xs tabular-nums ${wordCount < MIN_WORDS ? 'text-zinc-600' : 'text-green-500'}`}>
          {wordCount} words {wordCount < MIN_WORDS ? `(${MIN_WORDS - wordCount} more to go)` : '✓'}
        </span>
      </div>
      <textarea
        value={prompt}
        onChange={e => setPrompt(e.target.value)}
        placeholder="Write your prompt here. Make it count."
        rows={10}
        className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-4 text-sm text-zinc-200 placeholder:text-zinc-700 focus:outline-none focus:border-orange-700 resize-none leading-relaxed transition-colors"
      />
      {error && (
        <p className="text-sm text-red-400 border border-red-900/50 rounded px-3 py-2 bg-red-950/20">✗ {error}</p>
      )}
      <button
        onClick={handleSubmit}
        disabled={isPending || wordCount < MIN_WORDS}
        className="w-full py-3 bg-orange-600 hover:bg-orange-500 disabled:bg-zinc-800 disabled:text-zinc-600 disabled:cursor-not-allowed text-white font-bold uppercase tracking-widest rounded-lg transition-colors text-sm"
      >
        {isPending ? 'FORGING...' : 'SUBMIT MISSION'}
      </button>
      <p className="text-xs text-zinc-600 text-center">Once submitted, you cannot edit. Choose your words.</p>
    </div>
  )
}
