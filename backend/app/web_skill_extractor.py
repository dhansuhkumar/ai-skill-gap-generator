"""
Web-Search Skill Extractor - Fast role-to-skills via DuckDuckGo.

Replaces HuggingFace dataset downloads with targeted web searches.
Extracts skills from job listings on LinkedIn, Indeed, and company career pages.
"""

import logging
import re
from typing import List, Dict, Set, Tuple
from collections import Counter
import hashlib
import json

logger = logging.getLogger(__name__)

_TECH_SKILLS_VOCAB: Dict[str, List[str]] = {
    "Python": [
        "python",
        "pytorch",
        "pandas",
        "numpy",
        "django",
        "flask",
        "fastapi",
        "scikit-learn",
        "jupyter",
    ],
    "JavaScript": [
        "javascript",
        "js",
        "node.js",
        "nodejs",
        "express",
        "express.js",
        "next.js",
        "nextjs",
        "nuxt",
    ],
    "TypeScript": ["typescript", "ts", "tsx", "jsx"],
    "React": [
        "react",
        "reactjs",
        "react.js",
        "redux",
        "react redux",
        "next.js",
        "remix",
    ],
    "Vue.js": ["vue", "vuejs", "vue.js", "nuxt", "nuxtjs", "pinia", "vuex"],
    "Angular": ["angular", "angularjs", "rxjs", "ngrx"],
    "Java": [
        "java",
        "spring",
        "springboot",
        "spring boot",
        "maven",
        "gradle",
        "hibernate",
        "junit",
    ],
    "C++": ["c++", "cpp", "stl"],
    "C#": ["c#", "csharp", ".net", ".net core", "asp.net", "entity framework"],
    "Go": ["go", "golang"],
    "Rust": ["rust"],
    "Swift": ["swift", "swiftui"],
    "Kotlin": ["kotlin"],
    "PHP": ["php", "laravel", "codeigniter", "symfony", "wordpress"],
    "Ruby": ["ruby", "ruby on rails", "rails", "sinatra"],
    "Scala": ["scala", "apache scala", "play framework", "spark"],
    "SQL": [
        "sql",
        "mysql",
        "postgresql",
        "postgres",
        "mongodb",
        "redis",
        "sqlite",
        "mariadb",
        "cassandra",
        "dynamodb",
        "elasticsearch",
    ],
    "NoSQL": ["mongodb", "cassandra", "dynamodb", "couchbase", "redis", "memcached"],
    "AWS": [
        "aws",
        "amazon web services",
        "ec2",
        "s3",
        "lambda",
        "ecs",
        "eks",
        "rds",
        "cloudformation",
        "sam",
        "boto3",
    ],
    "Azure": ["azure", "microsoft azure", "azure devops", "az-900"],
    "GCP": [
        "gcp",
        "google cloud",
        "google cloud platform",
        "bigquery",
        "cloud functions",
        "gke",
    ],
    "Docker": [
        "docker",
        "container",
        "containerization",
        "dockerfile",
        "docker-compose",
        "containerd",
    ],
    "Kubernetes": [
        "kubernetes",
        "k8s",
        "k8",
        "kubectl",
        "helm",
        "istio",
        "service mesh",
    ],
    "Git": [
        "git",
        "github",
        "gitlab",
        "bitbucket",
        "version control",
        "gitlab ci",
        "github actions",
    ],
    "CI/CD": [
        "ci/cd",
        "jenkins",
        "github actions",
        "gitlab ci",
        "circleci",
        "travis ci",
        "bitbucket pipelines",
        "cicd",
        "azure devops",
    ],
    "Linux": ["linux", "unix", "bash", "shell scripting", "ubuntu", "centos", "debian"],
    "Machine Learning": [
        "machine learning",
        "ml",
        "deep learning",
        "ai",
        "neural networks",
        "tensorflow",
        "pytorch",
        "scikit-learn",
        "mlops",
    ],
    "Data Science": [
        "data science",
        "data analysis",
        "data analytics",
        "statistics",
        "pandas",
        "numpy",
        "jupyter",
        "r",
        "tableau",
        "power bi",
    ],
    "TensorFlow": ["tensorflow", "tf", "keras"],
    "PyTorch": ["pytorch"],
    "NLP": [
        "nlp",
        "natural language processing",
        "text analytics",
        "spacy",
        "transformers",
        "hugging face",
        "bert",
        "gpt",
        "llm",
    ],
    "Computer Vision": [
        "computer vision",
        "opencv",
        "image processing",
        "yolo",
        "object detection",
        "cnn",
    ],
    "DevOps": [
        "devops",
        "sre",
        "site reliability",
        "infrastructure",
        "terraform",
        "ansible",
        "puppet",
        "chef",
    ],
    "Cloud": ["cloud computing", "saas", "paas", "iaas", "serverless", "microservices"],
    "API": [
        "api",
        "rest",
        "restful",
        "graphql",
        "grpc",
        "webhook",
        "swagger",
        "openapi",
        "postman",
    ],
    "Microservices": [
        "microservices",
        "microservice",
        "service mesh",
        "api gateway",
        "kong",
        "nginx",
    ],
    "Security": [
        "security",
        "cybersecurity",
        "penetration testing",
        "owasp",
        "oauth",
        "jwt",
        "ssl",
        "tls",
        "encryption",
    ],
    "Testing": [
        "testing",
        "unit testing",
        "integration testing",
        "e2e testing",
        "selenium",
        "jest",
        "pytest",
        "junit",
        "testng",
        "mocha",
        "cypress",
        "playwright",
    ],
    "Agile": ["agile", "scrum", "kanban", "jira", "sprint", "standup", "retrospective"],
    "HTML/CSS": [
        "html",
        "css",
        "html5",
        "css3",
        "sass",
        "scss",
        "less",
        "tailwind",
        "bootstrap",
        "material ui",
        "mui",
        "styled-components",
        "responsive design",
    ],
    "Mobile": [
        "mobile development",
        "react native",
        "flutter",
        "ios",
        "android",
        "swift",
        "kotlin",
        "xamarin",
    ],
    "Blockchain": [
        "blockchain",
        "ethereum",
        "solidity",
        "web3",
        "smart contracts",
        "defi",
        "nft",
        "hyperledger",
    ],
    "Data Engineering": [
        "data engineering",
        "etl",
        "data pipeline",
        "airflow",
        "apache spark",
        "kafka",
        "flink",
        "snowflake",
        "databricks",
        "dbt",
    ],
    "Excel": ["excel", "spreadsheet", "vlookup", "pivot table", "vba"],
    "Tableau": ["tableau"],
    "Power BI": ["power bi", "powerbi"],
    "Spark": ["spark", "pyspark", "apache spark", "databricks"],
    "Hadoop": ["hadoop", "hdfs", "mapreduce", "hive", "hbase", "pig"],
    "Kafka": ["kafka", "confluent", "kafka streams", "apache kafka"],
    "PostgreSQL": ["postgresql", "postgres"],
    "MySQL": ["mysql", "mariadb"],
    "MongoDB": ["mongodb", "mongo"],
    "GraphQL": ["graphql"],
    "REST API": ["rest", "restful api", "rest api"],
    "Web": ["html", "css", "javascript", "dom", "responsive", "accessibility", "seo"],
    "Frontend": [
        "frontend",
        "front-end",
        "ui",
        "ux",
        "react",
        "vue",
        "angular",
        "svelte",
    ],
    "Backend": [
        "backend",
        "back-end",
        "server",
        "api",
        "database",
        "node",
        "python",
        "java",
    ],
    "Full Stack": ["full stack", "full-stack", "mern", "mean", "lamp", "jamstack"],
    "Firebase": ["firebase", "firestore", "realtime database"],
    "Supabase": ["supabase"],
    "Three.js": ["three.js", "threejs", "webgl", "3d graphics"],
    "WebRTC": ["webrtc", "real-time communication", "video calling"],
    "Webpack": ["webpack", "vite", "esbuild", "rollup"],
    "Babel": ["babel"],
    "npm": ["npm", "yarn", "pnpm", "package manager"],
    "Jest": ["jest", "testing library"],
    "Cypress": ["cypress", "e2e testing"],
    "Playwright": ["playwright"],
    "Figma": ["figma", "ui design", "design tool"],
    "Photoshop": ["photoshop", "image editing"],
    "Webpack": ["webpack"],
    "Vite": ["vite", "build tool"],
    "Redis": ["redis", "caching", "session store"],
    "Elasticsearch": ["elasticsearch", "elk stack", "elastic"],
    "Splunk": ["splunk", "log analysis"],
    "Prometheus": ["prometheus", "monitoring", "metrics"],
    "Grafana": ["grafana", "dashboards", "visualization"],
    "Datadog": ["datadog", "apm"],
    "New Relic": ["new relic", "application monitoring"],
    "Sentry": ["sentry", "error tracking"],
    "Jenkins": ["jenkins", "ci/cd"],
    "TeamCity": ["teamcity"],
    "CircleCI": ["circleci"],
    "Travis CI": ["travis ci"],
    "GitHub Actions": ["github actions", "gh actions"],
    "GitLab CI": ["gitlab ci"],
    "Databricks": ["databricks", "lakehouse"],
    "Snowflake": ["snowflake", "data warehouse"],
    "dbt": ["dbt", "data build tool"],
    "Airflow": ["airflow", "apache airflow"],
    "Prefect": ["prefect"],
    "Dagster": ["dagster"],
    "Terraform": ["terraform", "infrastructure as code", "iac"],
    "Pulumi": ["pulumi"],
    "Ansible": ["ansible", "configuration management"],
    "Chef": ["chef"],
    "Puppet": ["puppet"],
    "Vagrant": ["vagrant", "vm"],
    "VirtualBox": ["virtualbox"],
    "VMware": ["vmware"],
    "OpenStack": ["openstack", "open stack"],
    "Networking": [
        "networking",
        "tcp/ip",
        "dns",
        "http",
        "https",
        "ssl",
        "tls",
        "vpn",
        "负载均衡",
        "load balancer",
    ],
    "System Design": [
        "system design",
        "architecture",
        "scalability",
        "microservices",
        "distributed systems",
    ],
    "Algorithms": [
        "algorithms",
        "data structures",
        "complexity",
        "big-o",
        "sorting",
        "searching",
    ],
    "Design Patterns": [
        "design patterns",
        "singleton",
        "factory",
        "observer",
        "mvc",
        "mvvm",
    ],
    "OOP": [
        "oop",
        "object oriented",
        "classes",
        "inheritance",
        "polymorphism",
        "encapsulation",
    ],
    "Functional Programming": [
        "functional programming",
        "fp",
        "immutable",
        "pure functions",
        "map reduce",
    ],
    "Leadership": ["leadership", "mentoring", "team lead", "technical lead"],
    "Communication": [
        "communication",
        "presentation",
        "documentation",
        "technical writing",
    ],
}

