# backend/app/youtube_search.py
# simple in-memory cache
_YT_CACHE = {}
YT_QUOTA_EXCEEDED = False

import os
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
print("YOUTUBE_API_KEY loaded?", bool(YOUTUBE_API_KEY))


def search_youtube_videos(query: str, max_results: int = 3, allow_search: bool = True):
    if not allow_search:
        print("ℹ️ YouTube search disabled by allow_search=False.")
        return []

    cache_key = f"{query}:{max_results}"

    # ✅ return cached result instead of calling API again
    if cache_key in _YT_CACHE:
        return _YT_CACHE[cache_key]

    """
    Search YouTube for a query and return a small list of videos:
    [
      { "title": "...", "url": "...", "channel": "...", "thumbnail": "..." },
      ...
    ]

    If the API key is missing or something fails, returns [].
    """
    if not YOUTUBE_API_KEY:
        print("⚠️ YOUTUBE_API_KEY not set – skipping YouTube search.")
        return []

    try:
        base_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "type": "video",
            "q": query,
            "maxResults": max_results,
            "key": YOUTUBE_API_KEY,
            "safeSearch": "strict",
        }

        # Use requests with 10s timeout for better reliability
        resp = requests.get(base_url, params=params, timeout=10)

        if resp.status_code == 200:
            data = resp.json()
            results = []
            for item in data.get("items", []):
                vid_id = item["id"].get("videoId")
                if not vid_id:
                    continue
                snippet = item.get("snippet", {})
                results.append(
                    {
                        "title": snippet.get("title", "Untitled"),
                        "url": f"https://www.youtube.com/watch?v={vid_id}",
                        "channel": snippet.get("channelTitle", ""),
                        "thumbnail": snippet.get("thumbnails", {})
                        .get("medium", {})
                        .get("url", ""),
                    }
                )
            # ✅ cache result for future calls
            _YT_CACHE[cache_key] = results
            return results

        else:
            try:
                error_body = resp.json()
                error_msg = error_body.get("error", {}).get("message", resp.text)
            except:
                error_msg = resp.text[:200]

            print(f"❌ YouTube API Error ({resp.status_code}): {error_msg}")

            if resp.status_code == 403 and "quotaExceeded" in str(error_msg):
                print("⚠️ YouTube API quota exceeded.")
                global YT_QUOTA_EXCEEDED
                YT_QUOTA_EXCEEDED = True
                _YT_CACHE[cache_key] = []

            return []

    except requests.exceptions.Timeout:
        print("❌ YouTube Request Timeout (10s)")
        return []
    except requests.exceptions.RequestException as e:
        print(f"❌ YouTube search failed: {e}")
        return []
    except Exception as e:
        print(f"❌ YouTube search failed (other): {e}")
        return []
