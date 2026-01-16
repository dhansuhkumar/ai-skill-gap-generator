import sqlite3
import os

db_path = 'users.db'
print(f"Checking database at: {os.path.abspath(db_path)}")

if not os.path.exists(db_path):
    print(f"ERROR: Database file not found!")
    exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cur.fetchall()]

print(f"\n✅ Found {len(tables)} tables:")
for table in tables:
    print(f"   - {table}")

# Check if required tables exist
required_tables = ['users', 'profiles', 'skills', 'profile_skills', 'auth_users']
missing_tables = [t for t in required_tables if t not in tables]

if missing_tables:
    print(f"\n❌ Missing tables: {missing_tables}")
else:
    print(f"\n✅ All required tables exist!")

# Check profiles table structure
print(f"\n📋 Profiles table structure:")
cur.execute("PRAGMA table_info(profiles)")
for row in cur.fetchall():
    print(f"   {row[1]} ({row[2]})")

conn.close()
