import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'

export async function POST(req: NextRequest) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { missionId, missionDay, promptText } = await req.json()
  if (!missionId || !missionDay || !promptText?.trim())
    return NextResponse.json({ error: 'Missing required fields' }, { status: 400 })

  const wordCount = promptText.trim().split(/\s+/).length
  if (wordCount < 15)
    return NextResponse.json({ error: 'Minimum 15 words required' }, { status: 400 })

  const { data, error } = await supabase.rpc('record_submission_and_update_streak', {
    p_user_id: user.id,
    p_mission_id: missionId,
    p_mission_day: missionDay,
    p_prompt_text: promptText.trim(),
    p_word_count: wordCount,
  })

  if (error) return NextResponse.json({ error: error.message }, { status: 400 })
  return NextResponse.json({ success: true, ...data })
}
