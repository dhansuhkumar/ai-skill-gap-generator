-- migrations/create_phase2_tables.sql

CREATE TABLE IF NOT EXISTS profiles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT,            -- link to your users table (JWT subject)
  display_name TEXT,
  resume_parsed_json TEXT, -- store parser output as JSON string
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS skills (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS profile_skills (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  profile_id INTEGER,
  skill_id INTEGER,
  confidence INTEGER,
  source TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(profile_id) REFERENCES profiles(id),
  FOREIGN KEY(skill_id) REFERENCES skills(id)
);

