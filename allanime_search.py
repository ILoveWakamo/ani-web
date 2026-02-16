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
) -> List[dict]:
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
    api = "https://api.allanime.day/api"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://allanime.to/",
        "Origin": "https://allanime.to",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    graphql_query = """
    query GetSeasonalShows(
        $search: SearchInput
        $limit: Int
        $page: Int
        $translationType: VaildTranslationTypeEnumType
        $countryOrigin: VaildCountryOriginEnumType
    ) {
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
                description
                thumbnail
                availableEpisodes
            }
        }
    }
    """

    results: List[dict] = []
    page = 1
    limit = 26

    while True:
        variables = {
            "search": {
                "season": season.capitalize(),
                "year": year,
                "allowAdult": False,
                "allowUnknown": False
            },
            "limit": limit,
            "page": page,
            "translationType": mode,
            "countryOrigin": "JP"
        }

        payload = {
            "query": graphql_query,
            "variables": variables
        }

        if debug:
            print(f"Fetching page {page}")
            print(json.dumps(payload, indent=2))

        response = requests.post(api, headers=headers, json=payload)

        if debug:
            print(response.text)

        response.raise_for_status()
        data = response.json()

        shows = data.get("data", {}).get("shows")
        if not shows or not shows.get("edges"):
            break

        for edge in shows["edges"]:
            available = edge.get("availableEpisodes") or {}

            has_dub = available.get("dub", 0) > 0
            sub_eps = available.get("sub", 0)

            anime = {
                "id": edge.get("_id"),
                "title": edge.get("name"),
                "episodes": sub_eps,
                "images": {
                    "webp": {
                        "image_url": edge.get("thumbnail") or
                        "https://www.eclosio.ong/wp-content/uploads/2018/08/default.png"
                    }
                },
                "synopsis": edge.get("description") or "No description found.",
                "has_dub": has_dub
            }

            results.append(anime)

        page += 1

    if debug:
        print(f"Total results fetched: {len(results)}")

    return results



def search_anime(title: str, mode: str = "sub", debug: bool = False) -> List[dict]:
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
    for edge in edges:
        has_dub = edge.get("availableEpisodes", {}).get("dub", 0) > 0
        anime = {
            "id": edge.get("_id", ""),
            "title": edge.get("name", ""),
            "episodes": edge.get("availableEpisodes", {}).get(mode, 0),
            "images": {
                "webp": {
                    "image_url": edge.get("thumbnail") or "https://www.eclosio.ong/wp-content/uploads/2018/08/default.png"
                }
            },
            "synopsis": edge.get("description") or "No description found.",
            "has_dub": has_dub
        }
        
        results.append(anime)

    _debug(debug, "Search completed successfully")
    

    return results

def fetch_recent_anime(
    mode: str = "sub",
    debug: bool = False
) -> List[dict]:
    """
    Fetch all anime with episodes aired in the last 2 days from AllAnime using the persisted query.

    Args:
        mode (str): Translation type ('sub' or 'dub')
        debug (bool): Enable debug logging

    Returns:
        List[str]: Formatted anime entries (id, name, availableEpisodes, thumbnail)
    """
    api = "https://api.allanime.day/api"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://allanime.to/",
        "Origin": "https://allanime.to",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    graphql_query = """
    query GetRecentShows(
        $search: SearchInput
        $limit: Int
        $page: Int
        $translationType: VaildTranslationTypeEnumType
        $countryOrigin: VaildCountryOriginEnumType
    ) {
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
                description
                thumbnail
                availableEpisodes
                lastEpisodeDate
            }
        }
    }
    """

    variables = {
        "search": {
            "allowAdult": False,
            "allowUnknown": False
        },
        "limit": 26,
        "page": 1,
        "translationType": mode,
        "countryOrigin": "JP"
    }

    payload = {
        "query": graphql_query,
        "variables": variables
    }

    if debug:
        print(json.dumps(payload, indent=2))

    response = requests.post(api, headers=headers, json=payload)

    if debug:
        print(response.text)

    response.raise_for_status()
    data = response.json()

    shows = data.get("data", {}).get("shows")
    if not shows or not shows.get("edges"):
        return []

    results: List[dict] = []

    for edge in shows["edges"]:

        # lastEpisodeDate is now a generic object
        last_date_obj = (edge.get("lastEpisodeDate") or {}).get(mode)

        if not last_date_obj:
            continue

        try:
            air_date = datetime.date(
                last_date_obj["year"],
                last_date_obj["month"] + 1,  # still zero-indexed
                last_date_obj["date"]
            )
        except Exception:
            continue

        if (datetime.date.today() - air_date).days < 2:

            available = edge.get("availableEpisodes") or {}

            anime = {
                "id": edge.get("_id"),
                "title": edge.get("name"),
                "episodes": available.get("sub", 0),
                "images": {
                    "webp": {
                        "image_url": edge.get("thumbnail")
                        or "https://www.eclosio.ong/wp-content/uploads/2018/08/default.png"
                    }
                },
                "synopsis": edge.get("description") or "No description found."
            }

            results.append(anime)

    if debug:
        print(f"Total recent results: {len(results)}")

    return results

def search_by_id(anime_id: str, debug: bool = False) -> dict:
    if not anime_id:
        raise ValueError("missing anime id")

    api = "https://api.allanime.day/api"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://allanime.to/",
        "Origin": "https://allanime.to",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    graphql_query = """
    query GetShowById($_id: String!) {
        show(_id: $_id) {
            _id
            name
            description
            thumbnail
            availableEpisodes
        }
    }
    """

    payload = {
        "query": graphql_query,
        "variables": {
            "_id": anime_id
        }
    }

    if debug:
        print(json.dumps(payload, indent=2))

    response = requests.post(api, headers=headers, json=payload)

    if debug:
        print(response.text)

    response.raise_for_status()
    data = response.json()

    show = data.get("data", {}).get("show")
    if not show:
        raise AllAnimeSearchError("Anime not found")

    available = show.get("availableEpisodes") or {}
    has_dub = available.get("dub", 0) > 0

    return {
        "id": show["_id"],
        "title": show.get("name"),
        "thumbnail_url": show.get("thumbnail"),
        "synopsis": show.get("description") or "No synopsis available.",
        "description": show.get("description") or "No description available.",
        "episodes": available.get("sub", 0),
        "has_dub": has_dub
    }



