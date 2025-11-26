# backend/app/youtube_search.py
# simple in-memory cache
_YT_CACHE = {}
YT_QUOTA_EXCEEDED = False

import os
import json
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
print("YOUTUBE_API_KEY loaded?", bool(YOUTUBE_API_KEY))



def search_youtube_videos(query: str, max_results: int = 3):
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
        url = f"{base_url}?{urlencode(params)}"

        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        results = []
        for item in data.get("items", []):
            vid_id = item["id"].get("videoId")
            if not vid_id:
                continue
            snippet = item.get("snippet", {})
            results.append({
                "title": snippet.get("title", "Untitled"),
                "url": f"https://www.youtube.com/watch?v={vid_id}",
                "channel": snippet.get("channelTitle", ""),
                "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
            })
        # ✅ cache result for future calls
        _YT_CACHE[cache_key] = results
        return results
    
    except HTTPError as e:
        try:
            body = e.read().decode("utf-8")
        except Exception:
            body = "<no body>"
        print("❌ YouTube HTTPError:", e.code, e.reason)
        print("   Response body:", body)
        return []
    except URLError as e:
        print("❌ YouTube URLError:", e)
        return []
    except Exception as e:
        print("❌ YouTube search failed (other):", e)
    
    if "quotaExceeded" in  body:
        print("⚠️ YouTube API quota exceeded.")
        
        _YT_CACHE[cache_key] = []
    global YT_QUOTA_EXCEEDED
    if "quotaExceeded" in body:
        YT_QUOTA_EXCEEDED = True

    return []
