import json
import sys
import requests
from typing import List


class AllAnimeSearchError(Exception):
    """Base exception for AllAnime search errors."""


def _debug(enabled: bool, msg):
    if enabled:
        print(f"[DEBUG] {msg}", file=sys.stderr)


def search_anime(title: str, mode: str = "sub", debug: bool = False) -> List[str]:
    """
    Search AllAnime for shows matching a title.

    Args:
        title (str): Search query (required)
        mode (str): Translation type ('sub' or 'dub'), default 'sub'
        debug (bool): Enable debug logging to stderr

    Returns:
        List[str]: Formatted search results

    Raises:
        ValueError: If title is empty
        requests.RequestException: On HTTP errors
        AllAnimeSearchError: On malformed API responses
    """

    _debug(debug, "Initializing configuration")

    if not title:
        raise ValueError("missing title")

    agent = "Mozilla/5.0"
    base = "allanime.day"
    api = f"https://api.{base}/api"
    referer = "https://allmanga.to"

    _debug(debug, f"User-Agent: {agent}")
    _debug(debug, f"API endpoint: {api}")
    _debug(debug, f"Referer: {referer}")

    _debug(debug, f"Search title: {title}")
    _debug(debug, f"Translation mode: {mode}")

    search_gql = """
    query( $search: SearchInput $limit: Int $page: Int
           $translationType: VaildTranslationTypeEnumType
           $countryOrigin: VaildCountryOriginEnumType ) {
      shows(
        search: $search
        limit: $limit
        page: $page
        translationType: $translationType
        countryOrigin: $countryOrigin
      ) {
        edges {
          _id
          name
          availableEpisodes
          __typename
        }
      }
    }
    """.strip()

    _debug(debug, "GraphQL query prepared")

    variables = {
        "search": {
            "allowAdult": False,
            "allowUnknown": False,
            "query": title
        },
        "limit": 40,
        "page": 1,
        "translationType": mode,
        "countryOrigin": "ALL"
    }

    _debug(debug, "GraphQL variables:")
    _debug(debug, json.dumps(variables, indent=2))

    headers = {
        "User-Agent": agent,
        "Referer": referer
    }

    params = {
        "query": search_gql,
        "variables": json.dumps(variables, separators=(",", ":"))
    }

    _debug(debug, "Sending HTTP GET request")

    response = requests.get(api, headers=headers, params=params)

    _debug(debug, f"HTTP status code: {response.status_code}")
    _debug(debug, f"Response byte length: {len(response.content)}")

    response.raise_for_status()

    _debug(debug, "Parsing JSON response")

    data = response.json()

    try:
        edges = data["data"]["shows"]["edges"]
    except (KeyError, TypeError):
        raise AllAnimeSearchError("Unexpected API response structure")

    _debug(debug, f"Number of results returned: {len(edges)}")

    results: List[str] = []

    for i, edge in enumerate(edges, 1):
        _debug(debug, f"Processing result #{i}")
        _debug(debug, edge)

        _id = edge.get("_id", "")
        name = edge.get("name", "")
        sub_eps = edge.get("availableEpisodes", {}).get("sub", 0)

        formatted = f"{_id}\t{name} ({sub_eps} episodes)"
        results.append(formatted)

        _debug(debug, f"Formatted result: {formatted}")

    _debug(debug, "Search completed successfully")

    return results

