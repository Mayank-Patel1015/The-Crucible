export default function StreakDisplay({
  currentStreak,
  longestStreak,
}: {
  currentStreak: number
  longestStreak: number
}) {
  return (
    <div className="flex flex-col items-end">
      <div className={`flex items-center gap-1.5 ${currentStreak > 0 ? 'streak-ember' : ''}`}>
        <span className="text-xl">{currentStreak > 0 ? '🔥' : '💀'}</span>
        <span className="text-2xl font-bold text-orange-400 tabular-nums">{currentStreak}</span>
      </div>
      <p className="text-xs text-zinc-600 uppercase tracking-widest">streak · best {longestStreak}</p>
    </div>
  )
}
