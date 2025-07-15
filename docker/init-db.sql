-- Dreamcatcher Database Initialization
-- Creates initial database structure and sample data

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
CREATE TYPE idea_source_type AS ENUM ('voice', 'text', 'dream', 'image');
CREATE TYPE idea_category AS ENUM ('creative', 'business', 'personal', 'metaphysical', 'utility');
CREATE TYPE processing_status AS ENUM ('pending', 'processing', 'completed', 'failed');
CREATE TYPE proposal_status AS ENUM ('pending', 'approved', 'rejected', 'in_progress', 'completed');

-- Insert initial tags
INSERT INTO tags (name, color, description) VALUES
('urgent', '#ef4444', 'High priority ideas that need immediate attention'),
('creative', '#8b5cf6', 'Creative and artistic ideas'),
('business', '#10b981', 'Business and entrepreneurial concepts'),
('tech', '#3b82f6', 'Technology and software ideas'),
('personal', '#f59e0b', 'Personal development and lifestyle ideas'),
('dream', '#ec4899', 'Ideas from dreams and subconscious'),
('experimental', '#6b7280', 'Experimental or untested concepts'),
('brilliant', '#fbbf24', 'Exceptionally good ideas'),
('draft', '#9ca3af', 'Work in progress ideas'),
('inspiration', '#f97316', 'Inspirational or motivational ideas')
ON CONFLICT (name) DO NOTHING;

-- Insert initial agents
INSERT INTO agents (id, name, description, version, config, is_active) VALUES
(
    'listener',
    'Capture Agent',
    'I heard something. Logging it now.',
    '1.0.0',
    '{"whisper_model": "base", "auto_capture": false}',
    true
),
(
    'classifier',
    'Analysis Agent',
    'I''m not saying this is another ADHD thought spiral, but... yeah it is. Categorized under ''You Might Actually Build This.''',
    '1.0.0',
    '{"urgency_threshold": 70, "novelty_threshold": 80}',
    true
),
(
    'expander',
    'Expansion Agent',
    'Let me take that spark and turn it into a full flame.',
    '1.0.0',
    '{"max_expansions": 3, "preferred_model": "claude"}',
    true
),
(
    'visualizer',
    'Visual Agent',
    'Darling, that idea needs a visual. Let me handle it.',
    '1.0.0',
    '{"default_style": "modern", "image_size": "1024x1024"}',
    true
),
(
    'proposer',
    'Proposal Agent',
    'Proposal generated. Here''s a structured plan with bullet points, deadlines, and passive income streams.',
    '1.0.0',
    '{"min_viability_score": 75, "include_timeline": true}',
    true
),
(
    'reviewer',
    'Review Agent',
    'Time to revisit a hidden gem from your archives.',
    '1.0.0',
    '{"review_interval_days": 7, "min_dormant_score": 80}',
    true
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    version = EXCLUDED.version,
    config = EXCLUDED.config,
    is_active = EXCLUDED.is_active,
    updated_at = CURRENT_TIMESTAMP;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_ideas_created_at ON ideas(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ideas_urgency_score ON ideas(urgency_score DESC);
CREATE INDEX IF NOT EXISTS idx_ideas_source_type ON ideas(source_type);
CREATE INDEX IF NOT EXISTS idx_ideas_category ON ideas(category);
CREATE INDEX IF NOT EXISTS idx_ideas_processing_status ON ideas(processing_status);

CREATE INDEX IF NOT EXISTS idx_agent_logs_started_at ON agent_logs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_logs_agent_id ON agent_logs(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_logs_status ON agent_logs(status);

CREATE INDEX IF NOT EXISTS idx_proposals_status ON proposals(status);
CREATE INDEX IF NOT EXISTS idx_proposals_created_at ON proposals(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_system_metrics_metric_name ON system_metrics(metric_name);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_ideas_updated_at BEFORE UPDATE ON ideas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_proposals_updated_at BEFORE UPDATE ON proposals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for development (commented out for production)
-- INSERT INTO ideas (content_raw, source_type, category, urgency_score, novelty_score, processing_status) VALUES
-- ('AI-powered morning routine optimizer that learns your patterns', 'text', 'utility', 75.0, 80.0, 'completed'),
-- ('Dream journal with pattern recognition and lucid dreaming triggers', 'dream', 'metaphysical', 85.0, 90.0, 'completed'),
-- ('Voice-activated meditation timer with binaural beats', 'voice', 'personal', 65.0, 70.0, 'completed');

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE dreamcatcher TO dreamcatcher;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO dreamcatcher;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO dreamcatcher;

-- Log database initialization
INSERT INTO system_metrics (metric_name, metric_value, metric_type, labels) VALUES
('database_initialized', 1, 'counter', '{"version": "1.0.0", "timestamp": "' || CURRENT_TIMESTAMP || '"}');

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Dreamcatcher database initialized successfully!';
    RAISE NOTICE 'Agents registered: %', (SELECT COUNT(*) FROM agents WHERE is_active = true);
    RAISE NOTICE 'Tags available: %', (SELECT COUNT(*) FROM tags);
END $$;