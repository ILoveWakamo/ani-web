#!/usr/bin/env python3
import argparse
import os
import re
import requests
import sys
import tempfile
import json


# ------------------------------
# CONFIGURATION
# ------------------------------
agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
allanime_refr = "https://allmanga.to"
allanime_base = "allanime.day"
allanime_api = f"https://api.{allanime_base}"
mode = "sub"
debug_toggle = False

# ------------------------------
# HELPER FUNCTIONS
# ------------------------------
def die(msg):
    print(f"\033[1;31m{msg}\033[0m", file=sys.stderr)
    sys.exit(1)

def debug(msg, var=None):
    if debug_toggle == True:
        if var is not None:
            print(f"[DEBUG] {msg}: {var}", file=sys.stderr)
        else:
            print(f"[DEBUG] {msg}", file=sys.stderr)

# ------------------------------
# HEX TRANSLATION
# ------------------------------
HEX_TRANSLATION = {
    "79": "A","7a": "B","7b": "C","7c": "D","7d": "E","7e": "F","7f": "G",
    "70": "H","71": "I","72": "J","73": "K","74": "L","75": "M","76": "N",
    "77": "O","68": "P","69": "Q","6a": "R","6b": "S","6c": "T","6d": "U",
    "6e": "V","6f": "W","60": "X","61": "Y","62": "Z",
    "59": "a","5a": "b","5b": "c","5c": "d","5d": "e","5e": "f","5f": "g",
    "50": "h","51": "i","52": "j","53": "k","54": "l","55": "m","56": "n",
    "57": "o","48": "p","49": "q","4a": "r","4b": "s","4c": "t","4d": "u",
    "4e": "v","4f": "w","40": "x","41": "y","42": "z",
    "08": "0","09": "1","0a": "2","0b": "3","0c": "4","0d": "5","0e": "6","0f": "7",
    "00": "8","01": "9",
    "15": "-","16": ".","67": "_","46": "~","02": ":","17": "/","07": "?",
    "1b": "#","63": "[","65": "]","78": "@","19": "!","1c": "$","1e": "&",
    "10": "(","11": ")","12": "*","13": "+","14": ",","03": ";","05": "=","1d": "%"
}

def decode_provider(raw_id):
    decoded = "".join(HEX_TRANSLATION.get(raw_id[i:i+2], raw_id[i:i+2])
                      for i in range(0, len(raw_id), 2))
    return decoded.replace("/clock", "/clock.json")

# ------------------------------
# STEP 1: EPISODE LIST
# ------------------------------
def episodes_list(show_id):
    gql = 'query ($showId: String!) { show( _id: $showId ) { _id availableEpisodesDetail }}'
    params = {"variables": f'{{"showId":"{show_id}"}}', "query": gql}
    resp = requests.get(f"{allanime_api}/api", headers={"User-Agent": agent, "Referer": allanime_refr}, params=params).text
    debug("Raw episode list response (first 500 chars)", resp[:500])

    match = re.search(rf'{mode}":\[(.*?)\]', resp)
    if not match:
        debug("No episode list found in GraphQL response")
        return []
    eps_list_str = match.group(1)
    eps = [int(x.replace('"','')) for x in eps_list_str.split(',') if x.strip()]
    eps.sort()
    debug("Episode list", eps)
    return eps

# ------------------------------
# STEP 2: EXTRACT PROVIDERS
# ------------------------------
def extract_providers(resp):
    debug("Raw GraphQL response for providers (first 500 chars)", resp[:500])
    # mimic Bash tr '{}' '\n'
    lines = re.sub(r'[{}]', '\n', resp)
    lines = lines.replace("\\u002F","/").replace("\\","")
    debug("After tr/sed processing (first 500 chars)", lines[:500])
    matches = re.findall(r'sourceUrl":"--([^"]+)".*?sourceName":"([^"]+)"', lines)
    debug("Regex matches for providers", matches)
    providers = [(name, raw_id) for raw_id, name in matches]
    debug("Extracted providers", providers)
    return providers

# ------------------------------
# STEP 3: FETCH PROVIDER LINKS
# ------------------------------

def get_links(provider_name, provider_id):
    # provider_id can be absolute (https://...) or relative (/path)
    if provider_id.startswith("http"):
        url = provider_id
    else:
        url = f"https://{allanime_base}{provider_id}"

    debug(f"Fetching provider URL", url)
    response = requests.get(url, headers={"User-Agent": agent, "Referer": allanime_refr}).text
    debug(f"Raw response for {provider_name} (first 500 chars)", response[:1000])

    episode_links = []
    try:
        json_resp = json.loads(response)  # no need for str()
        first_link = json_resp["links"][0]["link"]
        if json_resp["links"][0]["resolutionStr"] == "Mp4":
            res = "Mp4"
            episode_links.append(f"{res} >{first_link}")
        elif json_resp["links"][0]["resolutionStr"] == "Hls":
            response = requests.get(first_link, headers={"User-Agent": agent})
            playlist_text = response.text
            resolutions = {}
            lines = playlist_text.splitlines()
            for i, line in enumerate(lines):
                if line.startswith("#EXT-X-STREAM-INF:"):
                    # Extract resolution from the tag
                    res_part = [x for x in line.split(",") if x.startswith("RESOLUTION=")][0]
                    res = res_part.split("=")[1].split("x")[1]
                    # The URL is on the next line
                    media_url = lines[i + 1]
                    resolutions[res] = media_url
            for res, media_url in resolutions.items():
                episode_links.append(f"{res} >{media_url.rsplit('/', 1)[0].replace('repackager.wixmp.com/', '')}")
    except json.JSONDecodeError:
        debug(f"No valid JSON returned")
    except KeyError:
        debug(f"JSON structure is not as expected")

    debug(f"Episode links before processing", episode_links)
    return episode_links


# ------------------------------
# STEP 4: SELECT QUALITY
# ------------------------------
def select_quality(links, quality="best"):
    debug("Links before quality selection", links)
    if not links:
        return None
    if quality == "best":
        result = links[0]
    elif quality == "worst":
        numeric = [l for l in links if re.match(r'^\d+', l)]
        result = numeric[-1] if numeric else links[0]
    else:
        for l in links:
            if l.startswith(quality):
                result = l
                break
        else:
            result = links[0]
    debug("Selected link after quality filter", result)
    return result

# ------------------------------
# STEP 5: GET EPISODE URL
# ------------------------------

def get_episode_url(show_id, ep_no):
    gql = """
    query ($showId: String!, $translationType: VaildTranslationTypeEnumType!, $episodeString: String!) {
        episode(showId: $showId translationType: $translationType episodeString: $episodeString) {
            episodeString sourceUrls
        }
    }"""
    variables = {"showId": show_id, "translationType": mode, "episodeString": str(ep_no)}
    
    resp = requests.get(
        f"{allanime_api}/api",
        headers={"User-Agent": agent, "Referer": allanime_refr},
        params={"variables": json.dumps(variables), "query": gql}
    ).text
    debug("Raw GraphQL episode response (first 500 chars)", resp[:500])

    providers = extract_providers(resp)
    if not providers:
        die("No providers found for this episode!")

    all_links = []
    for name, raw_id in providers:
        if(name == "Yt-mp4"):
            continue
        pid = decode_provider(raw_id)
        debug("Decoded provider URL", pid)
        links = get_links(name, pid)
        all_links.extend(links)

    all_links.sort(reverse=True)
    debug("All collected links", all_links)
    return all_links

