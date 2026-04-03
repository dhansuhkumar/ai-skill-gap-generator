"""Web search module using DuckDuckGo for finding learning resources and live jobs."""

import logging
import re
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

_SEARCH_CACHE = {}


# Seniority keywords to exclude for fresher searches
SENIOR_KEYWORDS = [
    "senior",
    "sr.",
    "sr ",
    "lead",
    "principal",
    "staff engineer",
    "director",
    "manager",
    "head of",
    "vp",
    "chief",
]
# Experience-friendly keywords to include
JUNIOR_KEYWORDS = [
    "junior",
    "jr.",
    "jr ",
    "entry level",
    "entry-level",
    "fresher",
    "new grad",
    "graduate",
    "intern",
    "0-2 years",
    "0-3 years",
    "1-3 years",
]


def _is_senior_role(title: str, snippet: str) -> bool:
    """Check if a job posting is for a senior/experienced role."""
    text = f"{title} {snippet}".lower()
    return any(kw in text for kw in SENIOR_KEYWORDS)


def _build_job_queries(
    role: str, experience_level: str, skills: List[str]
) -> List[str]:
    """Build targeted search queries based on role and experience level."""
    queries = []

    if experience_level == "fresher":
        queries.extend(
            [
                f"{role} entry level jobs 2025",
                f"{role} junior jobs for freshers",
                f"hiring {role} no experience required",
                f"site:linkedin.com {role} entry level OR junior",
                f"site:indeed.com {role} fresher OR entry level",
            ]
        )
        if skills:
            queries.append(f"{role} jobs {skills[0]} entry level")
    elif experience_level == "experienced":
        queries.extend(
            [
                f"senior {role} jobs hiring",
                f"lead {role} positions",
                f"{role} 5+ years experience",
                f"site:linkedin.com senior {role}",
                f"site:indeed.com senior {role}",
            ]
        )
        if skills:
            queries.append(f"senior {role} {skills[0]}")
    else:
        queries.extend(
            [
                f"{role} jobs hiring now",
                f"site:linkedin.com/jobs {role}",
                f"site:indeed.com {role} jobs",
                f"{role} careers open positions",
            ]
        )
        if skills:
            queries.extend(
                [
                    f"{role} {skills[0]} jobs",
                    f"{role} developer jobs {skills[0]}",
                ]
            )

    return queries[:8]


def _parse_job_title(title: str) -> tuple:
    """Parse job title to extract company name and clean title."""
    title = title.strip()

    patterns = [
        r"^([^-\|]+?)\s*[-|]\s*(.+)$",
        r"^([^-\|]+?)\s*[-|]\s*(.+?)\s*[-|]",
    ]

    for pattern in patterns:
        match = re.match(pattern, title, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            clean_title = match.group(2).strip()
            if len(company) > 1 and len(clean_title) > 2:
                return company, clean_title

    return "", title


def _extract_location_from_snippet(snippet: str) -> str:
    """Try to extract location from job snippet."""
    patterns = [
        r"(?:location|Location)[:\s]+([A-Za-z\s,]+?)(?:\.|,|$)",
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?,\s*[A-Z]{2})\s*[-–]",
        r"(Remote|remote|Hybrid|hybrid|On-site|onsite)",
    ]

    for pattern in patterns:
        match = re.search(pattern, snippet)
        if match:
            loc = match.group(1).strip()
            if loc and len(loc) < 50:
                return loc

    return ""


def _validate_url(url: str) -> bool:
    """Check if URL is valid and points to a job board or company career page."""
    if not url:
        return False
    url_lower = url.lower()
    job_boards = [
        "linkedin.com/jobs",
        "indeed.com",
        "glassdoor.com",
        "monster.com",
        "greenhouse.io",
        "boards.greenhouse.io",
        "lever.co",
        "jobs.lever.co",
        "workday.com",
        "bamboohr.com",
        "myworkdayjobs.com",
        "smartrecruiters.com",
        "recruitee.com",
        "ashbyhq.com",
        "triplebyte.com",
        "underdog.io",
        "karat.com",
        "careers.page",
        "careers.",
        "jobvite.com",
        "taleo.net",
        "brassring.com",
    ]
    return any(board in url_lower for board in job_boards)


