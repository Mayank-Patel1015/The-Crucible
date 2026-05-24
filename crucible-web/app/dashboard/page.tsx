import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import { getTodaysMission } from '@/lib/missions'
import MissionCard from '@/components/MissionCard'
import StreakDisplay from '@/components/StreakDisplay'
import SubmissionForm from '@/components/SubmissionForm'
import CountdownTimer from '@/components/CountdownTimer'

export default async function DashboardPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  const { data: profile } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', user.id)
    .single()

  const mission = getTodaysMission()

  const { data: existingSubmission } = await supabase
    .from('submissions')
    .select('id, submitted_at, prompt_text')
    .eq('user_id', user.id)
    .eq('mission_day', mission.day_number)
    .maybeSingle()

  const alreadyCompleted = !!existingSubmission

  async function handleSignOut() {
    'use server'
    const { createClient } = await import('@/lib/supabase/server')
    const supabase = await createClient()
    await supabase.auth.signOut()
    const { redirect } = await import('next/navigation')
    redirect('/login')
  }

  return (
    <main className="min-h-screen bg-zinc-950 px-4 py-8 md:px-8">
      <header className="max-w-4xl mx-auto mb-10 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-widest text-zinc-100 uppercase">⚔ The Crucible</h1>
          <p className="text-xs text-zinc-500 tracking-widest mt-1 uppercase">Daily AI Skill Forge</p>
        </div>
        <div className="flex items-center gap-6">
          <CountdownTimer />
          <StreakDisplay
            currentStreak={profile?.current_streak ?? 0}
            longestStreak={profile?.longest_streak ?? 0}
          />
          <form action={handleSignOut}>
            <button
              type="submit"
              className="text-xs text-zinc-600 hover:text-zinc-400 uppercase tracking-widest transition-colors"
            >
              Exit
            </button>
          </form>
        </div>
      </header>

      <div className="max-w-4xl mx-auto mb-8">
        <div className="h-px bg-gradient-to-r from-transparent via-orange-500/50 to-transparent" />
      </div>

      <div className="max-w-4xl mx-auto space-y-6">
        <MissionCard mission={mission} alreadyCompleted={alreadyCompleted} />

        {alreadyCompleted ? (
          <div className="border border-green-800/60 bg-green-950/20 rounded-lg p-6 space-y-3">
            <div className="flex items-center gap-3">
              <span className="text-2xl">✓</span>
              <div>
                <p className="font-bold text-green-400 tracking-wide uppercase text-sm">
                  Mission Complete — Streak: {profile?.current_streak ?? 0} day{profile?.current_streak !== 1 ? 's' : ''}
                </p>
                <p className="text-xs text-zinc-500 mt-0.5">
                  Submitted at {new Date(existingSubmission!.submitted_at).toLocaleTimeString()}. Return tomorrow.
                </p>
              </div>
            </div>
            <div className="border border-zinc-800 rounded p-4 bg-zinc-900/60">
              <p className="text-xs text-zinc-500 uppercase tracking-widest mb-2">Your Submission</p>
              <p className="text-sm text-zinc-300 whitespace-pre-wrap leading-relaxed">{existingSubmission!.prompt_text}</p>
            </div>
          </div>
        ) : (
          <SubmissionForm
            missionId={mission.id}
            missionDay={mission.day_number}
            userId={user.id}
          />
        )}

        <div className="grid grid-cols-3 gap-4 pt-4">
          {[
            { label: 'Total Completions', value: profile?.total_completions ?? 0 },
            { label: 'Current Streak', value: `${profile?.current_streak ?? 0}d` },
            { label: 'Best Streak', value: `${profile?.longest_streak ?? 0}d` },
          ].map(({ label, value }) => (
            <div key={label} className="border border-zinc-800 rounded-lg p-4 text-center bg-zinc-900/40">
              <div className="text-2xl font-bold text-orange-400">{value}</div>
              <div className="text-xs text-zinc-500 uppercase tracking-widest mt-1">{label}</div>
            </div>
          ))}
        </div>
      </div>
    </main>
  )
}
