import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

def fetch_tavily_sources(query: str, max_results: int = 5, search_depth: str = "advanced") -> list:
    """Fetches web snippets using the Tavily API."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY is not set in environment variables.")

    client = TavilyClient(api_key=api_key)
    response = client.search(query=query, search_depth=search_depth, max_results=max_results)

    return [
        {
            "url": res.get("url"),
            "title": res.get("title"),
            "snippet": res.get("content"),
            "credibility_score": 0.0,
        }
        for res in response.get("results", [])
    ]

