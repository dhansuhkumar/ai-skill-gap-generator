"""
Migration script to upload filtered CSV data to Supabase.
This script will:
1. Create tables in Supabase
2. Upload data in batches with progress tracking
3. Create indexes for performance
"""

import os
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path
import time
from tqdm import tqdm

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ Supabase credentials not found in .env file")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Paths to filtered CSV files
DATA_DIR = Path(__file__).parent / 'data'
JOBS_CSV = DATA_DIR / 'linkedin_job_postings_filtered.csv'
SKILLS_CSV = DATA_DIR / 'job_skills_filtered.csv'

# Batch size for uploads
BATCH_SIZE = 1000

def create_tables():
    """Create Supabase tables using SQL."""
    print("\n" + "=" * 80)
    print("CREATING SUPABASE TABLES")
    print("=" * 80)
    
    # Note: These SQL commands should be run in Supabase SQL Editor
    # We'll provide the SQL for the user to run manually
    
    sql_commands = """
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

-- Create policies to allow public read access
CREATE POLICY "Allow public read access on job_postings"
    ON job_postings FOR SELECT
    USING (true);

CREATE POLICY "Allow public read access on job_skills"
    ON job_skills FOR SELECT
    USING (true);
"""
    
    print("\n📝 SQL commands to create tables:")
    print("\n" + "=" * 80)
    print(sql_commands)
    print("=" * 80)
    
    # Save SQL to file
    sql_file = Path(__file__).parent / 'create_tables.sql'
    with open(sql_file, 'w') as f:
        f.write(sql_commands)
    
    print(f"\n✅ SQL commands saved to: {sql_file}")
    print("\n⚠️  MANUAL STEP REQUIRED:")
    print("   1. Go to Supabase Dashboard → SQL Editor")
    print("   2. Copy and run the SQL commands above")
    print("   3. Press Enter here to continue after tables are created...")
    input()

def upload_job_postings():
    """Upload job postings to Supabase in batches."""
    print("\n" + "=" * 80)
    print("UPLOADING JOB POSTINGS")
    print("=" * 80)
    
    # Read CSV
    print(f"\n📖 Reading {JOBS_CSV}...")
    df = pd.read_csv(JOBS_CSV)
    total_rows = len(df)
    print(f"   Total rows: {total_rows:,}")
    
    # Convert DataFrame to list of dicts
    records = df.to_dict('records')
    
    # Upload in batches
    print(f"\n📤 Uploading in batches of {BATCH_SIZE}...")
    successful = 0
    failed = 0
    
    for i in tqdm(range(0, total_rows, BATCH_SIZE), desc="Uploading job postings"):
        batch = records[i:i + BATCH_SIZE]
        
        try:
            # Insert batch
            supabase.table('job_postings').insert(batch).execute()
            successful += len(batch)
            time.sleep(0.5)  # Rate limiting
        except Exception as e:
            print(f"\n❌ Error uploading batch {i}-{i+len(batch)}: {e}")
            failed += len(batch)
    
    print(f"\n✅ Upload complete!")
    print(f"   Successful: {successful:,}")
    print(f"   Failed: {failed:,}")
    
    return successful, failed

def upload_job_skills():
    """Upload job skills to Supabase in batches."""
    print("\n" + "=" * 80)
    print("UPLOADING JOB SKILLS")
    print("=" * 80)
    
    # Read CSV
    print(f"\n📖 Reading {SKILLS_CSV}...")
    df = pd.read_csv(SKILLS_CSV)
    total_rows = len(df)
    print(f"   Total rows: {total_rows:,}")
    
    # Convert DataFrame to list of dicts
    records = df.to_dict('records')
    
    # Upload in batches
    print(f"\n📤 Uploading in batches of {BATCH_SIZE}...")
    successful = 0
    failed = 0
    
    for i in tqdm(range(0, total_rows, BATCH_SIZE), desc="Uploading job skills"):
        batch = records[i:i + BATCH_SIZE]
        
        try:
            # Insert batch
            supabase.table('job_skills').insert(batch).execute()
            successful += len(batch)
            time.sleep(0.5)  # Rate limiting
        except Exception as e:
            print(f"\n❌ Error uploading batch {i}-{i+len(batch)}: {e}")
            failed += len(batch)
    
    print(f"\n✅ Upload complete!")
    print(f"   Successful: {successful:,}")
    print(f"   Failed: {failed:,}")
    
    return successful, failed

def verify_upload():
    """Verify data was uploaded correctly."""
    print("\n" + "=" * 80)
    print("VERIFYING UPLOAD")
    print("=" * 80)
    
    try:
        # Count job postings
        result = supabase.table('job_postings').select('id', count='exact').limit(1).execute()
        job_count = result.count
        print(f"\n✅ Job postings in database: {job_count:,}")
        
        # Count job skills
        result = supabase.table('job_skills').select('id', count='exact').limit(1).execute()
        skills_count = result.count
        print(f"✅ Job skills in database: {skills_count:,}")
        
        # Sample query
        print("\n📊 Sample job posting:")
        result = supabase.table('job_postings').select('*').limit(1).execute()
        if result.data:
            sample = result.data[0]
            print(f"   Title: {sample.get('job_title')}")
            print(f"   Company: {sample.get('company')}")
            print(f"   Location: {sample.get('job_location')}")
        
        return True
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    try:
        print("=" * 80)
        print("SUPABASE MIGRATION SCRIPT")
        print("=" * 80)
        print(f"\nSupabase URL: {SUPABASE_URL}")
        print(f"Job postings CSV: {JOBS_CSV}")
        print(f"Job skills CSV: {SKILLS_CSV}")
        
        # Step 1: Create tables
        create_tables()
        
        # Step 2: Upload job postings
        jobs_success, jobs_failed = upload_job_postings()
        
        # Step 3: Upload job skills
        skills_success, skills_failed = upload_job_skills()
        
        # Step 4: Verify
        verify_upload()
        
        print("\n" + "=" * 80)
        print("✅ MIGRATION COMPLETE!")
        print("=" * 80)
        print(f"\nSummary:")
        print(f"  Job postings uploaded: {jobs_success:,}")
        print(f"  Job skills uploaded: {skills_success:,}")
        print(f"  Total records: {jobs_success + skills_success:,}")
        
        if jobs_failed > 0 or skills_failed > 0:
            print(f"\n⚠️  Some records failed to upload:")
            print(f"  Job postings failed: {jobs_failed:,}")
            print(f"  Job skills failed: {skills_failed:,}")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