def search_live_jobs(
    role: str,
    experience_level: str = "neutral",
    skills: Optional[List[str]] = None,
    max_results: int = 15,
) -> List[Dict]:
    """
    Phase 1: Real-time job search with experience-level filtering.

    Translates experience_level into targeted search queries:
    - fresher: Includes "junior", "entry level", excludes "senior", "lead"
    - experienced: Includes "senior", "lead", excludes "junior"
    - neutral: General job search

    Returns real URLs from job boards (LinkedIn, Indeed, etc.)
    """
    if skills is None:
        skills = []

    cache_key = f"jobs:{role}:{experience_level}:{','.join(skills[:3])}:{max_results}"
    if cache_key in _SEARCH_CACHE:
        logger.info(f"Using cached job results for {role}")
        return _SEARCH_CACHE[cache_key]

    try:
        from ddgs import DDGS

        results = []
        seen_urls = set()
        queries = _build_job_queries(role, experience_level, skills)

        logger.info(
            f"Searching live jobs: role={role}, exp={experience_level}, queries={queries}"
        )

        with DDGS() as ddgs:
            for query in queries:
                if len(results) >= max_results:
                    break

                raw_count = 0
                try:
                    for r in ddgs.text(query, max_results=15):
                        raw_count += 1
                        url = r.get("href", "")
                        title = r.get("title", "")
                        snippet = r.get("body", "")

                        if not url or url in seen_urls:
                            continue

                        # Skip non-job URLs more broadly
                        if not _validate_url(url):
                            continue

                        # Filter by experience level for freshers
                        if experience_level == "fresher" and _is_senior_role(
                            title, snippet
                        ):
                            logger.debug(f"Filtered senior role: {title}")
                            continue

                        seen_urls.add(url)
                        company, clean_title = _parse_job_title(title)
                        location = _extract_location_from_snippet(snippet)

                        results.append(
                            {
                                "job_link": url,
                                "job_title": clean_title or title,
                                "company": company,
                                "job_location": location,
                                "snippet": snippet[:300] if snippet else "",
                                "source": "live_search",
                                "experience_filter": experience_level,
                            }
                        )

                        if len(results) >= max_results:
                            break

                    logger.info(
                        f"Query '{query[:60]}...' returned {raw_count} raw, kept {len([r for r in results])}"
                    )

                except Exception as e:
                    logger.warning(f"Query failed: {query[:50]} - {e}")
                    continue

        _SEARCH_CACHE[cache_key] = results
        logger.info(
            f"Live job search complete: {len(results)} valid job listings for {role}"
        )
        return results

    except Exception as e:
        logger.error(f"Live job search failed: {e}")
        return []


def search_roadmaps(skill: str, max_results: int = 8) -> List[Dict]:
    """
    Phase 1 Discovery: Search for high-authority open-source roadmaps and curricula.
    Targets GitHub Awesome lists, roadmap.sh, and university syllabi.
    """
    cache_key = f"roadmap:{skill}:{max_results}"
    if cache_key in _SEARCH_CACHE:
        return _SEARCH_CACHE[cache_key]

    try:
        from ddgs import DDGS

        results = []
        queries = [
            f'site:github.com "awesome" "{skill}" learning curriculum roadmap',
            f'site:roadmap.sh "{skill}"',
            f'"{skill}" developer roadmap 2025 2026',
            f'"{skill}" open source syllabus curriculum',
            f'"{skill}" guide comprehensive tutorial free',
        ]

        with DDGS() as ddgs:
            seen_urls = set()
            for query in queries:
                if len(results) >= max_results:
                    break
                for r in ddgs.text(query, max_results=max_results):
                    url = r.get("href", "")
                    if url and url not in seen_urls and _is_high_quality_source(url):
                        seen_urls.add(url)
                        results.append(
                            {
                                "title": r.get("title", ""),
                                "url": url,
                                "snippet": r.get("body", ""),
                                "source": "roadmap",
                                "authority": _get_source_authority(url),
                            }
                        )

        results.sort(key=lambda x: x.get("authority", 0), reverse=True)
        _SEARCH_CACHE[cache_key] = results
        return results
    except Exception as e:
        logger.error(f"Roadmap search failed for {skill}: {e}")
        return []


