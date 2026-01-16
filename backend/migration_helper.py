"""
Quick start script to help with database migration.
This script checks prerequisites and guides you through the migration process.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_prerequisites():
    """Check if all prerequisites are met."""
    print("=" * 80)
    print("DATABASE MIGRATION - PREREQUISITES CHECK")
    print("=" * 80)
    
    issues = []
    
    # Check 1: Supabase credentials
    print("\n1️⃣ Checking Supabase credentials...")
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("   ❌ Supabase credentials not found in .env file")
        issues.append("Add SUPABASE_URL and SUPABASE_KEY to .env file")
    else:
        print(f"   ✅ Supabase URL: {supabase_url}")
        print(f"   ✅ Supabase Key: {supabase_key[:20]}...")
    
    # Check 2: Filtered CSV files
    print("\n2️⃣ Checking filtered CSV files...")
    data_dir = Path(__file__).parent / 'data'
    jobs_csv = data_dir / 'linkedin_job_postings_filtered.csv'
    skills_csv = data_dir / 'job_skills_filtered.csv'
    
    if not jobs_csv.exists():
        print(f"   ❌ Filtered jobs CSV not found: {jobs_csv}")
        issues.append("Run: python backend/analyze_and_filter_data.py")
    else:
        size_mb = jobs_csv.stat().st_size / (1024**2)
        print(f"   ✅ Jobs CSV found: {size_mb:.2f} MB")
    
    if not skills_csv.exists():
        print(f"   ❌ Filtered skills CSV not found: {skills_csv}")
        issues.append("Run: python backend/analyze_and_filter_data.py")
    else:
        size_mb = skills_csv.stat().st_size / (1024**2)
        print(f"   ✅ Skills CSV found: {size_mb:.2f} MB")
    
    # Check 3: Required Python packages
    print("\n3️⃣ Checking required packages...")
    try:
        import pandas
        print("   ✅ pandas installed")
    except ImportError:
        print("   ❌ pandas not installed")
        issues.append("Install: pip install pandas")
    
    try:
        import supabase
        print("   ✅ supabase installed")
    except ImportError:
        print("   ❌ supabase not installed")
        issues.append("Install: pip install supabase")
    
    try:
        import tqdm
        print("   ✅ tqdm installed")
    except ImportError:
        print("   ❌ tqdm not installed")
        issues.append("Install: pip install tqdm")
    
    # Summary
    print("\n" + "=" * 80)
    if issues:
        print("❌ PREREQUISITES NOT MET")
        print("=" * 80)
        print("\nPlease fix the following issues:\n")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        print("\nAfter fixing these issues, run this script again.")
        return False
    else:
        print("✅ ALL PREREQUISITES MET!")
        print("=" * 80)
        print("\nYou're ready to proceed with the migration.")
        return True

def show_next_steps():
    """Show next steps for migration."""
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    
    print("\n📋 Migration Process:\n")
    print("1. Create Supabase tables:")
    print("   - Run: python backend/migrate_to_supabase.py")
    print("   - The script will show SQL commands")
    print("   - Copy and run them in Supabase SQL Editor")
    print("   - Press Enter to continue\n")
    
    print("2. Upload data:")
    print("   - The script will automatically upload data in batches")
    print("   - This may take 15-30 minutes")
    print("   - Progress will be shown\n")
    
    print("3. Verify migration:")
    print("   - The script will verify data was uploaded")
    print("   - Check Supabase dashboard to confirm\n")
    
    print("4. Test application:")
    print("   - Run: python backend/run.py")
    print("   - The app should now use database instead of CSV files")
    print("   - Startup should be faster!\n")
    
    print("5. Commit changes:")
    print("   - CSV files are now in .gitignore")
    print("   - You can safely commit without large files")
    print("   - Run: git add . && git commit -m 'Migrated to Supabase database'\n")
    
    print("=" * 80)
    print("\n📖 For detailed instructions, see: DATABASE_SETUP.md")
    print("\n🚀 Ready to start migration? Run: python backend/migrate_to_supabase.py")
    print("=" * 80)

if __name__ == "__main__":
    print("\n🔧 AI Skill Gap Generator - Database Migration Helper\n")
    
    if check_prerequisites():
        show_next_steps()
    else:
        print("\n❌ Please fix the issues above before proceeding.")
        sys.exit(1)
