"""
Analyze CSV files and create filtered versions for Supabase free tier.
Target: Keep data under 400MB to fit comfortably in 500MB limit.
"""

import pandas as pd
import os
from pathlib import Path

# Paths
DATA_DIR = Path(__file__).parent / 'data'
JOBS_CSV = DATA_DIR / 'linkedin_job_postings.csv'
SKILLS_CSV = DATA_DIR / 'job_skills.csv'

def analyze_csv_files():
    """Analyze the CSV files to understand their structure and size."""
    print("=" * 80)
    print("ANALYZING CSV FILES")
    print("=" * 80)
    
    # Analyze job postings
    print("\n📊 LinkedIn Job Postings CSV:")
    print(f"   File size: {JOBS_CSV.stat().st_size / (1024**2):.2f} MB")
    
    jobs_df = pd.read_csv(JOBS_CSV, nrows=10)
    print(f"   Columns: {jobs_df.columns.tolist()}")
    print(f"\n   Sample data:")
    print(jobs_df.head(3))
    
    # Count total rows
    print("\n   Counting total rows (this may take a moment)...")
    jobs_full = pd.read_csv(JOBS_CSV)
    print(f"   Total rows: {len(jobs_full):,}")
    
    # Analyze job skills
    print("\n📊 Job Skills CSV:")
    print(f"   File size: {SKILLS_CSV.stat().st_size / (1024**2):.2f} MB")
    
    skills_df = pd.read_csv(SKILLS_CSV, nrows=10)
    print(f"   Columns: {skills_df.columns.tolist()}")
    print(f"\n   Sample data:")
    print(skills_df.head(3))
    
    print("\n   Counting total rows (this may take a moment)...")
    skills_full = pd.read_csv(SKILLS_CSV)
    print(f"   Total rows: {len(skills_full):,}")
    
    # Calculate reduction needed
    total_size_mb = (JOBS_CSV.stat().st_size + SKILLS_CSV.stat().st_size) / (1024**2)
    target_size_mb = 400  # Target 400MB to leave buffer
    reduction_ratio = target_size_mb / total_size_mb
    
    print("\n" + "=" * 80)
    print("FILTERING STRATEGY")
    print("=" * 80)
    print(f"Current total size: {total_size_mb:.2f} MB")
    print(f"Target size: {target_size_mb} MB")
    print(f"Reduction needed: {(1 - reduction_ratio) * 100:.1f}%")
    print(f"Keep approximately: {reduction_ratio * 100:.1f}% of data")
    print(f"Estimated rows to keep: {int(len(jobs_full) * reduction_ratio):,} job postings")
    
    return jobs_full, skills_full, reduction_ratio

def filter_data(jobs_df, skills_df, keep_ratio):
    """
    Filter data intelligently to keep the most relevant records.
    Strategy: Keep recent postings and those with skills data.
    """
    print("\n" + "=" * 80)
    print("FILTERING DATA")
    print("=" * 80)
    
    # Strategy 1: Keep only jobs that have associated skills
    print("\n1️⃣ Filtering jobs with skills data...")
    jobs_with_skills = jobs_df[jobs_df['job_link'].isin(skills_df['job_link'])]
    print(f"   Jobs with skills: {len(jobs_with_skills):,} ({len(jobs_with_skills)/len(jobs_df)*100:.1f}%)")
    
    # Strategy 2: Sample to meet size requirements
    target_rows = int(len(jobs_df) * keep_ratio)
    
    if len(jobs_with_skills) > target_rows:
        print(f"\n2️⃣ Sampling {target_rows:,} jobs from those with skills...")
        # Random sample to get diverse job types
        filtered_jobs = jobs_with_skills.sample(n=target_rows, random_state=42)
    else:
        print(f"\n2️⃣ Keeping all {len(jobs_with_skills):,} jobs with skills data")
        filtered_jobs = jobs_with_skills
    
    # Filter skills to match filtered jobs
    print(f"\n3️⃣ Filtering skills to match selected jobs...")
    filtered_skills = skills_df[skills_df['job_link'].isin(filtered_jobs['job_link'])]
    
    print(f"\n✅ Filtered Results:")
    print(f"   Job postings: {len(filtered_jobs):,}")
    print(f"   Skill records: {len(filtered_skills):,}")
    
    return filtered_jobs, filtered_skills

def save_filtered_data(jobs_df, skills_df):
    """Save filtered data to new CSV files."""
    print("\n" + "=" * 80)
    print("SAVING FILTERED DATA")
    print("=" * 80)
    
    # Save filtered CSVs
    filtered_jobs_path = DATA_DIR / 'linkedin_job_postings_filtered.csv'
    filtered_skills_path = DATA_DIR / 'job_skills_filtered.csv'
    
    print(f"\n💾 Saving filtered job postings...")
    jobs_df.to_csv(filtered_jobs_path, index=False)
    jobs_size = filtered_jobs_path.stat().st_size / (1024**2)
    print(f"   Saved: {filtered_jobs_path}")
    print(f"   Size: {jobs_size:.2f} MB")
    
    print(f"\n💾 Saving filtered job skills...")
    skills_df.to_csv(filtered_skills_path, index=False)
    skills_size = filtered_skills_path.stat().st_size / (1024**2)
    print(f"   Saved: {filtered_skills_path}")
    print(f"   Size: {skills_size:.2f} MB")
    
    total_size = jobs_size + skills_size
    print(f"\n✅ Total filtered size: {total_size:.2f} MB")
    
    if total_size < 500:
        print(f"   ✅ Fits in Supabase free tier (500 MB)!")
    else:
        print(f"   ⚠️  Still exceeds 500 MB, need more filtering")
    
    return filtered_jobs_path, filtered_skills_path

if __name__ == "__main__":
    try:
        # Analyze
        jobs_df, skills_df, keep_ratio = analyze_csv_files()
        
        # Filter
        filtered_jobs, filtered_skills = filter_data(jobs_df, skills_df, keep_ratio)
        
        # Save
        save_filtered_data(filtered_jobs, filtered_skills)
        
        print("\n" + "=" * 80)
        print("✅ ANALYSIS AND FILTERING COMPLETE!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
