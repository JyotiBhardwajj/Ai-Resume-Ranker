-- BACKUP SCRIPT: Run this to restore all three overloads in case of rollback
-- 1. Restore 3-parameter overload
CREATE OR REPLACE FUNCTION public.match_candidates(
  query_embedding vector(3072),
  match_threshold float,
  match_count int
)
RETURNS TABLE (
  candidate_id text,
  profile_data jsonb,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  select
    candidates.candidate_id,
    candidates.profile_data,
    1 - (candidates.embedding <=> query_embedding) as similarity
  from candidates
  where 1 - (candidates.embedding <=> query_embedding) > match_threshold
  order by similarity desc
  limit match_count;
$$;

-- 2. Restore 4-parameter overload
CREATE OR REPLACE FUNCTION public.match_candidates(
  query_embedding vector(3072),
  match_threshold float,
  match_count int,
  p_is_custom boolean
)
RETURNS TABLE (
  candidate_id text,
  profile_data jsonb,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  select
    candidates.candidate_id,
    candidates.profile_data,
    1 - (candidates.embedding <=> query_embedding) as similarity
  from candidates
  where 1 - (candidates.embedding <=> query_embedding) > match_threshold
    and candidates.is_custom = p_is_custom
  order by similarity desc
  limit match_count;
$$;

-- 3. Restore 5-parameter overload
CREATE OR REPLACE FUNCTION public.match_candidates(
  query_embedding vector(3072),
  match_threshold float,
  match_count int,
  p_is_custom boolean,
  p_user_id uuid
)
RETURNS TABLE (
  candidate_id text,
  profile_data jsonb,
  similarity float
)
LANGUAGE sql STABLE
AS $$
  select
    candidates.candidate_id,
    candidates.profile_data,
    1 - (candidates.embedding <=> query_embedding) as similarity
  from candidates
  where 1 - (candidates.embedding <=> query_embedding) > match_threshold
    and candidates.is_custom = p_is_custom
    and (p_user_id is null or candidates.user_id = p_user_id)
  order by similarity desc
  limit match_count;
$$;
