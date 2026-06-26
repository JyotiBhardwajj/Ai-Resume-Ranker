-- Enable the pgvector extension to work with embedding vectors
create extension if not exists vector;

-- Drop existing table and function if they exist to reset the schema
drop table if exists candidates cascade;
drop function if exists match_candidates cascade;

-- Create a table to store candidate profiles and their embeddings
create table if not exists candidates (
  id serial primary key,
  candidate_id text not null unique,
  profile_data jsonb not null,
  -- gemini-embedding-2 outputs 3072 dimensions (not 768)
  embedding vector(3072)
);


-- Create a function to search for candidates using cosine similarity
create or replace function match_candidates (
  query_embedding vector(3072),
  match_threshold float,
  match_count int,
  p_is_custom boolean
)
returns table (
  candidate_id text,
  profile_data jsonb,
  similarity float
)
language sql stable
as $$
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
