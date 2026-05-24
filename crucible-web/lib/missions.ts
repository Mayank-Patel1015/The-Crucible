export type Difficulty = 'INITIATE' | 'OPERATIVE' | 'SPECIALIST' | 'ELITE'

export interface Mission {
  id: string
  day_number: number
  title: string
  description: string
  objective: string
  difficulty: Difficulty
  tags: string[]
  example_prompt?: string
}

const MISSIONS: Mission[] = [
  {
    id: 'mission-001',
    day_number: 1,
    title: 'THE INTERROGATOR',
    description: "Most people write prompts like they're texting. You're going to write one like you're briefing an expert.",
    objective: 'Write a prompt that extracts a structured 5-point analysis of any topic. The AI must return numbered points, each with a header and 2-sentence explanation. No fluff. No preamble.',
    difficulty: 'INITIATE',
    tags: ['structure', 'formatting', 'output-control'],
    example_prompt: 'Analyze [TOPIC]. Return exactly 5 numbered insights. Format each as: **[INSIGHT TITLE]**: [2-sentence explanation]. Be direct. No preamble.',
  },
  {
    id: 'mission-002',
    day_number: 2,
    title: 'PERSONA FORGE',
    description: 'A generic AI gives generic answers. An AI playing a specific role gives targeted answers. Build the persona.',
    objective: 'Write a system-level persona prompt that transforms the AI into a brutally honest senior engineer with 20 years of experience. Then use it to review a piece of code or technical decision.',
    difficulty: 'INITIATE',
    tags: ['persona', 'role-playing', 'system-prompt'],
  },
  {
    id: 'mission-003',
    day_number: 3,
    title: 'THE CONTRARIAN',
    description: 'Confirmation bias is the enemy of good thinking. Force the AI to fight you.',
    objective: "Write a prompt that forces the AI to steelman the opposite of your stated position. It must give you 3 genuine counterarguments you haven't considered, not weak strawmen.",
    difficulty: 'OPERATIVE',
    tags: ['reasoning', 'chain-of-thought', 'critical-thinking'],
  },
  {
    id: 'mission-004',
    day_number: 4,
    title: 'CHAIN ARCHITECT',
    description: 'One prompt is a sentence. A chain of prompts is a program. Design one.',
    objective: 'Design a 3-step prompt chain where each output feeds the next. Document what each step does and why the order matters. The chain must produce something neither step alone could.',
    difficulty: 'OPERATIVE',
    tags: ['chaining', 'workflow', 'multi-step'],
  },
  {
    id: 'mission-005',
    day_number: 5,
    title: 'THE COMPRESSOR',
    description: 'Verbosity is a crutch. Constraint is a skill.',
    objective: 'Take any complex task and write a prompt that accomplishes it in under 25 words. The output must still be specific, structured, and useful. Prove that brevity is power.',
    difficulty: 'SPECIALIST',
    tags: ['brevity', 'constraint', 'precision'],
  },
]

export function getTodaysMission(): Mission {
  const index = Math.floor(Date.now() / 86_400_000) % MISSIONS.length
  return MISSIONS[index]
}

export const DIFFICULTY_CONFIG: Record<Difficulty, { color: string; label: string }> = {
  INITIATE:   { color: 'text-green-400 border-green-800 bg-green-950/30',    label: '◈ INITIATE' },
  OPERATIVE:  { color: 'text-yellow-400 border-yellow-800 bg-yellow-950/30', label: '◈ OPERATIVE' },
  SPECIALIST: { color: 'text-orange-400 border-orange-800 bg-orange-950/30', label: '◈ SPECIALIST' },
  ELITE:      { color: 'text-red-400 border-red-800 bg-red-950/30',          label: '◈ ELITE' },
}
