# backend/app/youtube_search.py

import os
import json
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


def search_youtube_videos(query: str, max_results: int = 3):
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

        return results
    except Exception as e:
        print("❌ YouTube search failed:", e)
        return []
