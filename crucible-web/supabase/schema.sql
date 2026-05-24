-- PROFILES
create table public.profiles (
  id                uuid primary key references auth.users(id) on delete cascade,
  username          text unique not null,
  email             text not null,
  current_streak    int not null default 0,
  longest_streak    int not null default 0,
  total_completions int not null default 0,
  last_completed_date date,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);

alter table public.profiles enable row level security;

create policy "Users can view their own profile"
  on public.profiles for select using (auth.uid() = id);

create policy "Users can update their own profile"
  on public.profiles for update using (auth.uid() = id);

create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, email, username)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data->>'username', split_part(new.email, '@', 1))
  );
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- MISSIONS
create table public.missions (
  id            uuid primary key default gen_random_uuid(),
  day_number    int unique not null,
  title         text not null,
  description   text not null,
  objective     text not null,
  difficulty    text not null check (difficulty in ('INITIATE','OPERATIVE','SPECIALIST','ELITE')),
  tags          text[] not null default '{}',
  example_prompt text,
  created_at    timestamptz not null default now()
);

alter table public.missions enable row level security;
create policy "Anyone can read missions" on public.missions for select using (true);

-- SUBMISSIONS
create table public.submissions (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid not null references public.profiles(id) on delete cascade,
  mission_id   uuid not null references public.missions(id) on delete cascade,
  mission_day  int not null,
  prompt_text  text not null,
  word_count   int not null,
  submitted_at timestamptz not null default now(),
  unique(user_id, mission_day)
);

alter table public.submissions enable row level security;

create policy "Users can insert their own submissions"
  on public.submissions for insert with check (auth.uid() = user_id);

create policy "Users can view their own submissions"
  on public.submissions for select using (auth.uid() = user_id);

-- STREAK FUNCTION
create or replace function public.record_submission_and_update_streak(
  p_user_id     uuid,
  p_mission_id  uuid,
  p_mission_day int,
  p_prompt_text text,
  p_word_count  int
)
returns json language plpgsql security definer as $$
declare
  v_profile    public.profiles%rowtype;
  v_today      date := current_date;
  v_yesterday  date := current_date - interval '1 day';
  v_new_streak int;
  v_new_longest int;
begin
  if exists (
    select 1 from public.submissions
    where user_id = p_user_id and mission_day = p_mission_day
  ) then
    raise exception 'Already submitted for this mission';
  end if;

  insert into public.submissions (user_id, mission_id, mission_day, prompt_text, word_count)
  values (p_user_id, p_mission_id, p_mission_day, p_prompt_text, p_word_count);

  select * into v_profile from public.profiles where id = p_user_id;

  if v_profile.last_completed_date = v_yesterday then
    v_new_streak := v_profile.current_streak + 1;
  elsif v_profile.last_completed_date = v_today then
    raise exception 'Already completed today';
  else
    v_new_streak := 1;
  end if;

  v_new_longest := greatest(v_profile.longest_streak, v_new_streak);

  update public.profiles set
    current_streak      = v_new_streak,
    longest_streak      = v_new_longest,
    total_completions   = total_completions + 1,
    last_completed_date = v_today,
    updated_at          = now()
  where id = p_user_id;

  return json_build_object('new_streak', v_new_streak, 'longest_streak', v_new_longest);
end;
$$;

-- SEED MISSIONS
insert into public.missions (day_number, title, description, objective, difficulty, tags, example_prompt) values
(1,'THE INTERROGATOR','Most people write prompts like they''re texting. You''re going to write one like you''re briefing an expert.','Write a prompt that extracts a structured 5-point analysis of any topic. The AI must return numbered points, each with a header and 2-sentence explanation. No fluff. No preamble.','INITIATE',ARRAY['structure','formatting','output-control'],'Analyze [TOPIC]. Return exactly 5 numbered insights. Format each as: **[INSIGHT TITLE]**: [2-sentence explanation]. Be direct. No preamble.'),
(2,'PERSONA FORGE','A generic AI gives generic answers. An AI playing a specific role gives targeted answers. Build the persona.','Write a system-level persona prompt that transforms the AI into a brutally honest senior engineer with 20 years of experience. Then use it to review a piece of code or technical decision.','INITIATE',ARRAY['persona','role-playing','system-prompt'],null),
(3,'THE CONTRARIAN','Confirmation bias is the enemy of good thinking. Force the AI to fight you.','Write a prompt that forces the AI to steelman the opposite of your stated position. It must give you 3 genuine counterarguments you haven''t considered, not weak strawmen.','OPERATIVE',ARRAY['reasoning','chain-of-thought','critical-thinking'],null),
(4,'CHAIN ARCHITECT','One prompt is a sentence. A chain of prompts is a program. Design one.','Design a 3-step prompt chain where each output feeds the next. Document what each step does and why the order matters. The chain must produce something neither step alone could.','OPERATIVE',ARRAY['chaining','workflow','multi-step'],null),
(5,'THE COMPRESSOR','Verbosity is a crutch. Constraint is a skill.','Take any complex task and write a prompt that accomplishes it in under 25 words. The output must still be specific, structured, and useful. Prove that brevity is power.','SPECIALIST',ARRAY['brevity','constraint','precision'],null);
