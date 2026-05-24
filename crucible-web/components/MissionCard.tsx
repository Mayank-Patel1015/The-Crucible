import { Mission, DIFFICULTY_CONFIG } from '@/lib/missions'

export default function MissionCard({
  mission,
  alreadyCompleted,
}: {
  mission: Mission
  alreadyCompleted: boolean
}) {
  const diff = DIFFICULTY_CONFIG[mission.difficulty]
  return (
    <div
      className={`border rounded-lg p-6 space-y-5 ${
        alreadyCompleted
          ? 'border-zinc-800 opacity-60'
          : 'border-orange-900/60 bg-zinc-900/50'
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs text-zinc-500 uppercase tracking-widest mb-1">Day {mission.day_number} Mission</p>
          <h2 className="text-2xl font-bold tracking-wider text-zinc-100 uppercase">{mission.title}</h2>
        </div>
        <span className={`shrink-0 text-xs font-bold border rounded px-2 py-1 tracking-widest ${diff.color}`}>
          {diff.label}
        </span>
      </div>
      <p className="text-zinc-400 text-sm leading-relaxed border-l-2 border-orange-800/60 pl-4">
        {mission.description}
      </p>
      <div className="bg-zinc-950/80 border border-zinc-800 rounded-lg p-4">
        <p className="text-xs text-zinc-500 uppercase tracking-widest mb-2">Your Objective</p>
        <p className="text-zinc-200 text-sm leading-relaxed">{mission.objective}</p>
      </div>
      <div className="flex flex-wrap gap-2">
        {mission.tags.map(tag => (
          <span
            key={tag}
            className="text-xs text-zinc-500 border border-zinc-800 rounded px-2 py-0.5 uppercase tracking-widest"
          >
            {tag}
          </span>
        ))}
      </div>
      {mission.example_prompt && !alreadyCompleted && (
        <details className="group">
          <summary className="text-xs text-zinc-600 hover:text-zinc-400 cursor-pointer uppercase tracking-widest select-none">
            ▶ Show scaffold (costs you nothing, teaches you less)
          </summary>
          <div className="mt-3 bg-zinc-950 border border-zinc-800 rounded p-4">
            <pre className="text-xs text-zinc-400 whitespace-pre-wrap leading-relaxed">
              {mission.example_prompt}
            </pre>
          </div>
        </details>
      )}
    </div>
  )
}
