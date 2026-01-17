#!/usr/bin/env python3
"""
Push job data to Hugging Face Hub as Parquet format.
Converts filtered CSVs to optimized Parquet and uploads to HF Datasets.
"""

import os
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
from datasets import Dataset

# Configuration
HF_USERNAME = os.getenv("HF_USERNAME", "dhansuhkumar")
DATA_DIR = Path(__file__).parent.parent / "data"

# CSV file paths (filtered versions for smaller size)
JOBS_CSV = DATA_DIR / "linkedin_job_postings_filtered.csv"
SKILLS_CSV = DATA_DIR / "job_skills_filtered.csv"


def load_csv(path: Path, name: str) -> pd.DataFrame:
    """Load a CSV file and clean it."""
    print(f"  Loading {path.name}...")
    if not path.exists():
        raise FileNotFoundError(f"{name} CSV not found: {path}")
    
    df = pd.read_csv(path)
    print(f"  ✅ Loaded {len(df):,} {name}")
    
    # Clean data - handle NaN values and convert all to string
    df = df.fillna("").astype(str)
    
    # Remove pandas index column if present
    if '__index_level_0__' in df.columns:
        df = df.drop(columns=['__index_level_0__'])
    
    return df


def push_dataset(df: pd.DataFrame, repo_name: str, description: str):
    """Convert DataFrame to HF Dataset and push to Hub."""
    
    print(f"\n🔄 Converting {repo_name} to HuggingFace Dataset...")
    dataset = Dataset.from_pandas(df, preserve_index=False)
    print(f"  ✅ Created dataset with {len(dataset):,} rows")
    print(f"     Columns: {dataset.column_names}")
    
    full_repo = f"{HF_USERNAME}/{repo_name}"
    print(f"\n🚀 Pushing to: https://huggingface.co/datasets/{full_repo}")
    
    try:
        dataset.push_to_hub(
            full_repo,
            private=False,
            commit_message=f"Upload {description} in Parquet format"
        )
        print(f"  ✅ Successfully pushed {repo_name}!")
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False


def main():
    """Main entry point."""
    print("=" * 60)
    print("  HuggingFace Data Migration Script")
    print("  Converting CSV → Parquet → HuggingFace Hub")
    print("=" * 60 + "\n")
    
    print(f"📁 Loading data from: {DATA_DIR}\n")
    
    # Load CSVs
    jobs_df = load_csv(JOBS_CSV, "job postings")
    skills_df = load_csv(SKILLS_CSV, "skill mappings")
    
    # Push as separate datasets
    success = True
    
    print("\n" + "-" * 40)
    print("Pushing Jobs Dataset")
    print("-" * 40)
    success &= push_dataset(jobs_df, "skill-gap-jobs", "job postings data")
    
    print("\n" + "-" * 40)
    print("Pushing Skills Dataset")
    print("-" * 40)
    success &= push_dataset(skills_df, "skill-gap-skills", "job skills mapping")
    
    print("\n" + "=" * 60)
    if success:
        print("  ✅ Migration Complete!")
        print(f"\n  Datasets available at:")
        print(f"    - https://huggingface.co/datasets/{HF_USERNAME}/skill-gap-jobs")
        print(f"    - https://huggingface.co/datasets/{HF_USERNAME}/skill-gap-skills")
    else:
        print("  ⚠️ Migration completed with errors. Check output above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
