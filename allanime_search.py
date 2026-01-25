import json
import sys
import requests
from typing import List
import datetime

class AllAnimeSearchError(Exception):
    """Base exception for AllAnime search errors."""


def _debug(enabled: bool, msg):
    if enabled:
        print(f"[DEBUG] {msg}", file=sys.stderr)


def fetch_season_anime(
    season: str,
    year: int,
    mode: str = "sub",
    debug: bool = False
) -> List[str]:
    """
    Fetch all anime for a given season and year from AllAnime using the persisted query.

    Args:
        season (str): Season name (Winter, Spring, Summer, Fall)
        year (int): Release year
        mode (str): Translation type ('sub' or 'dub')
        debug (bool): Enable debug logging

    Returns:
        List[str]: Formatted anime entries (id, name, availableEpisodes, thumbnail)
    """

    agent = "Mozilla/5.0"
    api = "https://api.allanime.day/api"
    referer = "https://allmanga.to"

    headers = {
        "User-Agent": agent,
        "Referer": referer,
        "Accept": "*/*",
        "Origin": referer
    }

    results: List[str] = []
    page = 1
    limit = 26  # safe max

    while True:
        variables = {
            "search": {
                "season": season.capitalize(),  # "Winter", "Spring", etc.
                "year": year,
                "allowAdult": False,
                "allowUnknown": False
            },
            "limit": limit,
            "page": page,
            "translationType": mode,
            "countryOrigin": "JP"
        }

        # Persisted query required for season/year searches
        params = {
            "variables": json.dumps(variables, separators=(",", ":")),
            "extensions": json.dumps({
                "persistedQuery": {
                    "version": 1,
                    "sha256Hash": "06327bc10dd682e1ee7e07b6db9c16e9ad2fd56c1b769e47513128cd5c9fc77a"
                }
            })
        }

        _debug(debug, f"Fetching page {page} with variables: {variables}")

        response = requests.get(api, headers=headers, params=params)
        _debug(debug, f"HTTP status code: {response.status_code}")
        response.raise_for_status()

        data = response.json()
        try:
            edges = data["data"]["shows"]["edges"]
        except (KeyError, TypeError):
            raise AllAnimeSearchError("Unexpected API response structure")

        if not edges:
            _debug(debug, "No more results, stopping pagination")
            break

        for edge in edges:
            anime = {
                "id": edge.get("_id"),
                "title": edge.get("name"),
                "episodes": edge.get("availableEpisodes", {}).get("sub", 0),
                "images": {
                    "webp": {
                        "image_url": edge.get("thumbnail") or ""
                    }
                }
            }
            results.append(anime)
        page += 1

    _debug(debug, f"Total results fetched: {len(results)}")
    return results



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
          thumbnail
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
        thumbnail = edge.get("thumbnail", "")
        
        formatted = f"{_id}\t{name}\t{thumbnail}"
        results.append(formatted)

        if name == title:
            return [formatted]

        _debug(debug, f"Formatted result: {formatted}")


    _debug(debug, "Search completed successfully")
    

    return results

def fetch_recent_anime(
    mode: str = "sub",
    debug: bool = False
) -> List[str]:
    """
    Fetch all anime with episodes aired in the last 2 days from AllAnime using the persisted query.

    Args:
        season (str): Season name (Winter, Spring, Summer, Fall)
        year (int): Release year
        mode (str): Translation type ('sub' or 'dub')
        debug (bool): Enable debug logging

    Returns:
        List[str]: Formatted anime entries (id, name, availableEpisodes, thumbnail)
    """

    agent = "Mozilla/5.0"
    api = "https://api.allanime.day/api"
    referer = "https://allmanga.to"

    headers = {
        "User-Agent": agent,
        "Referer": referer,
        "Accept": "*/*",
        "Origin": referer
    }

    results: List[str] = []
    limit = 26  # safe max

    variables = {
        "search": {
            "allowAdult": False,
            "allowUnknown": False
        },
        "limit": limit,
        "page": 1,
        "translationType": mode,
        "countryOrigin": "JP"
    }

    # Persisted query required for season/year searches
    params = {
        "variables": json.dumps(variables, separators=(",", ":")),
        "extensions": json.dumps({
            "persistedQuery": {
                "version": 1,
                "sha256Hash": "06327bc10dd682e1ee7e07b6db9c16e9ad2fd56c1b769e47513128cd5c9fc77a"
            }
        })
    }

    _debug(debug, f"Fetching recents with variables: {variables}")

    response = requests.get(api, headers=headers, params=params)
    _debug(debug, f"HTTP status code: {response.status_code}")
    response.raise_for_status()

    data = response.json()
    try:
        edges = data["data"]["shows"]["edges"]
    except (KeyError, TypeError):
        raise AllAnimeSearchError("Unexpected API response structure")

    if not edges:
        _debug(debug, "No more results, stopping pagination")
        return []

    for edge in edges:
        base_date = edge.get("lastEpisodeDate", {}).get(mode, {})
        air_date = datetime.date(base_date["year"], base_date["month"]+1, base_date["date"])
        t_delta = datetime.date.today() - air_date
        if t_delta.days < 2:
            anime = {
                "id": edge.get("_id"),
                "title": edge.get("name"),
                "episodes": edge.get("availableEpisodes", {}).get("sub", 0),
                "images": {
                    "webp": {
                        "image_url": edge.get("thumbnail") or ""
                    }
                }
            }
            results.append(anime)

    _debug(debug, f"Total results fetched: {len(results)}")
    return results


