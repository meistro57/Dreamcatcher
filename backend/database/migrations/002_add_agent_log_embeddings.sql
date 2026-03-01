-- Add embedding support for agent logs to enable semantic search over operational history.

CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE agent_logs ADD COLUMN IF NOT EXISTS content_embedding vector(384);
ALTER TABLE agent_logs ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(255);
ALTER TABLE agent_logs ADD COLUMN IF NOT EXISTS embedding_updated_at TIMESTAMP WITH TIME ZONE;

CREATE INDEX IF NOT EXISTS agent_logs_embedding_idx
    ON agent_logs USING ivfflat (content_embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS agent_logs_embedding_model_idx
    ON agent_logs (embedding_model);

CREATE INDEX IF NOT EXISTS agent_logs_embedding_updated_at_idx
    ON agent_logs (embedding_updated_at);
