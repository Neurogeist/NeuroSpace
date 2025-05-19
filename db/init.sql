-- Enable pgcrypto for UUID support
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS vector;


-- Sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  wallet_address TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  title TEXT
);

-- Messages table
CREATE TABLE IF NOT EXISTS chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  timestamp TIMESTAMPTZ DEFAULT now(),

  model_name TEXT,
  model_id TEXT,

  ipfs_cid TEXT,
  transaction_hash TEXT,
  verification_hash TEXT,
  signature TEXT,

  message_metadata JSONB
);

-- -----------------------------
-- Free Requests Table
-- -----------------------------

-- Create the table with the updated schema
create table free_requests (
    id uuid primary key default gen_random_uuid(),
    wallet_address text not null unique,
    remaining_requests integer not null default 10,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Add an index on wallet_address for faster lookups
create index free_requests_wallet_address_idx on free_requests(wallet_address);

-- Add a trigger to automatically update the updated_at timestamp
create or replace function update_updated_at_column()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

create trigger update_free_requests_updated_at
    before update on free_requests
    for each row
    execute function update_updated_at_column();

-- -----------------------------
-- Document Uploads Table
-- -----------------------------

CREATE TABLE document_uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id TEXT NOT NULL,
    document_name TEXT NOT NULL,
    ipfs_hash TEXT NOT NULL,
    wallet_address TEXT NOT NULL,
    uploaded_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id TEXT NOT NULL,
    document_name TEXT NOT NULL,
    ipfs_hash TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chunks_embedding
ON document_chunks USING ivfflat (embedding vector_l2_ops)
WITH (lists = 100);

create table flagged_messages (
  id uuid primary key default gen_random_uuid(),
  message_id uuid references chat_messages(id) on delete cascade,
  reason text not null check (reason in ('hallucination', 'inappropriate', 'inaccuracy', 'other')),
  note text,
  wallet_address text,
  flagged_at timestamptz default now()
);