_SKILL_CACHE: Dict[str, Tuple[List[str], int]] = {}
_SEARCH_CACHE: Dict[str, List[Dict]] = {}


def get_tech_skills_vocab() -> Dict[str, List[str]]:
    """Return the shared tech skills vocabulary."""
    return _TECH_SKILLS_VOCAB


def _extract_skills_from_text(text: str) -> List[str]:
    """Extract skills from text using vocabulary matching."""
    text_lower = text.lower()
    found_skills = []

    for primary_skill, variations in _TECH_SKILLS_VOCAB.items():
        for variant in variations:
            if variant in text_lower:
                if primary_skill not in found_skills:
                    found_skills.append(primary_skill)
                break

    return found_skills


def _count_skill_frequency(snippets: List[str]) -> Dict[str, int]:
    """Count skill frequency across multiple text snippets."""
    skill_counts = Counter()

    for snippet in snippets:
        skills = _extract_skills_from_text(snippet)
        for skill in skills:
            skill_counts[skill] += 1

    return dict(skill_counts)


def search_role_skills(role: str, top_n: int = 15) -> Tuple[List[str], int]:
    """
    Extract skills for a role using LLM (primary) or predefined fallback.

    Args:
        role: Target job role (e.g., "Python Developer")
        top_n: Number of top skills to return

    Returns:
        Tuple of (top_skills_list, sources_analyzed)
    """
    cache_key = f"role_skills:{role.lower().strip()}:{top_n}"
    if cache_key in _SKILL_CACHE:
        logger.info(f"Using cached skills for role: {role}")
        return _SKILL_CACHE[cache_key]

    logger.info(f"Extracting skills for role: {role} via LLM")

    try:
        from .llm_skill_extractor import extract_skills_with_llm

        skills, source = extract_skills_with_llm(role, top_n)
        if skills:
            logger.info(f"LLM extracted {len(skills)} skills for {role}")
            _SKILL_CACHE[cache_key] = (skills, 1)
            return (skills, 1)
    except Exception as e:
        logger.warning(f"LLM extraction failed: {e}, using fallback")

    logger.warning(f"Using predefined fallback skills for {role}")
    fallback_skills = _get_role_fallback_skills(role)
    _SKILL_CACHE[cache_key] = (fallback_skills, 0)
    return (fallback_skills, 0)


