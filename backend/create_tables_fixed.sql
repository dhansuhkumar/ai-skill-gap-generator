
-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Allow public read access on job_postings" ON job_postings;
DROP POLICY IF EXISTS "Allow public read access on job_skills" ON job_skills;
DROP POLICY IF EXISTS "Allow public insert on job_postings" ON job_postings;
DROP POLICY IF EXISTS "Allow public insert on job_skills" ON job_skills;

-- Table: job_postings
CREATE TABLE IF NOT EXISTS job_postings (
    id BIGSERIAL PRIMARY KEY,
    job_link TEXT UNIQUE NOT NULL,
    last_processed_time TEXT,
    got_summary BOOLEAN,
    got_ner BOOLEAN,
    is_being_worked BOOLEAN,
    job_title TEXT,
    company TEXT,
    job_location TEXT,
    first_seen TEXT,
    search_city TEXT,
    search_country TEXT,
    search_position TEXT,
    job_level TEXT,
    job_type TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table: job_skills
CREATE TABLE IF NOT EXISTS job_skills (
    id BIGSERIAL PRIMARY KEY,
    job_link TEXT NOT NULL,
    job_skills TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_job_postings_title ON job_postings(job_title);
CREATE INDEX IF NOT EXISTS idx_job_postings_company ON job_postings(company);
CREATE INDEX IF NOT EXISTS idx_job_postings_location ON job_postings(job_location);
CREATE INDEX IF NOT EXISTS idx_job_postings_link ON job_postings(job_link);
CREATE INDEX IF NOT EXISTS idx_job_skills_link ON job_skills(job_link);

-- Enable Row Level Security (RLS)
ALTER TABLE job_postings ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_skills ENABLE ROW LEVEL SECURITY;

-- Create policies to allow public read AND insert access
CREATE POLICY "Allow public read access on job_postings"
    ON job_postings FOR SELECT
    USING (true);

CREATE POLICY "Allow public insert on job_postings"
    ON job_postings FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Allow public read access on job_skills"
    ON job_skills FOR SELECT
    USING (true);

CREATE POLICY "Allow public insert on job_skills"
    ON job_skills FOR INSERT
    WITH CHECK (true);
