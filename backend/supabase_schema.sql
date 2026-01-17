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
-- VERIFICATION QUERY
-- ============================================================
-- Run this to verify tables were created:
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('auth_users', 'profiles', 'skills', 'profile_skills')
ORDER BY table_name;
