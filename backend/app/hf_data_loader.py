"""
HuggingFace Data Loader - Loads job/skill data from HuggingFace Datasets.
Uses Arrow/Parquet format with local caching for fast retrieval.
"""

import os
import functools
from typing import List, Dict, Optional
from collections import Counter, defaultdict

# HuggingFace dataset configuration
HF_USERNAME = os.getenv("HF_USERNAME", "dhansuhkumar")
HF_JOBS_DATASET = os.getenv("HF_JOBS_DATASET", f"{HF_USERNAME}/skill-gap-jobs")
HF_SKILLS_DATASET = os.getenv("HF_SKILLS_DATASET", f"{HF_USERNAME}/skill-gap-skills")
HF_PROJECTS_DATASET = os.getenv(
    "HF_PROJECTS_DATASET", f"{HF_USERNAME}/skill-gap-projects"
)
HF_LEARNING_PATHS_DATASET = os.getenv(
    "HF_LEARNING_PATHS_DATASET", f"{HF_USERNAME}/skill-gap-learning-paths"
)


class HFDataLoader:
    """Load and query job/skill data from HuggingFace Datasets with local caching."""

    _instance = None
    _jobs_df = None
    _skills_df = None
    _projects_df = None
    _learning_paths_df = None
    _initialized = False
    _projects_initialized = False
    _paths_initialized = False

    # ── In-memory inverted index: normalised_title_word -> list[job_row_dict] ──
    _role_index: dict = {}  # built once after datasets load
    # Merged view: normalised_title -> list[str] (skills)
    _role_skills_index: dict = {}  # "machine learning engineer" -> ["Python", ...]
    # Real job data indexed by lowercase title: normalised_title -> [job_row, ...]
    _role_jobs_index: dict = {}  # "machine learning engineer" -> [{job_link, company, job_location}, ...]
    _MAX_JOBS_PER_TITLE = 15  # Memory management: store max 15 samples per title

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _ensure_loaded(self):
        """Lazy load datasets on first access."""
        if self._initialized:
            return

        try:
            import datasets
            import pandas as pd

            # Set a 10-second timeout for downloading to prevent backend hang
            from datasets import DownloadConfig

            dl_config = DownloadConfig(max_retries=1)
            # Apply global timeout hack for older datasets versions
            import os

            os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "10"

            print(f"📥 Loading datasets from HuggingFace Hub (10s timeout)...")
            print(f"   Jobs: {HF_JOBS_DATASET}")
            print(f"   Skills: {HF_SKILLS_DATASET}")

            # Load datasets with timeout configuration
            jobs_ds = datasets.load_dataset(
                HF_JOBS_DATASET, split="train", download_config=dl_config
            )
            skills_ds = datasets.load_dataset(
                HF_SKILLS_DATASET, split="train", download_config=dl_config
            )

            # Convert to pandas for fast in-memory operations
            self._jobs_df = jobs_ds.to_pandas()
            self._skills_df = skills_ds.to_pandas()

            print(
                f"✅ Loaded {len(self._jobs_df):,} jobs and {len(self._skills_df):,} skill mappings"
            )
            self._initialized = True

            # ── Build fast in-memory index once ───────────────────────────
            self._build_role_skills_index()

        except Exception as e:
            print(f"❌ Failed to load HuggingFace datasets: {e}")
            import pandas as pd

            self._jobs_df = pd.DataFrame()
            self._skills_df = pd.DataFrame()
            self._initialized = True

    def _ensure_projects_loaded(self):
        """Lazy load projects dataset."""
        if self._projects_initialized:
            return

        try:
            import datasets
            import pandas as pd

            from datasets import DownloadConfig

            dl_config = DownloadConfig(max_retries=1)
            import os

            os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "10"

            print(f"📥 Loading projects from: {HF_PROJECTS_DATASET} (10s timeout)")
            projects_ds = datasets.load_dataset(
                HF_PROJECTS_DATASET, split="train", download_config=dl_config
            )
            self._projects_df = projects_ds.to_pandas()
            print(f"✅ Loaded {len(self._projects_df)} projects")
            self._projects_initialized = True

        except Exception as e:
            print(f"⚠️ Failed to load projects dataset: {e}")
            import pandas as pd

            self._projects_df = pd.DataFrame()
            self._projects_initialized = True

    def _build_role_skills_index(self):
        """
        Build in-memory indexes:
        - normalised_job_title -> [skill, skill, ...]
        - normalised_job_title -> [{job_link, company, job_location}, ...] (max 15 per title)
        Called ONCE after the datasets are loaded into memory.
        """
        if self._jobs_df is None or self._jobs_df.empty:
            return
        if self._skills_df is None or self._skills_df.empty:
            return

        import pandas as pd

        print("🔧 Building role→skills in-memory index...")

        # Build job_link -> skills mapping from skills DataFrame
        link_to_skills: dict = defaultdict(list)
        if (
            "job_link" in self._skills_df.columns
            and "job_skills" in self._skills_df.columns
        ):
            for _, row in self._skills_df.iterrows():
                link = row["job_link"]
                skills_str = row.get("job_skills", "")
                if pd.notna(skills_str) and skills_str:
                    for s in str(skills_str).split(","):
                        s = s.strip()
                        if s:
                            link_to_skills[link].append(s)

        # Build title -> aggregated skills index AND title -> real job samples index
        if "job_title" in self._jobs_df.columns and "job_link" in self._jobs_df.columns:
            title_skills: dict = defaultdict(list)
            title_jobs: dict = defaultdict(list)
            for _, row in self._jobs_df.iterrows():
                title = str(row.get("job_title", "")).lower().strip()
                link = row.get("job_link", "")
                if title:
                    if link in link_to_skills:
                        title_skills[title].extend(link_to_skills[link])
                    # Store real job metadata for fast path (max 15 per title)
                    if len(title_jobs[title]) < self._MAX_JOBS_PER_TITLE:
                        title_jobs[title].append(
                            {
                                "job_link": row.get("job_link", ""),
                                "company": row.get("company", ""),
                                "job_location": row.get("job_location", ""),
                                "job_level": row.get("job_level", ""),
                                "job_type": row.get("job_type", ""),
                            }
                        )

            self._role_skills_index = dict(title_skills)
            self._role_jobs_index = dict(title_jobs)

        print(f"✅ Index built: {len(self._role_skills_index):,} unique role titles")
        print(
            f"✅ Job index built: {len(self._role_jobs_index):,} titles with real job data"
        )

    # ==================== LEARNING PATHS ====================
    def _ensure_learning_paths_loaded(self):
        """Lazy load learning paths dataset."""
        if self._paths_initialized:
            return

        try:
            import datasets
            import pandas as pd

            from datasets import DownloadConfig

            dl_config = DownloadConfig(max_retries=1)
            import os

            os.environ["HF_HUB_DOWNLOAD_TIMEOUT"] = "10"

            print(
                f"📥 Loading learning paths from: {HF_LEARNING_PATHS_DATASET} (10s timeout)"
            )
            paths_ds = datasets.load_dataset(
                HF_LEARNING_PATHS_DATASET, split="train", download_config=dl_config
            )
            self._learning_paths_df = paths_ds.to_pandas()
            print(f"✅ Loaded {len(self._learning_paths_df)} learning path phases")
            self._paths_initialized = True

        except Exception as e:
            print(f"⚠️ Failed to load learning paths dataset: {e}")
            import pandas as pd

            self._learning_paths_df = pd.DataFrame()
            self._paths_initialized = True

    def get_all_job_titles(self) -> List[str]:
        """Return all unique job titles."""
        self._ensure_loaded()
        if self._jobs_df is None or "job_title" not in self._jobs_df.columns:
            return []
        return self._jobs_df["job_title"].dropna().unique().tolist()

    def find_matching_jobs(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Find jobs matching a query string.
        Uses the pre-built in-memory index for O(1) lookup,
        falls back to DataFrame scan if index not ready.
        """
        self._ensure_loaded()
        if self._jobs_df is None or self._jobs_df.empty:
            return []

        query_lower = query.lower().strip()

        # ── Fast path: use pre-built index ───────────────────────────────────
        if self._role_skills_index and self._role_jobs_index:
            # Gather all titles that contain the query keyword
            matched_titles = [
                title for title in self._role_skills_index if query_lower in title
            ][:limit]

            results = []
            for title in matched_titles:
                # Get real job samples for this title from _role_jobs_index
                job_samples = self._role_jobs_index.get(title, [])
                if job_samples:
                    # Return first available real job data
                    sample = job_samples[0]
                    results.append(
                        {
                            "job_link": sample.get("job_link", ""),
                            "job_title": title,
                            "company": sample.get("company", ""),
                            "job_location": sample.get("job_location", ""),
                            "job_level": sample.get("job_level", ""),
                            "job_type": sample.get("job_type", ""),
                        }
                    )
                else:
                    # Fallback only if no real data available
                    results.append(
                        {
                            "job_link": "",
                            "job_title": title,
                            "company": "",
                            "job_location": "",
                            "job_level": "",
                            "job_type": "",
                        }
                    )
            if results:
                return results[:limit]

        # ── Slow path: DataFrame scan (fallback if index not ready) ────────
        import pandas as pd

        mask = (
            self._jobs_df["job_title"].str.lower().str.contains(query_lower, na=False)
        )
        matched = self._jobs_df[mask].head(limit)

        results = []
        for _, row in matched.iterrows():
            results.append(
                {
                    "job_link": row.get("job_link", ""),
                    "job_title": row.get("job_title", ""),
                    "company": row.get("company", ""),
                    "job_location": row.get("job_location", ""),
                    "job_level": row.get("job_level", ""),
                    "job_type": row.get("job_type", ""),
                }
            )

        return results

    def get_job_links_for_titles(self, job_titles: List[str]) -> List[str]:
        """Get job_links for a list of job titles."""
        self._ensure_loaded()
        if self._jobs_df is None or self._jobs_df.empty or not job_titles:
            return []

        import pandas as pd

        # Create a mask for matching titles
        titles_set = set(t.lower() for t in job_titles)
        mask = (
            self._jobs_df["job_title"]
            .str.lower()
            .apply(lambda x: x in titles_set if pd.notna(x) else False)
        )

        return self._jobs_df[mask]["job_link"].dropna().unique().tolist()

    def get_skills_for_job_links(self, job_links: List[str]) -> Dict[str, List[str]]:
        """Get skills mapping for a list of job_links or title proxy keys."""
        self._ensure_loaded()

        # ── Fast path: check index (titles used as proxy keys) ────────────────
        if self._role_skills_index:
            result = {}
            missing_links = []
            for link in job_links:
                title_key = link.lower().strip()
                if title_key in self._role_skills_index:
                    result[link] = self._role_skills_index[title_key]
                else:
                    missing_links.append(link)

            # Fall through to DataFrame for any real job_links not in index
            if (
                missing_links
                and self._skills_df is not None
                and not self._skills_df.empty
            ):
                import pandas as pd

                mask = self._skills_df["job_link"].isin(missing_links)
                filtered = self._skills_df[mask]
                for _, row in filtered.iterrows():
                    link = row["job_link"]
                    skills_str = row.get("job_skills", "")
                    if pd.notna(skills_str) and skills_str:
                        result[link] = [s.strip() for s in str(skills_str).split(",")]
            return result

        # ── Slow path: always scan DataFrame ──────────────────────────────
        if self._skills_df is None or self._skills_df.empty or not job_links:
            return {}

        import pandas as pd

        mask = self._skills_df["job_link"].isin(job_links)
        filtered = self._skills_df[mask]

        result = {}
        for _, row in filtered.iterrows():
            link = row["job_link"]
            skills_str = row.get("job_skills", "")
            if pd.notna(skills_str) and skills_str:
                skills = [s.strip() for s in str(skills_str).split(",")]
                result[link] = skills

        return result

    def get_projects_for_skills(self, skills: List[str], limit: int = 5) -> List[Dict]:
        self._ensure_projects_loaded()
        if self._projects_df is None or self._projects_df.empty:
            return []

        import pandas as pd

        results = []
        skills_lower = [s.lower() for s in skills]

        for _, row in self._projects_df.iterrows():
            proj_skills = str(row.get("skills", "")).lower()
            match_count = sum(1 for s in skills_lower if s in proj_skills)
            if match_count > 0:
                results.append(
                    (
                        match_count,
                        {
                            "title": row.get("title", ""),
                            "description": row.get("description", ""),
                            "skills": [
                                s.strip()
                                for s in str(row.get("skills", "")).split(",")
                                if s.strip()
                            ],
                        },
                    )
                )

        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:limit]]

    def get_learning_path_for_skill(self, skill: str, days: int = 7) -> Dict:
        self._ensure_learning_paths_loaded()
        if self._learning_paths_df is None or self._learning_paths_df.empty:
            return {}

        import pandas as pd

        skill_lower = skill.lower()
        mask = self._learning_paths_df["skill"].str.lower() == skill_lower
        matched = self._learning_paths_df[mask]
        if matched.empty:
            return {}

        steps = []
        for _, row in matched.iterrows():
            steps.append(
                {
                    "day_from": row.get("day_from", 1),
                    "day_to": row.get("day_to", 2),
                    "title": row.get("title", ""),
                    "tasks": [
                        t.strip()
                        for t in str(row.get("tasks", "")).split(",")
                        if t.strip()
                    ],
                    "project": row.get("project", ""),
                    "resources": [],
                }
            )

        return {"skill": skill, "summary": f"Learning path for {skill}", "steps": steps}

    def get_required_skills(self, query: str, limit_jobs: int = 20) -> List[str]:
        jobs = self.find_matching_jobs(query, limit=limit_jobs)
        skills_map = self.get_skills_for_job_links(
            [j.get("job_link", "") for j in jobs]
        )

        from collections import Counter

        all_skills = []
        for skills in skills_map.values():
            all_skills.extend(skills)

        counter = Counter([s for s in all_skills if s.strip()])
        return [skill for skill, _ in counter.most_common(20)]

    def get_similar_job_titles(self, query: str, limit: int = 10) -> List[str]:
        jobs = self.find_matching_jobs(query, limit=limit)
        titles = set()
        for j in jobs:
            t = j.get("job_title", "").strip()
            if t:
                titles.add(t.title())
        return list(titles)[:limit]


# Singleton instance
hf_loader = HFDataLoader()


# Convenience functions (maintain same API as db_data_loader)
def get_all_job_titles():
    return hf_loader.get_all_job_titles()


@functools.lru_cache(maxsize=256)
def find_matching_jobs(query: str, limit: int = 10):
    """Cached wrapper — same role query returns instantly on repeat calls."""
    return hf_loader.find_matching_jobs(query, limit)


def get_required_skills(query: str, limit_jobs: int = 20):
    return hf_loader.get_required_skills(query, limit_jobs)


def get_similar_job_titles(query: str, limit: int = 10):
    return hf_loader.get_similar_job_titles(query, limit)


# New convenience functions for projects and learning paths
def get_projects_for_skills(skills: List[str], limit: int = 5):
    return hf_loader.get_projects_for_skills(skills, limit)


def get_learning_path_for_skill(skill: str, days: int = 7):
    return hf_loader.get_learning_path_for_skill(skill, days)
