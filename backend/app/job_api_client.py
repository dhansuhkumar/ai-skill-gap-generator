"""
Job API Client - Real job posting URLs from multiple sources.

Sources:
1. JSearch (primary) - RapidAPI, 200 req/month free, pulls from LinkedIn/Indeed/Glassdoor
2. Jooble (secondary) - Free tier 500/day, needs API key in .env
3. Adzuna (tertiary) - Free tier 100/day, needs API key in .env

Returns real application URLs, not search result pages.
"""

import logging
import os
import re
import time
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from .web_skill_extractor import get_tech_skills_vocab

logger = logging.getLogger(__name__)

_JOB_CACHE: Dict[str, Tuple[List[Dict], float]] = {}
_CACHE_TTL = 3600  # 1 hour cache

JSEARCH_BASE = "https://jsearch.p.rapidapi.com/search"
JOOBLE_BASE = "https://jooble.org/api/"
ADZUNA_BASE = "https://api.adzuna.com/v1/api/jobs"

TECH_SKILLS = get_tech_skills_vocab()


# ---------------------------------------------------------------------------
# Key helpers
# ---------------------------------------------------------------------------

def _get_jsearch_key() -> Optional[str]:
    return os.getenv("JSEARCH_API_KEY", "").strip() or None


def _get_jooble_key() -> Optional[str]:
    return os.getenv("JOOBLE_API_KEY", "").strip() or None


def _get_adzuna_keys() -> Tuple[Optional[str], Optional[str]]:
    app_id = os.getenv("ADZUNA_APP_ID", "").strip() or None
    app_key = os.getenv("ADZUNA_APP_KEY", "").strip() or None
    return app_id, app_key


# ---------------------------------------------------------------------------
# Skill helpers
# ---------------------------------------------------------------------------

def _extract_skills_from_text(text: str) -> List[str]:
    """Extract skills from job description."""
    text_lower = text.lower()
    found = []
    for skill, variations in TECH_SKILLS.items():
        for variant in variations:
            if variant in text_lower:
                if skill not in found:
                    found.append(skill)
                break
    return found


def _calculate_match_score(job_description: str, user_skills: List[str]) -> int:
    """Calculate how well a job matches user's skills (0-100)."""
    if not user_skills:
        return 50

    job_skills = _extract_skills_from_text(job_description)
    if not job_skills:
        return 50

    user_lower = {s.lower().strip() for s in user_skills}
    job_lower = {s.lower().strip() for s in job_skills}

    matched = len(user_lower.intersection(job_lower))
    if matched > 0:
        return min(95, 30 + (matched * 15))
    return 40


def _filter_experience_level(
    jobs: List[Dict], experience_level: str, user_skills: List[str]
) -> List[Dict]:
    """Filter jobs by experience level (fresher/experienced/neutral)."""
    if experience_level == "neutral":
        return jobs

    fresher_keywords = [
        "entry",
        "junior",
        "fresher",
        "graduate",
        "intern",
        "0-2",
        "0-3",
        "1-3",
        "no experience",
        "new grad",
    ]
    senior_keywords = [
        "senior",
        "lead",
        "principal",
        "5+ years",
        "6+ years",
        "7+ years",
        "manager",
        "director",
    ]

    filtered = []
    for job in jobs:
        title = job.get("job_title", "").lower()
        desc = job.get("description", "").lower()
        text = f"{title} {desc}"

        has_fresher = any(kw in text for kw in fresher_keywords)
        has_senior = any(kw in text for kw in senior_keywords)

        if experience_level == "fresher":
            if has_fresher or not has_senior:
                filtered.append(job)
        elif experience_level == "experienced":
            if has_senior or not has_fresher:
                filtered.append(job)
        else:
            filtered.append(job)

    return filtered


# ---------------------------------------------------------------------------
# JSearch (PRIMARY — replaces Remotive)
# ---------------------------------------------------------------------------