def _get_role_fallback_skills(role: str) -> List[str]:
    """Get fallback skills based on role keywords."""
    role_lower = role.lower()

    role_skill_map = {
        "backend": [
            "Python",
            "Java",
            "Node.js",
            "SQL",
            "REST API",
            "Git",
            "Linux",
            "Docker",
        ],
        "frontend": [
            "JavaScript",
            "React",
            "HTML",
            "CSS",
            "TypeScript",
            "Git",
            "REST API",
        ],
        "full stack": [
            "JavaScript",
            "React",
            "Python",
            "SQL",
            "REST API",
            "Git",
            "Docker",
        ],
        "python": ["Python", "Django", "Flask", "SQL", "Git", "REST API", "Docker"],
        "java": ["Java", "Spring", "SQL", "Git", "REST API", "Docker", "Maven"],
        "javascript": [
            "JavaScript",
            "Node.js",
            "React",
            "TypeScript",
            "Git",
            "REST API",
        ],
        "react": [
            "React",
            "JavaScript",
            "TypeScript",
            "HTML",
            "CSS",
            "REST API",
            "Git",
        ],
        "machine learning": [
            "Python",
            "Machine Learning",
            "TensorFlow",
            "PyTorch",
            "SQL",
            "Data Science",
        ],
        "ml": [
            "Python",
            "Machine Learning",
            "TensorFlow",
            "PyTorch",
            "SQL",
            "Data Science",
        ],
        "data science": [
            "Python",
            "Data Science",
            "SQL",
            "Machine Learning",
            "Pandas",
            "Statistics",
        ],
        "devops": ["Docker", "Kubernetes", "AWS", "Linux", "CI/CD", "Terraform", "Git"],
        "cloud": [
            "AWS",
            "Azure",
            "Docker",
            "Kubernetes",
            "Linux",
            "Terraform",
            "CI/CD",
        ],
        "web developer": ["JavaScript", "React", "HTML", "CSS", "Python", "SQL", "Git"],
        "software engineer": [
            "Python",
            "Java",
            "SQL",
            "Git",
            "Docker",
            "REST API",
            "Data Structures",
        ],
        "software developer": [
            "Python",
            "Java",
            "SQL",
            "Git",
            "Docker",
            "REST API",
            "Data Structures",
        ],
        "backend engineer": [
            "Python",
            "Java",
            "SQL",
            "REST API",
            "Git",
            "Linux",
            "Docker",
            "Redis",
        ],
        "frontend engineer": [
            "JavaScript",
            "React",
            "TypeScript",
            "CSS",
            "HTML",
            "Git",
            "REST API",
        ],
        "full stack engineer": [
            "JavaScript",
            "React",
            "Python",
            "SQL",
            "REST API",
            "Docker",
            "Git",
        ],
        "data engineer": [
            "Python",
            "SQL",
            "Spark",
            "Airflow",
            "Kafka",
            "AWS",
            "Data Engineering",
        ],
        "security": [
            "Security",
            "Cybersecurity",
            "Python",
            "Network Security",
            "Penetration Testing",
        ],
        "mobile": ["React Native", "Flutter", "iOS", "Android", "JavaScript", "API"],
    }

    for key, skills in role_skill_map.items():
        if key in role_lower:
            return skills

    return ["Python", "JavaScript", "SQL", "Git", "REST API", "Docker", "Linux"]