def _is_high_quality_source(url: str) -> bool:
    """Check if URL is from a high-authority open-source source."""
    quality_domains = [
        "github.com",
        "roadmap.sh",
        "freecodecamp.org",
        "theodinproject.com",
        "github.io",
        "mozilla.org",
        "kubernetes.io",
        "docs.python.org",
        "typescriptlang.org",
        "reactjs.org",
        "vuejs.org",
        "pytorch.org",
        "tensorflow.org",
        "scikit-learn.org",
        "pandas.pydata.org",
    ]
    url_lower = url.lower()
    return any(domain in url_lower for domain in quality_domains)


def _get_source_authority(url: str) -> int:
    """Get authority score for a source URL."""
    url_lower = url.lower()
    if "github.com" in url_lower and "awesome" in url_lower:
        return 100
    if "roadmap.sh" in url_lower:
        return 95
    if "github.com" in url_lower:
        return 80
    if any(
        doc in url_lower for doc in ["docs.", ".io/docs", "mozilla.org", "python.org"]
    ):
        return 75
    if any(site in url_lower for site in ["freecodecamp", "theodinproject"]):
        return 70
    return 50


def search_learning_resources(
    skill: str, role: str, max_results: int = 5
) -> List[Dict]:
    """Search DuckDuckGo for tutorials, courses, and articles for a skill."""
    cache_key = f"{skill}:{role}:{max_results}"
    if cache_key in _SEARCH_CACHE:
        return _SEARCH_CACHE[cache_key]

    try:
        from ddgs import DDGS

        results = []
        queries = [
            f"{skill} tutorial for beginners 2025 2026",
            f"best {skill} course free {role}",
            f"{skill} project ideas {role}",
        ]

        with DDGS() as ddgs:
            for query in queries:
                for r in ddgs.text(query, max_results=max_results):
                    results.append(
                        {
                            "title": r.get("title", ""),
                            "url": r.get("href", ""),
                            "snippet": r.get("body", ""),
                            "source": "web_search",
                        }
                    )

        _SEARCH_CACHE[cache_key] = results
        return results
    except Exception as e:
        logger.error(f"Web search failed for {skill}: {e}")
        return []


def search_youtube_embeds(skill: str, role: str, max_results: int = 3) -> List[Dict]:
    """Search DuckDuckGo for YouTube videos and return embed-ready data."""
    cache_key = f"yt:{skill}:{role}:{max_results}"
    if cache_key in _SEARCH_CACHE:
        return _SEARCH_CACHE[cache_key]

    try:
        from ddgs import DDGS

        results = []
        with DDGS() as ddgs:
            for r in ddgs.videos(f"{skill} tutorial {role}", max_results=max_results):
                url = r.get("content", "")
                title = r.get("title", "")

                video_id = None
                if "youtube.com/watch?v=" in url:
                    video_id = url.split("v=")[1].split("&")[0]
                elif "youtu.be/" in url:
                    video_id = url.split("youtu.be/")[1].split("?")[0]

                if video_id:
                    results.append(
                        {
                            "title": title,
                            "url": url,
                            "video_id": video_id,
                            "embed_url": f"https://www.youtube.com/embed/{video_id}",
                            "thumbnail": f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",
                            "channel": r.get("uploader", ""),
                            "duration": r.get("duration", ""),
                            "source": "youtube_embed",
                        }
                    )

        _SEARCH_CACHE[cache_key] = results
        return results
    except Exception as e:
        logger.error(f"YouTube embed search failed for {skill}: {e}")
        return []