def _search_jsearch(
    skills: List[str], role: str, experience_level: str, max_results: int = 15
) -> List[Dict]:
    """
    Search JSearch API (RapidAPI) for jobs aggregated from LinkedIn, Indeed,
    Glassdoor, ZipRecruiter, and more.

    Requires JSEARCH_API_KEY in env (free tier: 200 req/month).
    Sign up: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
    """
    api_key = _get_jsearch_key()
    if not api_key:
        logger.info("JSearch API key not configured — skipping JSearch")
        return []

    import requests

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }

    # Build queries based on experience level
    if experience_level == "fresher":
        base_skills = " ".join(skills[:2]) if skills else role
        queries = [
            f"junior {base_skills} developer",
            f"entry level {role}",
            f"fresher {base_skills}",
        ]
    else:
        base_skills = " ".join(skills[:2]) if skills else role
        queries = [
            f"{base_skills} {role}",
            f"{role} developer",
            f"{base_skills} engineer",
        ]

    jobs = []
    seen = set()

    for query in queries:
        if len(jobs) >= max_results:
            break

        try:
            params = {
                "query": query,
                "page": "1",
                "num_pages": "1",
                "date_posted": "month",       # jobs posted this month
                "employment_types": "FULLTIME,CONTRACTOR,PARTTIME",
            }

            response = requests.get(
                JSEARCH_BASE, headers=headers, params=params, timeout=12
            )

            if response.status_code == 200:
                data = response.json()
                job_list = data.get("data", [])

                logger.info(
                    f"JSearch query '{query}': {len(job_list)} raw results"
                )

                for j in job_list:
                    apply_link = j.get("job_apply_link", "")
                    if not apply_link or apply_link in seen:
                        continue
                    seen.add(apply_link)

                    desc = j.get("job_description", "")[:2000]
                    match_score = _calculate_match_score(desc, skills)

                    # Build a clean location string
                    city = j.get("job_city", "")
                    state = j.get("job_state", "")
                    country = j.get("job_country", "")
                    location_parts = [p for p in [city, state, country] if p]
                    location_str = ", ".join(location_parts) if location_parts else "Remote"

                    if j.get("job_is_remote"):
                        location_str = "Remote"

                    # Salary range
                    sal_min = j.get("job_min_salary")
                    sal_max = j.get("job_max_salary")
                    salary_str = ""
                    if sal_min and sal_max:
                        salary_str = f"{sal_min}–{sal_max} {j.get('job_salary_currency', '')}".strip()
                    elif sal_min:
                        salary_str = f"{sal_min}+ {j.get('job_salary_currency', '')}".strip()

                    # Publisher / source site (e.g., "linkedin.com", "indeed.com")
                    publisher = j.get("job_publisher", "")

                    jobs.append(
                        {
                            "job_link": apply_link,
                            "job_title": j.get("job_title", ""),
                            "company": j.get("employer_name", ""),
                            "company_logo": j.get("employer_logo", ""),
                            "job_location": location_str,
                            "description": desc,
                            "salary": salary_str,
                            "job_type": j.get("job_employment_type", ""),
                            "published_date": j.get("job_posted_at_datetime_utc", ""),
                            "source": "jsearch",
                            "publisher": publisher,
                            "success_rate": match_score,
                            "required_skills": _extract_skills_from_text(desc),
                        }
                    )

            elif response.status_code == 429:
                logger.warning("JSearch rate limit hit — stopping JSearch queries")
                break
            else:
                logger.warning(
                    f"JSearch returned HTTP {response.status_code} for '{query}'"
                )

        except Exception as e:
            logger.warning(f"JSearch search failed for '{query}': {e}")
            continue

    jobs = _filter_experience_level(jobs, experience_level, skills)
    jobs.sort(key=lambda x: x.get("success_rate", 0), reverse=True)
    return jobs[:max_results]


# ---------------------------------------------------------------------------
# Jooble (secondary fallback)
# ---------------------------------------------------------------------------