def get_role_skills_from_job_listings(
    role: str, max_results: int = 20
) -> Dict[str, int]:
    """
    Get skill frequency from live job listings for a role.

    Returns:
        Dict mapping skill name to frequency count
    """
    cache_key = f"job_skills:{role.lower().strip()}:{max_results}"
    if cache_key in _SEARCH_CACHE:
        return _SEARCH_CACHE[cache_key]

    try:
        from ddgs import DDGS

        results = []
        seen = set()

        queries = [
            f'"{role}" job listing requirements skills',
            f'"{role}" position qualifications tech stack',
            f'"{role}" career opportunities skills needed',
        ]

        with DDGS() as ddgs:
            for query in queries:
                if len(results) >= max_results:
                    break

                for r in ddgs.text(query, max_results=max_results):
                    url = r.get("href", "")
                    body = r.get("body", "")

                    if url in seen or len(body) < 100:
                        continue

                    seen.add(url)
                    results.append(body)

        skill_freq = _count_skill_frequency(results)
        _SEARCH_CACHE[cache_key] = skill_freq
        return skill_freq

    except Exception as e:
        logger.error(f"Job listing search failed for {role}: {e}")
        return {}


def extract_skills_from_snippet(
    snippet: str, known_skills: List[str] = None
) -> List[str]:
    """
    Extract skills from a job snippet, combining known user skills with vocabulary.

    Args:
        snippet: Job description text
        known_skills: List of skills the user already has (to match against)

    Returns:
        List of extracted skill names
    """
    snippet_lower = snippet.lower()
    found = []

    if known_skills:
        for skill in known_skills:
            if skill.lower() in snippet_lower:
                found.append(skill)

    vocab_skills = _extract_skills_from_text(snippet)
    for skill in vocab_skills:
        if skill not in found:
            found.append(skill)

    return found[:10]


def clear_skill_cache():
    """Clear all skill-related caches."""
    global _SKILL_CACHE, _SEARCH_CACHE
    _SKILL_CACHE.clear()
    _SEARCH_CACHE.clear()
    logger.info("Skill caches cleared")
