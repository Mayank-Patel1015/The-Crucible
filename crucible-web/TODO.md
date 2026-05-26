3 key things to make the app fully functional
Provision and connect the Supabase backend

Apply schema.sql to your Supabase project so profiles, missions, submissions, the auth trigger, and record_submission_and_update_streak RPC are available.
Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in your environment.
Verify auth/session flow

Confirm page.tsx, page.tsx, page.tsx, and layout.tsx are correctly routing users and protecting the dashboard.
Ensure Supabase auth email confirmation/settings match the signup/login flow, or adjust the signup flow if confirmation is required.
Complete the submission/streak pipeline

Validate route.ts works with the logged-in user and the record_submission_and_update_streak function.
Make sure the mission data in missions.ts aligns with seeded public.missions or switch to DB-backed missions if you want a single source of truth.