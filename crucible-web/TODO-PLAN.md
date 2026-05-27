# crucible-web — Execution Plan

Based on TODO.md. Three tasks to make the app fully functional, ordered by dependency.

---

## Task 1 — Provision & Connect Supabase Backend

**Blocks everything else. Do this first.**

### Steps

1. **Create a Supabase project** at https://supabase.com (free tier is fine).

2. **Apply the schema** — open the SQL Editor in your Supabase dashboard, paste the full contents of `supabase/schema.sql`, and run it. This creates:
   - `profiles` table + `handle_new_user` trigger
   - `missions` table + seeded rows (5 missions with UUIDs)
   - `submissions` table
   - `record_submission_and_update_streak` RPC

3. **Create `.env.local`** in `crucible-web/` (copy from `.env.local.example`):
   ```
   NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
   SUPABASE_SERVICE_ROLE_KEY=eyJ...   # only needed for admin scripts, not runtime
   ```
   Get these from: Supabase dashboard → Settings → API.

4. **Verify** by running `npm run dev` and checking the browser console for Supabase errors. A clean load with no auth errors means it's connected.

### Acceptance Criteria
- `npm run dev` loads without Supabase connection errors in console
- The SQL editor shows all tables and the RPC in Supabase dashboard

---

## Task 2 — Fix the Signup Flow (Email Confirmation Gap)

**Current bug:** `signup/page.tsx` calls `router.push('/dashboard')` immediately after `signUp()`, but if Supabase requires email confirmation the user isn't authenticated — middleware redirects them back to `/login` with no explanation.

### Option A — Disable email confirmation (fastest for solo dev)
In Supabase dashboard → Authentication → Email → disable "Confirm email". Users can log in immediately after signup.

### Option B — Add a confirmation landing state (better UX)
In `signup/page.tsx`, after a successful `signUp()` response, check whether a session was returned:

```typescript
const { data, error } = await supabase.auth.signUp({ ... })
if (error) { setError(error.message); setLoading(false); return }

// If no session, email confirmation is required
if (!data.session) {
  // Show "Check your inbox" message instead of pushing to dashboard
  setConfirmationSent(true)
  setLoading(false)
  return
}
router.push('/dashboard')
router.refresh()
```

Add a `confirmationSent` state and render a confirmation message when true.

### Verify Auth Flow
After fixing signup, test the full loop:
1. Sign up with a new email → should land on dashboard (Option A) or show confirmation message (Option B)
2. Log out → redirected to `/login`
3. Log back in → redirected to `/dashboard`
4. Visit `/dashboard` unauthenticated → redirected to `/login` ✓ (middleware already handles this)
5. Visit `/login` while authenticated → redirected to `/dashboard` ✓ (middleware already handles this)

### Acceptance Criteria
- New user can complete signup and reach the dashboard without a confusing redirect loop
- Auth guard (`middleware.ts` + `dashboard/layout.tsx`) still blocks unauthenticated access

---

## Task 3 — Fix the Submission / Streak Pipeline

**Current bug:** `mission.id` in `missions.ts` is a static string like `'mission-001'`, but `record_submission_and_update_streak` expects a real Postgres UUID for `p_mission_id`. Submissions will fail with a Postgres type error.

### Fix — Switch dashboard to DB-backed missions (recommended)

After seeding `supabase/schema.sql`, the `missions` table contains real UUIDs. Update `dashboard/page.tsx` to fetch today's mission from Supabase instead of the static `missions.ts` function:

```typescript
// In DashboardPage — replace getTodaysMission() with a DB fetch
const todayIndex = Math.floor(Date.now() / 86_400_000) % 5
const { data: mission } = await supabase
  .from('missions')
  .select('*')
  .eq('day_number', todayIndex + 1)
  .single()

if (!mission) redirect('/login') // shouldn't happen after seeding
```

Now `mission.id` is the real UUID, and `SubmissionForm` passes it correctly to `/api/submit`.

### Alternative Fix — Keep static missions, pass `mission_day` only
If you prefer to keep `missions.ts` as the source of truth, remove `p_mission_id` from the RPC call and look up the mission UUID server-side in `route.ts`:

```typescript
// In api/submit/route.ts — resolve UUID server-side
const { data: missionRow } = await supabase
  .from('missions')
  .select('id')
  .eq('day_number', missionDay)
  .single()

if (!missionRow) return NextResponse.json({ error: 'Mission not found' }, { status: 404 })
// then use missionRow.id as p_mission_id
```

### Verify the Full Pipeline
1. Log in and navigate to `/dashboard`
2. Submit a prompt (≥15 words)
3. The page should refresh and show "Mission Complete" with streak count
4. Check Supabase dashboard → Table Editor → `submissions` to confirm the row was inserted
5. Check `profiles` table to confirm `current_streak` incremented

### Acceptance Criteria
- Submitting a prompt creates a row in `submissions`
- `profiles.current_streak` increments correctly
- Submitting a second time the same day returns "Already completed today" error
- Streak resets to 1 if a day is skipped (test by temporarily changing `last_completed_date` in the DB)

---

## Recommended Order

```
Task 1 (Supabase)  →  Task 2 (signup fix)  →  Task 3 (submission fix)
     ~15 min              ~20 min                   ~30 min
```

Total: ~1 hour to a fully working app.
