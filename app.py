from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
import subprocess
from datetime import datetime
import re
import sys
import time
import requests
import fetch_episode
from allanime_search import search_anime, fetch_season_anime, fetch_recent_anime, search_by_id

app = Flask(__name__)
app.config['VERSION'] = '1.0.5'
debug_toggle = False

# ------------------------------
# HELPER FUNCTIONS
# ------------------------------
def debug(msg, var=None):
    if debug_toggle == True:
        if var is not None:
            print(f"[DEBUG] {msg}: {var}", file=sys.stderr)
        else:
            print(f"[DEBUG] {msg}", file=sys.stderr)



# ---------------------------
# ANILIST AUTOCOMPLETE
# ---------------------------
ANILIST_API = "https://graphql.anilist.co"

def search_anilist(query, limit=10):
    graphql_query = """
    query ($search: String, $perPage: Int) {
      Page(perPage: $perPage) {
        media(search: $search, type: ANIME) {
          id
          title { romaji }
          episodes
        }
      }
    }
    """
    variables = {"search": query, "perPage": limit}
    try:
        response = requests.post(
            ANILIST_API,
            json={"query": graphql_query, "variables": variables},
            headers={"Content-Type": "application/json"}
        )
        data = response.json()
        results = []
        for media in data["data"]["Page"]["media"]:
            results.append({
                "title": media["title"]["romaji"],
                "episodes": media.get("episodes") or 1
            })
        return results
    except Exception as e:
        debug("AniList search error:", e)
        return []

@app.route("/autocomplete")
def autocomplete():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    return jsonify(search_anilist(q))

# ---------------------------
# MP4 FETCH HELPER
# ---------------------------
def get_mp4_link(anime_id, episode, retries=10, delay=2, mode="sub"):
    for attempt in range(1, retries+1):
        debug(f"\n--- Attempt {attempt} for episode {episode} ---")
        output = fetch_episode.get_episode_url(anime_id, episode, mode)
        for entry in output:
            match = re.search(r"Mp4 >\s*(https?://\S+)|https?://\S+?\.mp4\b|https?://tools\.fast4speed\.rsvp\S+", entry)
            if match:
                mp4_link = match.group(1) or match.group(0)
                debug(f"MP4 link found: {mp4_link}")
                return mp4_link
            debug(f"MP4 link not found, retrying in {delay}s...")
            time.sleep(delay)
    debug("Failed to fetch MP4 link after all retries.")
    return None

# ---------------------------
# ANIME SEASON HELPER
# ---------------------------

def current_anime_season() -> tuple[str, int]:
    now = datetime.now()
    month = now.month
    year = now.year

    if month in [1, 2, 3]:
        season = "Winter"
    elif month in [4, 5, 6]:
        season = "Spring"
    elif month in [7, 8, 9]:
        season = "Summer"
    else:  # 10,11,12
        season = "Fall"

    return season, year



# ---------------------------
# ROUTES
# ---------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/search", methods=["GET", "POST"])
def search():
    title = request.args.get("title") or request.form.get("title")
    mode = request.args.get("mode", "sub")
    if not title:
        return redirect(url_for("home"))

    try:
        results = search_anime(title, mode, debug=debug_toggle)
        return render_template("results.html", results=results, mode=mode, title=title)
    except Exception as e:
        return f"Error: {e}"

@app.route("/video_proxy")
def video_proxy():
    url = request.args.get("url")
    if not url:
        return "Missing URL", 400

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Referer": "https://allmanga.to"
    }

    resp = requests.get(url, headers=headers, stream=True)
    return Response(resp.iter_content(chunk_size=8192), content_type=resp.headers.get("content-type"))


# Player route (episode via query param)
@app.route("/play/<anime_id>")
def play(anime_id):
    episode = request.args.get("episode", default=1, type=int)
    total_episodes = request.args.get("total", default=episode, type=int)
    mode = request.args.get("mode", default="sub", type=str)

    mp4_link = get_mp4_link(anime_id, episode, mode=mode)
    if not mp4_link:
        mp4_link = None
        error_message = f"No video available for episode {episode}."
    else:
        error_message = None
    return render_template(
        "player.html",
        mp4_link=mp4_link,
        anime_id=anime_id,
        episode=episode,
        total_episodes=total_episodes,
        error_message=error_message
    )

@app.route("/schedule")
def schedule():

    mode = request.args.get("mode", "sub")
    # Current season
    season, year = current_anime_season()
    seasonal = fetch_season_anime(season, year, mode, debug_toggle)

    # Recent anime
    recent = fetch_recent_anime(mode, debug_toggle)


    return render_template("schedule.html", latest=recent, seasonal=seasonal, mode=mode)

@app.route("/description/<anime_id>")
def description(anime_id):
    # Mode can be optional, default to "sub"
    mode = request.args.get("mode", "sub")

    try:
        # Ideally, you have cached search results, otherwise you can search all anime
        anime_data = search_by_id(anime_id, debug=debug_toggle)  # empty query returns nothing? maybe another fetch function
        if not anime_data:
            # Fallback if not found
            anime_data = {
                "id": anime_id,
                "title": "Unknown Anime",
                "synopsis": "No description available.",
                "episodes": 0,
                "thumbnail_url": "https://www.eclosio.ong/wp-content/uploads/2018/08/default.png",
            }

        # Make sure template variable matches
        return render_template("description.html", anime=anime_data, mode=mode)

    except Exception as e:
        return f"Error fetching anime description: {e}", 500

@app.route("/watchlist")
def watchlist():
    mode = request.args.get("mode", "sub")
    return render_template("watchlist.html", mode=mode)



# ---------------------------
# ENTRY POINT
# ---------------------------
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")

