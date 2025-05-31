-- PostgreSQL schema for citation graph platform
-- User management, sessions, and structured data

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- User and firm management
CREATE TABLE firms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    short_name VARCHAR(50),
    bar_number VARCHAR(100),
    jurisdiction VARCHAR(10),
    practice_areas TEXT[], -- Array of practice areas
    subscription_tier VARCHAR(50) DEFAULT 'basic',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    firm_id UUID REFERENCES firms(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'attorney', -- attorney, paralegal, admin, associate, partner, guest
    bar_number VARCHAR(100),
    practice_areas TEXT[], -- Array of practice areas
    preferences JSONB DEFAULT '{}',
    permissions JSONB DEFAULT '{}', -- Custom permissions beyond role defaults
    last_login TIMESTAMP WITH TIME ZONE,
    password_changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Research sessions and queries
CREATE TABLE research_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    firm_id UUID REFERENCES firms(id) ON DELETE CASCADE,
    title VARCHAR(500),
    objective TEXT,
    jurisdiction VARCHAR(10),
    practice_areas TEXT[],
    status VARCHAR(50) DEFAULT 'active', -- active, completed, archived
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE research_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES research_sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    query_text TEXT NOT NULL,
    query_type VARCHAR(50) DEFAULT 'semantic', -- semantic, citation, hybrid
    filters JSONB DEFAULT '{}',
    results_count INTEGER DEFAULT 0,
    execution_time_ms INTEGER,
    success_score DECIMAL(3,2), -- User-rated success 0.00-1.00
    feedback TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Memory and personalization
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    preference_type VARCHAR(100) NOT NULL, -- search_style, citation_format, etc.
    preference_key VARCHAR(100) NOT NULL,
    preference_value JSONB NOT NULL,
    confidence_score DECIMAL(3,2) DEFAULT 0.5,
    last_used TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, preference_type, preference_key)
);

CREATE TABLE research_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    firm_id UUID REFERENCES firms(id) ON DELETE CASCADE,
    pattern_type VARCHAR(100) NOT NULL, -- successful_strategy, failed_approach, etc.
    context JSONB NOT NULL, -- Practice area, jurisdiction, case type, etc.
    pattern_data JSONB NOT NULL, -- The actual pattern/strategy
    success_score DECIMAL(3,2),
    usage_count INTEGER DEFAULT 1,
    last_used TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Case tracking and outcomes
CREATE TABLE tracked_cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    firm_id UUID REFERENCES firms(id) ON DELETE CASCADE,
    case_id VARCHAR(255) NOT NULL, -- References Neo4j case node
    case_name VARCHAR(500),
    client_matter VARCHAR(255),
    our_role VARCHAR(100), -- plaintiff, defendant, amicus, etc.
    status VARCHAR(50) DEFAULT 'active',
    practice_areas TEXT[],
    tracking_reason TEXT, -- Why we're tracking this case
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE case_outcomes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tracked_case_id UUID REFERENCES tracked_cases(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    outcome_type VARCHAR(100) NOT NULL, -- motion_granted, case_won, settlement, etc.
    outcome_date DATE NOT NULL,
    strategies_used TEXT[],
    key_factors TEXT[],
    success_score DECIMAL(3,2), -- How successful was this outcome
    lessons_learned TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Document and brief storage
CREATE TABLE research_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES research_sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    document_type VARCHAR(100) NOT NULL, -- memo, brief, research_note, etc.
    title VARCHAR(500) NOT NULL,
    content TEXT,
    document_format VARCHAR(50) DEFAULT 'markdown', -- markdown, html, pdf
    source_queries UUID[], -- Array of query IDs that contributed
    chroma_document_id VARCHAR(255), -- Reference to ChromaDB document
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API and integration tracking
CREATE TABLE api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    firm_id UUID REFERENCES firms(id) ON DELETE CASCADE,
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    request_id UUID,
    response_status INTEGER,
    execution_time_ms INTEGER,
    tokens_used INTEGER DEFAULT 0,
    cost_cents INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE mcp_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    firm_id UUID REFERENCES firms(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    client_info JSONB DEFAULT '{}',
    tools_used TEXT[],
    queries_count INTEGER DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true
);

-- API Keys for programmatic access
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    firm_id UUID REFERENCES firms(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    permissions TEXT[] NOT NULL,
    last_used TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT true
);

-- Password reset tokens
CREATE TABLE password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    is_used BOOLEAN DEFAULT false
);

