-- MIGRATION SCRIPT: Run this to resolve PostgREST RPC overloading conflict PGRST203
-- This drops the obsolete 3-parameter and 5-parameter overloads of match_candidates
-- and ensures only the correct 4-parameter version exists.

-- 1. Drop the obsolete 3-parameter overload
DROP FUNCTION IF EXISTS public.match_candidates(vector, double precision, integer);

-- 2. Drop the obsolete 5-parameter overload (with p_user_id)
DROP FUNCTION IF EXISTS public.match_candidates(vector, double precision, integer, boolean, uuid);

-- 3. Drop the 4-parameter overload first to avoid defaults conflict (42P13)
DROP FUNCTION IF EXISTS public.match_candidates(vector, double precision, integer, boolean);

-- 4. Create the 4-parameter overload exactly as expected
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