def _search_jooble(
    skills: List[str],
    role: str,
    experience_level: str,
    location: str = "India",
    max_results: int = 15,
) -> List[Dict]:
    """
    Search Jooble API for jobs.
    Requires free API key in JOOBLE_API_KEY env var.
    """
    api_key = _get_jooble_key()
    if not api_key:
        logger.info("Jooble API key not configured")
        return []

    import requests

    jobs = []
    search_queries = []

    for skill in skills[:3]:
        search_queries.append(f"{skill} {role}")
    search_queries.append(f"{role} {location}")

    headers = {"Content-Type": "application/json"}

    for query in search_queries:
        if len(jobs) >= max_results:
            break

        try:
            body = {"keywords": query, "location": location, "page": 1}

            response = requests.post(
                f"{JOOBLE_BASE}{api_key}", json=body, headers=headers, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                job_list = data.get("jobs", [])

                for j in job_list:
                    job_url = j.get("link", "")
                    if not job_url:
                        continue

                    desc = j.get("snippet", "")[:2000]
                    match_score = _calculate_match_score(desc, skills)

                    jobs.append(
                        {
                            "job_link": job_url,
                            "job_title": j.get("title", ""),
                            "company": j.get("company", ""),
                            "job_location": j.get("location", ""),
                            "description": desc,
                            "salary": j.get("salary", ""),
                            "source": "jooble",
                            "success_rate": match_score,
                            "required_skills": _extract_skills_from_text(desc),
                        }
                    )

        except Exception as e:
            logger.warning(f"Jooble search failed for '{query}': {e}")
            continue

    jobs = _filter_experience_level(jobs, experience_level, skills)
    jobs.sort(key=lambda x: x.get("success_rate", 0), reverse=True)
    return jobs[:max_results]


# ---------------------------------------------------------------------------
# Adzuna (tertiary fallback)
# ---------------------------------------------------------------------------

def _search_adzuna(
    skills: List[str],
    role: str,
    experience_level: str,
    country: str = "in",
    max_results: int = 15,
) -> List[Dict]:
    """
    Search Adzuna API for jobs.
    Requires free API key in ADZUNA_APP_ID and ADZUNA_APP_KEY env vars.
    """
    app_id, app_key = _get_adzuna_keys()
    if not app_id or not app_key:
        logger.info("Adzuna API keys not configured")
        return []

    import requests

    jobs = []
    search_queries = []

    top_skills = skills[:3] if skills else []

    if experience_level == "fresher":
        if top_skills:
            search_queries.append(f"{top_skills[0]} developer fresher")
            if len(top_skills) > 1:
                search_queries.append(f"{top_skills[0]} {top_skills[1]} fresher")
        search_queries.append("software engineer fresher")
        search_queries.append("developer fresher")
        search_queries.append("fresher software developer")
    else:
        if top_skills:
            search_queries.append(f"{top_skills[0]} developer")
            if len(top_skills) > 1:
                search_queries.append(f"{top_skills[0]} {top_skills[1]} developer")
        search_queries.append(role)
        search_queries.append("software engineer")

    seen = set()

    for query in search_queries:
        if len(jobs) >= max_results:
            break

        try:
            params = {
                "app_id": app_id,
                "app_key": app_key,
                "what": query,
                "where": country,
                "results_per_page": max_results,
            }

            response = requests.get(
                f"{ADZUNA_BASE}/{country}/search/1", params=params, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])

                logger.info(f"Adzuna query '{query}': {len(results)} results")

                for j in results:
                    job_url = j.get("redirect_url", "")
                    if not job_url or job_url in seen:
                        continue
                    seen.add(job_url)

                    title = j.get("title", "")
                    desc = (
                        j.get("description", "")[:2000] if j.get("description") else ""
                    )
                    match_score = _calculate_match_score(desc, skills)

                    company = j.get("company", "")
                    if isinstance(company, dict):
                        company = company.get("display_name", "")
                    else:
                        company = str(company) if company else ""

                    location = j.get("location", "")
                    if isinstance(location, dict):
                        location = location.get("display_name", "")
                    else:
                        location = str(location) if location else ""

                    jobs.append(
                        {
                            "job_link": job_url,
                            "job_title": title,
                            "company": company,
                            "job_location": location,
                            "description": desc,
                            "salary": str(
                                j.get("salary_min", "") or j.get("salary_max", "") or ""
                            ),
                            "source": "adzuna",
                            "success_rate": match_score,
                            "required_skills": _extract_skills_from_text(desc),
                        }
                    )

        except Exception as e:
            logger.warning(f"Adzuna search failed for '{query}': {e}")
            continue

    jobs = _filter_experience_level(jobs, experience_level, skills)
    jobs.sort(key=lambda x: x.get("success_rate", 0), reverse=True)
    return jobs[:max_results]


