-- Supabase Migration: Learning Paths & Progress Tables
-- Run this in your Supabase SQL Editor

-- Table for storing user's generated learning paths
CREATE TABLE IF NOT EXISTS learning_paths (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    target_role TEXT NOT NULL,
    selected_skills TEXT[] DEFAULT '{}',
    learning_path JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table for tracking learning step completion
CREATE TABLE IF NOT EXISTS learning_progress (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    skill_name TEXT,
    completed_steps INTEGER[] DEFAULT '{}',
    path_id TEXT,
    week_number INTEGER,
    day_number INTEGER,
    completed_tasks INTEGER[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, skill_name)
);

-- Add unique constraint for path-based progress if columns are present
-- This will be handled by the application logic

-- Enable RLS
ALTER TABLE learning_paths ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_progress ENABLE ROW LEVEL SECURITY;

-- RLS Policies for learning_paths
CREATE POLICY "Users can view own learning paths" ON learning_paths
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own learning paths" ON learning_paths
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own learning paths" ON learning_paths
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own learning paths" ON learning_paths
    FOR DELETE USING (auth.uid() = user_id);

-- RLS Policies for learning_progress
CREATE POLICY "Users can view own progress" ON learning_progress
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own progress" ON learning_progress
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own progress" ON learning_progress
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own progress" ON learning_progress
    FOR DELETE USING (auth.uid() = user_id);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_learning_paths_user_id ON learning_paths(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_progress_user_id ON learning_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_progress_skill ON learning_progress(skill_name);
