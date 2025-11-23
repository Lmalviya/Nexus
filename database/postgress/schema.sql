-- 1. Enable UUID extension for secure IDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. ORGANIZATIONS (The Clients)
-- This handles your "Two Clients" requirement.
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,                -- e.g., "Acme Corp India"
    slug VARCHAR(50) UNIQUE NOT NULL,          -- e.g., "acme-ind" (for subdomains/URLs)
    domain VARCHAR(255),                       -- e.g., "acme.in" (to auto-join users)
    
    -- Subscription / Limits
    plan_tier VARCHAR(50) DEFAULT 'standard',  -- 'free', 'pro', 'enterprise'
    max_users INT DEFAULT 10,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. USERS (The Employees)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Login Info
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),                -- Nullable if using only Google Login
    full_name VARCHAR(100),
    avatar_url TEXT,
    
    -- Roles & Access
    role VARCHAR(20) DEFAULT 'employee',       -- 'admin', 'employee', 'viewer'
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Localization (Critical for India context)
    timezone VARCHAR(50) DEFAULT 'Asia/Kolkata',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);


CREATE TABLE IF NOT EXISTS user_settings (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    
    -- JSONB is perfect for flexible settings that might change often
    preferences JSONB DEFAULT '{
        "theme": "system",
        "default_mode": "standard", 
        "allow_artifacts": true,
        "language": "en-IN"
    }'::jsonb,
    
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. API KEYS
-- Stores LLM provider API keys for users/organizations
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,  -- 'openai', 'claude', 'gemini', etc.
    key_name VARCHAR(100),
    encrypted_key TEXT NOT NULL,  -- Encrypted API key
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. USAGE TRACKING
-- Tracks token usage per session and model
CREATE TABLE IF NOT EXISTS usage_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    api_key_id UUID REFERENCES api_keys(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID,  -- Chat session identifier
    model_name VARCHAR(100),  -- 'gpt-4', 'claude-3-opus', etc.
    tokens_used INTEGER DEFAULT 0,
    request_count INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