# ---------------------------------------------------------------------------
# Location helpers
# ---------------------------------------------------------------------------

def _is_job_nearby(job_location: str, user_location: Dict) -> bool:
    """Check if job location is near user's location."""
    if not job_location or not user_location:
        return False

    user_city = user_location.get("city", "").lower()
    user_state = user_location.get("state", "").lower()
    job_loc_lower = job_location.lower()

    nearby_cities = {
        "bangalore": ["bengaluru", "bengalore", "mysore", "hubli"],
        "bengaluru": ["bangalore", "bengalore", "mysore", "hubli"],
        "mumbai": ["navi mumbai", "thane", "pune", "nashik"],
        "delhi": [
            "new delhi",
            "gurgaon",
            "gurugram",
            "noida",
            "faridabad",
            "ghaziabad",
        ],
        "new delhi": [
            "delhi",
            "gurgaon",
            "gurugram",
            "noida",
            "faridabad",
            "ghaziabad",
        ],
        "gurgaon": ["gurugram", "delhi", "new delhi", "noida", "faridabad"],
        "gurugram": ["gurgaon", "delhi", "new delhi", "noida", "faridabad"],
        "noida": ["greater noida", "delhi", "new delhi", "gurgaon", "gurugram"],
        "hyderabad": ["secunderabad", "warangal"],
        "secunderabad": ["hyderabad", "warangal"],
        "chennai": ["coimbatore", "madurai", "trichy"],
        "pune": ["mumbai", "nagpur"],
        "kolkata": ["howrah", "siliguri", "durgapur"],
        "kochi": ["trivandrum", "thiruvananthapuram", "kozhikode"],
    }

    if user_city:
        metro_cities = nearby_cities.get(user_city, [])
        if user_city in job_loc_lower or any(
            city in job_loc_lower for city in metro_cities
        ):
            return True

        if user_state and user_state in job_loc_lower:
            return True

    return False


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def search_jobs(
    skills: List[str],
    role: str,
    experience_level: str = "neutral",
    location: str = "India",
    max_results: int = 20,
    user_location: Dict = None,
) -> Dict:
    """
    Search all configured job APIs and return combined, deduplicated results.

    Priority order:
      1. JSearch  (LinkedIn/Indeed/Glassdoor via RapidAPI) — needs JSEARCH_API_KEY
      2. Jooble   (global aggregator)                      — needs JOOBLE_API_KEY
      3. Adzuna   (India-focused aggregator)               — needs ADZUNA_APP_ID/KEY

    Args:
        skills: User's skills for matching
        role: Target job role
        experience_level: "fresher", "experienced", or "neutral"
        location: Geographic location filter
        max_results: Maximum jobs to return
        user_location: Dict with city, state, country extracted from resume

    Returns:
        Dict with:
            - jobs: List of job dicts with real application URLs
            - total_found: Total jobs found across all sources
            - sources: Which APIs were used
    """
    if user_location is None:
        user_location = {}

    user_city = user_location.get("city", "").lower()
    cache_key = (
        f"{','.join(sorted(skills[:5]))}|{role}|{experience_level}"
        f"|{location}|{max_results}|{user_city}"
    )

    if cache_key in _JOB_CACHE:
        cached_jobs, cached_time = _JOB_CACHE[cache_key]
        if time.time() - cached_time < _CACHE_TTL:
            logger.info("Using cached job results")
            return {
                "jobs": cached_jobs[:max_results],
                "total_found": len(cached_jobs),
                "sources": ["cache"],
                "cached": True,
            }

    logger.info(
        f"Searching jobs: role={role}, exp={experience_level}, "
        f"city={user_city}, skills={len(skills)}"
    )

    all_jobs = []
    sources_used = []

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {}

        # JSearch — primary
        if _get_jsearch_key():
            futures[
                executor.submit(
                    _search_jsearch, skills, role, experience_level, max_results
                )
            ] = "jsearch"
        else:
            logger.info(
                "JSearch key not set — skipping. "
                "Get a free key at https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch"
            )

        # Jooble — secondary fallback
        if _get_jooble_key():
            futures[
                executor.submit(
                    _search_jooble,
                    skills,
                    role,
                    experience_level,
                    location,
                    max_results,
                )
            ] = "jooble"

        # Adzuna — tertiary fallback
        if _get_adzuna_keys()[0]:
            futures[
                executor.submit(
                    _search_adzuna, skills, role, experience_level, "in", max_results
                )
            ] = "adzuna"

        for future in as_completed(futures):
            source = futures[future]
            try:
                jobs = future.result()
                if jobs:
                    all_jobs.extend(jobs)
                    sources_used.append(source)
                    logger.info(f"{source}: Found {len(jobs)} jobs")
            except Exception as e:
                logger.warning(f"{source} search failed: {e}")

    # Deduplicate by URL
    seen_urls = set()
    unique_jobs = []
    for job in all_jobs:
        url = job.get("job_link", "")
        if url and url not in seen_urls:
            seen_urls.add(url)

            job_location = job.get("job_location", "").lower()
            is_remote = "remote" in job_location or "work from home" in job_location

            if user_location and not is_remote:
                is_nearby = _is_job_nearby(job.get("job_location", ""), user_location)
                job["location_match"] = is_nearby
            else:
                job["location_match"] = is_remote

            unique_jobs.append(job)

    def _sort_jobs_key(job):
        score = job.get("success_rate", 0)
        location_match = job.get("location_match", False)
        is_remote = "remote" in job.get("job_location", "").lower()

        if location_match:
            score += 30
        elif is_remote:
            score += 15

        return score

    unique_jobs.sort(key=_sort_jobs_key, reverse=True)

    nearby_count = sum(1 for j in unique_jobs if j.get("location_match", False))
    logger.info(
        f"Total unique jobs: {len(unique_jobs)}, nearby: {nearby_count}, "
        f"sources: {sources_used}"
    )

    _JOB_CACHE[cache_key] = (unique_jobs, time.time())

    return {
        "jobs": unique_jobs[:max_results],
        "total_found": len(unique_jobs),
        "nearby_count": nearby_count,
        "sources": sources_used or [],
        "cached": False,
    }


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def get_job_match_stats(jobs: List[Dict], user_skills: List[str]) -> Dict:
    """Calculate match statistics for job results."""
    if not jobs:
        return {
            "avg_match": 0,
            "high_match_count": 0,
            "medium_match_count": 0,
            "low_match_count": 0,
        }

    scores = [j.get("success_rate", 0) for j in jobs]
    avg = sum(scores) // len(scores)

    return {
        "avg_match": avg,
        "high_match_count": len([s for s in scores if s >= 70]),
        "medium_match_count": len([s for s in scores if 50 <= s < 70]),
        "low_match_count": len([s for s in scores if s < 50]),
    }


def clear_job_cache():
    """Clear the job search cache."""
    global _JOB_CACHE
    _JOB_CACHE.clear()
    logger.info("Job cache cleared")
