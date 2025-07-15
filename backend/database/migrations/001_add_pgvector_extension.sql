-- Add pgvector extension for vector similarity search
-- This migration adds the pgvector extension and updates the ideas table
-- to support semantic search with vector embeddings

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding columns to ideas table
ALTER TABLE ideas ADD COLUMN IF NOT EXISTS content_embedding vector(384);
ALTER TABLE ideas ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(255);
ALTER TABLE ideas ADD COLUMN IF NOT EXISTS embedding_updated_at TIMESTAMP WITH TIME ZONE;

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS ideas_embedding_idx ON ideas USING ivfflat (content_embedding vector_cosine_ops);

-- Create index for embedding model
CREATE INDEX IF NOT EXISTS ideas_embedding_model_idx ON ideas (embedding_model);

-- Create index for embedding update timestamp
CREATE INDEX IF NOT EXISTS ideas_embedding_updated_at_idx ON ideas (embedding_updated_at);

-- Create function to calculate cosine similarity
CREATE OR REPLACE FUNCTION cosine_similarity(a vector, b vector) RETURNS float AS $$
    SELECT 1 - (a <=> b);
$$ LANGUAGE sql;

-- Create function to find similar ideas
CREATE OR REPLACE FUNCTION find_similar_ideas(
    query_embedding vector(384),
    user_id_param TEXT,
    similarity_threshold FLOAT DEFAULT 0.5,
    result_limit INTEGER DEFAULT 10
) RETURNS TABLE (
    id TEXT,
    content_processed TEXT,
    content_transcribed TEXT,
    content_raw TEXT,
    category TEXT,
    urgency_score FLOAT,
    novelty_score FLOAT,
    viability_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE,
    is_favorite BOOLEAN,
    is_archived BOOLEAN,
    similarity_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        i.id,
        i.content_processed,
        i.content_transcribed,
        i.content_raw,
        i.category,
        i.urgency_score,
        i.novelty_score,
        i.viability_score,
        i.created_at,
        i.is_favorite,
        i.is_archived,
        cosine_similarity(i.content_embedding, query_embedding) as similarity_score
    FROM ideas i
    WHERE i.user_id = user_id_param
        AND i.is_archived = false
        AND i.content_embedding IS NOT NULL
        AND cosine_similarity(i.content_embedding, query_embedding) >= similarity_threshold
    ORDER BY similarity_score DESC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- Create function to get embedding statistics
CREATE OR REPLACE FUNCTION get_embedding_stats() RETURNS TABLE (
    total_ideas INTEGER,
    ideas_with_embeddings INTEGER,
    coverage_percentage FLOAT,
    model_stats JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*)::INTEGER FROM ideas WHERE is_archived = false) as total_ideas,
        (SELECT COUNT(*)::INTEGER FROM ideas WHERE content_embedding IS NOT NULL AND is_archived = false) as ideas_with_embeddings,
        CASE 
            WHEN (SELECT COUNT(*) FROM ideas WHERE is_archived = false) > 0 THEN
                (SELECT COUNT(*)::FLOAT FROM ideas WHERE content_embedding IS NOT NULL AND is_archived = false) / 
                (SELECT COUNT(*)::FLOAT FROM ideas WHERE is_archived = false) * 100
            ELSE 0
        END as coverage_percentage,
        (SELECT jsonb_object_agg(embedding_model, model_count) 
         FROM (
             SELECT embedding_model, COUNT(*) as model_count
             FROM ideas 
             WHERE content_embedding IS NOT NULL AND is_archived = false
             GROUP BY embedding_model
         ) model_stats_query) as model_stats;
END;
$$ LANGUAGE plpgsql;

-- Add comments for documentation
COMMENT ON COLUMN ideas.content_embedding IS 'Vector embedding for semantic search using sentence-transformers';
COMMENT ON COLUMN ideas.embedding_model IS 'Name of the model used to generate the embedding';
COMMENT ON COLUMN ideas.embedding_updated_at IS 'Timestamp when the embedding was last updated';

COMMENT ON FUNCTION find_similar_ideas(vector, TEXT, FLOAT, INTEGER) IS 'Find ideas similar to a query embedding using cosine similarity';
COMMENT ON FUNCTION get_embedding_stats() IS 'Get statistics about embedding coverage and model usage';
COMMENT ON FUNCTION cosine_similarity(vector, vector) IS 'Calculate cosine similarity between two vectors';

-- Create trigger to update embedding_updated_at when embedding changes
CREATE OR REPLACE FUNCTION update_embedding_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.content_embedding IS DISTINCT FROM OLD.content_embedding THEN
        NEW.embedding_updated_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER ideas_embedding_timestamp_trigger
    BEFORE UPDATE ON ideas
    FOR EACH ROW
    EXECUTE FUNCTION update_embedding_timestamp();

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO dreamcatcher;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO dreamcatcher;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO dreamcatcher;