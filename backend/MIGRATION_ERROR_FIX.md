# Migration Error Fix Guide

## Errors Encountered

During the initial migration, we encountered two errors:

### 1. NaN Value Error
```
'invalid input syntax for type json'
Token "NaN" is invalid
```

**Cause:** CSV files contain NaN (Not a Number) values from pandas, which cannot be serialized to JSON for Supabase.

**Fix:** Replace all NaN values with `None` (null in JSON) before uploading.

### 2. Row-Level Security Policy Error
```
'new row violates row-level security policy for table "job_skills"'
```

**Cause:** The original SQL only created SELECT policies, but didn't create INSERT policies. RLS blocks all operations by default unless explicitly allowed.

**Fix:** Add INSERT policies to allow data uploads.

---

## How to Fix

### Option 1: Use the Fixed Script (Recommended)

1. **Stop the current migration** (if still running)
   - Press Ctrl+C in the terminal

2. **Run the fixed script:**
   ```bash
   python backend/migrate_to_supabase_fixed.py
   ```

3. **Update Supabase policies:**
   - The script will show new SQL commands
   - Go to Supabase Dashboard → SQL Editor
   - Run the new SQL (it includes DROP POLICY and CREATE POLICY for INSERT)
   - Press Enter to continue

4. **Data will upload successfully** with NaN handling

---

### Option 2: Manual Fix (If you want to continue current migration)

#### Step 1: Add INSERT Policies in Supabase

Go to Supabase Dashboard → SQL Editor and run:

```sql
-- Add INSERT policies
CREATE POLICY "Allow public insert on job_postings"
    ON job_postings FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Allow public insert on job_skills"
    ON job_skills FOR INSERT
    WITH CHECK (true);
```

#### Step 2: Clean the CSV Data

The NaN issue requires re-running with cleaned data, so Option 1 is better.

---

## What the Fixed Script Does

1. **Cleans NaN values:**
   ```python
   df = df.replace({np.nan: None})
   records = [clean_record(r) for r in records]
   ```

2. **Adds INSERT policies:**
   ```sql
   CREATE POLICY "Allow public insert on job_postings"
       ON job_postings FOR INSERT
       WITH CHECK (true);
   ```

3. **Better error handling** for debugging

---

## Recommended Action

**Use the fixed script:**
```bash
python backend/migrate_to_supabase_fixed.py
```

This will:
- ✅ Handle NaN values automatically
- ✅ Create proper RLS policies (SELECT + INSERT)
- ✅ Upload all data successfully
