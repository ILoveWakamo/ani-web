from flask import Flask, render_template, request, jsonify, redirect, url_for
import subprocess
from datetime import datetime
import re
import time
import requests
import fetch_episode
from allanime_search import search_anime, fetch_season_anime, fetch_recent_anime

app = Flask(__name__)
app.config['VERSION'] = '1.0.4'
debug_toggle = True

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
def get_mp4_link(anime_id, episode, retries=10, delay=2):
    for attempt in range(1, retries+1):
        debug(f"\n--- Attempt {attempt} for episode {episode} ---")
        output = fetch_episode.get_episode_url(anime_id, episode)
        for entry in output:
            match = re.search(r"Mp4 >\s*(https?://\S+)|https?://\S+?\.mp4\b", entry)
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

# Player route (episode via query param)
@app.route("/play/<anime_id>")
def play(anime_id):
    episode = request.args.get("episode", default=1, type=int)
    total_episodes = request.args.get("total", default=episode, type=int)

    mp4_link = get_mp4_link(anime_id, episode)
    if not mp4_link:
        return f"Failed to fetch MP4 link for episode {episode}.", 404

    return render_template(
        "player.html",
        mp4_link=mp4_link,
        anime_id=anime_id,
        episode=episode,
        total_episodes=total_episodes
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
# ---------------------------
# ENTRY POINT
# ---------------------------
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")