-- Email verification tokens
CREATE TABLE email_verification_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used_at TIMESTAMP WITH TIME ZONE,
    is_used BOOLEAN DEFAULT false
);

-- Audit log for security events
CREATE TABLE security_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    firm_id UUID REFERENCES firms(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL, -- login, logout, token_created, password_changed, etc.
    event_data JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_users_firm_id ON users(firm_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_research_sessions_user_id ON research_sessions(user_id);
CREATE INDEX idx_research_sessions_status ON research_sessions(status);
CREATE INDEX idx_research_queries_session_id ON research_queries(session_id);
CREATE INDEX idx_research_queries_user_id ON research_queries(user_id);
CREATE INDEX idx_research_queries_created_at ON research_queries(created_at);
CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX idx_research_patterns_user_id ON research_patterns(user_id);
CREATE INDEX idx_research_patterns_firm_id ON research_patterns(firm_id);
CREATE INDEX idx_tracked_cases_user_id ON tracked_cases(user_id);
CREATE INDEX idx_tracked_cases_case_id ON tracked_cases(case_id);
CREATE INDEX idx_case_outcomes_tracked_case_id ON case_outcomes(tracked_case_id);
CREATE INDEX idx_research_documents_session_id ON research_documents(session_id);
CREATE INDEX idx_api_usage_user_id ON api_usage(user_id);
CREATE INDEX idx_api_usage_firm_id ON api_usage(firm_id);
CREATE INDEX idx_api_usage_created_at ON api_usage(created_at);
CREATE INDEX idx_mcp_sessions_user_id ON mcp_sessions(user_id);
CREATE INDEX idx_mcp_sessions_token ON mcp_sessions(session_token);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_firm_id ON api_keys(firm_id);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_active ON api_keys(is_active);
CREATE INDEX idx_password_reset_tokens_hash ON password_reset_tokens(token_hash);
CREATE INDEX idx_password_reset_tokens_user_id ON password_reset_tokens(user_id);
CREATE INDEX idx_email_verification_tokens_hash ON email_verification_tokens(token_hash);
CREATE INDEX idx_email_verification_tokens_user_id ON email_verification_tokens(user_id);
CREATE INDEX idx_security_audit_log_user_id ON security_audit_log(user_id);
CREATE INDEX idx_security_audit_log_firm_id ON security_audit_log(firm_id);
CREATE INDEX idx_security_audit_log_event_type ON security_audit_log(event_type);
CREATE INDEX idx_security_audit_log_created_at ON security_audit_log(created_at);

-- GIN indexes for JSONB columns
CREATE INDEX idx_firms_settings ON firms USING GIN(settings);
CREATE INDEX idx_users_preferences ON users USING GIN(preferences);
CREATE INDEX idx_research_sessions_metadata ON research_sessions USING GIN(metadata);
CREATE INDEX idx_research_queries_filters ON research_queries USING GIN(filters);
CREATE INDEX idx_research_patterns_context ON research_patterns USING GIN(context);
CREATE INDEX idx_research_patterns_pattern_data ON research_patterns USING GIN(pattern_data);
CREATE INDEX idx_case_outcomes_metadata ON case_outcomes USING GIN(metadata);
CREATE INDEX idx_research_documents_metadata ON research_documents USING GIN(metadata);
CREATE INDEX idx_mcp_sessions_client_info ON mcp_sessions USING GIN(client_info);
CREATE INDEX idx_security_audit_log_event_data ON security_audit_log USING GIN(event_data);

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_firms_updated_at BEFORE UPDATE ON firms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_research_sessions_updated_at BEFORE UPDATE ON research_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tracked_cases_updated_at BEFORE UPDATE ON tracked_cases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_research_documents_updated_at BEFORE UPDATE ON research_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries
CREATE VIEW active_research_sessions AS
SELECT 
    rs.*,
    u.full_name as user_name,
    f.name as firm_name,
    COUNT(rq.id) as query_count
FROM research_sessions rs
JOIN users u ON rs.user_id = u.id
JOIN firms f ON rs.firm_id = f.id
LEFT JOIN research_queries rq ON rs.id = rq.session_id
WHERE rs.status = 'active'
GROUP BY rs.id, u.full_name, f.name;

CREATE VIEW user_research_stats AS
SELECT 
    u.id as user_id,
    u.full_name,
    u.email,
    COUNT(DISTINCT rs.id) as total_sessions,
    COUNT(rq.id) as total_queries,
    AVG(rq.success_score) as avg_success_score,
    MAX(rs.created_at) as last_research_date
FROM users u
LEFT JOIN research_sessions rs ON u.id = rs.user_id
LEFT JOIN research_queries rq ON rs.id = rq.session_id
GROUP BY u.id, u.full_name, u.email;

CREATE VIEW firm_usage_stats AS
SELECT 
    f.id as firm_id,
    f.name as firm_name,
    COUNT(DISTINCT u.id) as active_users,
    COUNT(DISTINCT rs.id) as total_sessions,
    COUNT(rq.id) as total_queries,
    SUM(au.cost_cents) as total_cost_cents,
    MAX(rs.created_at) as last_activity
FROM firms f
LEFT JOIN users u ON f.id = u.firm_id
LEFT JOIN research_sessions rs ON u.id = rs.user_id
LEFT JOIN research_queries rq ON rs.id = rq.session_id
LEFT JOIN api_usage au ON f.id = au.firm_id
WHERE u.is_active = true
GROUP BY f.id, f.name;

-- Sample data for development
INSERT INTO firms (name, short_name, jurisdiction, practice_areas, subscription_tier) VALUES
('Smith & Associates', 'Smith', 'CA', ARRAY['civil_rights', 'employment'], 'professional'),
('Legal Defense Fund', 'LDF', 'US', ARRAY['constitutional', 'civil_rights'], 'enterprise'),
('Corporate Counsel Group', 'CCG', 'NY', ARRAY['corporate', 'litigation'], 'basic');

-- Sample users with hashed passwords (password: "demo123!")
INSERT INTO users (firm_id, email, full_name, password_hash, role, practice_areas, email_verified) VALUES
((SELECT id FROM firms WHERE short_name = 'Smith'), 'jane.smith@smithlaw.com', 'Jane Smith', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4OTRQ.QNpm', 'partner', ARRAY['civil_rights'], true),
((SELECT id FROM firms WHERE short_name = 'LDF'), 'john.doe@ldf.org', 'John Doe', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4OTRQ.QNpm', 'attorney', ARRAY['constitutional'], true),
((SELECT id FROM firms WHERE short_name = 'CCG'), 'mary.jones@ccg.com', 'Mary Jones', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4OTRQ.QNpm', 'paralegal', ARRAY['corporate'], true),
((SELECT id FROM firms WHERE short_name = 'Smith'), 'admin@smithlaw.com', 'Admin User', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4OTRQ.QNpm', 'admin', ARRAY['civil_rights', 'employment'], true);

-- Comments for documentation
COMMENT ON TABLE firms IS 'Law firms using the platform';
COMMENT ON TABLE users IS 'Individual users (attorneys, paralegals, etc.)';
COMMENT ON TABLE research_sessions IS 'Research sessions tracking complete investigations';
COMMENT ON TABLE research_queries IS 'Individual search queries within sessions';
COMMENT ON TABLE user_preferences IS 'User-specific preferences learned over time';
COMMENT ON TABLE research_patterns IS 'Successful/unsuccessful research patterns for learning';
COMMENT ON TABLE tracked_cases IS 'Cases being monitored for developments';
COMMENT ON TABLE case_outcomes IS 'Outcomes of tracked cases for pattern learning';
COMMENT ON TABLE research_documents IS 'Generated memos, briefs, and research documents';
COMMENT ON TABLE api_usage IS 'API usage tracking for billing and monitoring';
COMMENT ON TABLE mcp_sessions IS 'MCP server sessions for external AI assistants';
COMMENT ON TABLE api_keys IS 'API keys for programmatic access to the platform';
COMMENT ON TABLE password_reset_tokens IS 'Secure tokens for password reset functionality';
COMMENT ON TABLE email_verification_tokens IS 'Tokens for email address verification';
COMMENT ON TABLE security_audit_log IS 'Audit trail for security-related events and actions';