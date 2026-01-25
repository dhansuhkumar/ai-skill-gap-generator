-- Supabase Database Schema for AI Skill Gap Generator
-- Run this in Supabase Dashboard → SQL Editor

-- ============================================================
-- AUTH USERS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS auth_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- PROFILES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS profiles (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth_users(id),
    display_name TEXT,
    resume_parsed_json TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- SKILLS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS skills (
    id BIGSERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- PROFILE SKILLS JUNCTION TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS profile_skills (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT REFERENCES profiles(id),
    skill_id BIGINT REFERENCES skills(id),
    confidence INTEGER DEFAULT 80,
    source TEXT DEFAULT 'user',
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_profile_skills_profile ON profile_skills(profile_id);
CREATE INDEX IF NOT EXISTS idx_profile_skills_skill ON profile_skills(skill_id);
CREATE INDEX IF NOT EXISTS idx_profiles_user ON profiles(user_id);

-- ============================================================
-- ENABLE ROW LEVEL SECURITY (RLS)
-- ============================================================
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE profile_skills ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- RLS POLICIES FOR PROFILES
-- ============================================================
CREATE POLICY "Users can read own profile"
    ON profiles FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update own profile"
    ON profiles FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own profile"
    ON profiles FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- ============================================================
-- RLS POLICIES FOR SKILLS (PUBLIC READ)
-- ============================================================
CREATE POLICY "Allow public read access on skills"
    ON skills FOR SELECT
    USING (true);

-- ============================================================
-- RLS POLICIES FOR PROFILE_SKILLS
-- ============================================================
CREATE POLICY "Users can read own profile_skills"
    ON profile_skills FOR SELECT
    USING (profile_id IN (SELECT id FROM profiles WHERE user_id = auth.uid()));

CREATE POLICY "Users can manage own profile_skills"
    ON profile_skills FOR ALL
    USING (profile_id IN (SELECT id FROM profiles WHERE user_id = auth.uid()));

-- ============================================================
-- GITHUB ANALYSIS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS github_analysis (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT REFERENCES profiles(id) ON DELETE CASCADE,
    username TEXT NOT NULL,
    analysis_data JSONB NOT NULL,      -- Full GitHub analysis results
    commit_timeline JSONB,              -- Commit history for heatmap
    total_repos INTEGER DEFAULT 0,
    diversity_bonus INTEGER DEFAULT 0,
    language_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- LEARNING PROGRESS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS learning_progress (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT REFERENCES profiles(id) ON DELETE CASCADE,
    skill_name TEXT NOT NULL,
    step_index INTEGER NOT NULL,
    step_title TEXT,
    completed BOOLEAN DEFAULT false,
    completed_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- LEARNING PLANS TABLE (Store generated learning plans)
-- ============================================================
CREATE TABLE IF NOT EXISTS learning_plans (
    id BIGSERIAL PRIMARY KEY,
    profile_id BIGINT REFERENCES profiles(id) ON DELETE CASCADE,
    target_role TEXT NOT NULL,
    selected_skills JSONB NOT NULL,     -- Array of skill names
    learning_path JSONB NOT NULL,       -- Full learning path data
    matching_score INTEGER DEFAULT 0,
    github_username TEXT,
    provider TEXT DEFAULT 'auto',
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_github_analysis_profile ON github_analysis(profile_id);
CREATE INDEX IF NOT EXISTS idx_github_analysis_username ON github_analysis(username);
CREATE INDEX IF NOT EXISTS idx_learning_progress_profile ON learning_progress(profile_id);
CREATE INDEX IF NOT EXISTS idx_learning_progress_skill ON learning_progress(skill_name);
CREATE INDEX IF NOT EXISTS idx_learning_plans_profile ON learning_plans(profile_id);
CREATE INDEX IF NOT EXISTS idx_learning_plans_role ON learning_plans(target_role);

-- ============================================================
-- ENABLE ROW LEVEL SECURITY (RLS)
-- ============================================================
ALTER TABLE github_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_plans ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- RLS POLICIES FOR GITHUB_ANALYSIS
-- ============================================================
CREATE POLICY "Users can read own github_analysis"
    ON github_analysis FOR SELECT
    USING (profile_id IN (SELECT id FROM profiles WHERE user_id = auth.uid()));

CREATE POLICY "Users can manage own github_analysis"
    ON github_analysis FOR ALL
    USING (profile_id IN (SELECT id FROM profiles WHERE user_id = auth.uid()));

-- ============================================================
-- RLS POLICIES FOR LEARNING_PROGRESS
-- ============================================================
CREATE POLICY "Users can read own learning_progress"
    ON learning_progress FOR SELECT
    USING (profile_id IN (SELECT id FROM profiles WHERE user_id = auth.uid()));

CREATE POLICY "Users can manage own learning_progress"
    ON learning_progress FOR ALL
    USING (profile_id IN (SELECT id FROM profiles WHERE user_id = auth.uid()));

-- ============================================================
-- RLS POLICIES FOR LEARNING_PLANS
-- ============================================================
CREATE POLICY "Users can read own learning_plans"
    ON learning_plans FOR SELECT
    USING (profile_id IN (SELECT id FROM profiles WHERE user_id = auth.uid()));

CREATE POLICY "Users can manage own learning_plans"
    ON learning_plans FOR ALL
    USING (profile_id IN (SELECT id FROM profiles WHERE user_id = auth.uid()));

-- ============================================================
-- VERIFICATION QUERY
-- ============================================================
-- Run this to verify all tables were created:
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'auth_users', 'profiles', 'skills', 'profile_skills',
    'github_analysis', 'learning_progress', 'learning_plans'
)
ORDER BY table_name;
