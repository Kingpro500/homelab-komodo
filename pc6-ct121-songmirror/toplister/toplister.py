"""Toplister: build world chart playlists and a "last 200 liked" playlist in Spotify.

Sources: Apple Music country charts (Top Songs, 100 per country) read through the
Apple Music web session stored by SongMirror. Writes go to Spotify through the
SongMirror sp_dc web session. Only playlists this script created (ids kept in
STATE_DIR/state.json) are ever modified.

Env:
  SONGMIRROR_DATA      SongMirror data dir (read-only), default /sm
  STATE_DIR            writable state dir, default /state
  DRY_RUN=1            compute and log, write nothing to Spotify
  RUN_ON_START=1       run once immediately
  RUN_AT=06:30         daily local run time (TZ env decides the zone)
  ONCE=1               run once and exit
"""

import collections
import datetime as dt
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

import requests

SM = Path(os.getenv("SONGMIRROR_DATA", "/sm"))
STATE_DIR = Path(os.getenv("STATE_DIR", "/state"))
os.environ.setdefault("SPOTIFY_SP_DC_FILE", str(SM / "spotify_sp_dc.private"))
os.environ.setdefault("SONGMIRROR_DATA_DIR", str(STATE_DIR))

from songmirror.engine import spotify_cookie as sc  # noqa: E402
from songmirror.engine.matching import score_candidate  # noqa: E402

DRY = os.getenv("DRY_RUN", "0") == "1"
AMP = "https://amp-api.music.apple.com/v1"

# region -> (western?, [(storefront, small?)])
REGIONS = {
    "Norden": (True, [("no", 0), ("se", 0), ("dk", 0), ("fi", 0), ("is", 1)]),
    "Vest-Europa": (True, [("gb", 0), ("de", 0), ("fr", 0), ("nl", 0), ("be", 0),
                           ("ie", 1), ("at", 0), ("ch", 0), ("lu", 1), ("mt", 1)]),
    "Sør/Øst-Europa": (True, [("it", 0), ("es", 0), ("pl", 0), ("pt", 0), ("gr", 0), ("ro", 0),
                              ("cz", 0), ("hu", 0), ("hr", 1), ("si", 1), ("ee", 1), ("lv", 1),
                              ("lt", 1), ("cy", 1), ("bg", 0), ("sk", 1)]),
    "Nord-Amerika": (True, [("us", 0), ("ca", 0)]),
    "Oseania": (True, [("au", 0), ("nz", 1), ("fj", 1), ("pg", 1)]),
    "Latin-Amerika": (False, [("mx", 0), ("br", 0), ("ar", 0), ("co", 0), ("cl", 0), ("pe", 0),
                              ("ec", 0), ("do", 0), ("gt", 0), ("cr", 1), ("pa", 1), ("uy", 1),
                              ("py", 1), ("bo", 1), ("jm", 1), ("tt", 1), ("bz", 1)]),
    "Afrika": (False, [("ng", 0), ("za", 0), ("ke", 0), ("gh", 0), ("eg", 0), ("ma", 0), ("ug", 0),
                       ("tz", 0), ("ci", 0), ("sn", 0), ("cm", 0), ("zw", 1), ("bw", 1),
                       ("na", 1), ("mu", 1)]),
    "Midtøsten": (False, [("tr", 0), ("sa", 0), ("ae", 0), ("il", 0), ("jo", 1), ("lb", 1),
                          ("kw", 1), ("qa", 1), ("bh", 1), ("om", 1)]),
    "Øst-Asia": (False, [("jp", 0), ("kr", 0), ("id", 0), ("ph", 0), ("th", 0), ("vn", 0),
                         ("my", 0), ("tw", 0), ("sg", 1), ("hk", 1), ("kh", 1), ("la", 1),
                         ("mn", 1)]),
    "Sør-Asia": (False, [("in", 0), ("pk", 0), ("lk", 1), ("np", 1)]),
}
LOCAL_LIST_FOR_REGION = {"Latin-Amerika": "latin", "Afrika": "afrika",
                         "Midtøsten": "midtosten", "Øst-Asia": "ostasia", "Sør-Asia": "sorasia"}
SMALL_PER_COUNTRY = 4
# "Små land" should be local hits, not Russian-language pop that charts across the
# Baltics/Cyprus. A track is skipped for that list if it also charts in one of these
# reference storefronts, has a Russian/Belarusian/Kazakh ISRC, or uses Cyrillic text.
RU_REFERENCE_SF = ["ru", "kz", "by"]
RU_ISRC_PREFIXES = ("RU", "BY", "KZ")
CYRILLIC = re.compile(r"[\u0400-\u04FF]")

GENRE_KEYS = {
    "latin": ["latin", "latino", "urbano", "reggaeton", "en español", "mexican", "mexicana",
              "banda", "norteño", "corrido", "sertanejo", "forró", "funk brasileiro", "mpb",
              "pagode", "axé", "samba", "salsa", "bachata", "cumbia", "vallenato", "tropical",
              "bossa", "brazil", "brasil", "tango", "merengue", "ranchera"],
    "afrika": ["africa", "afro", "amapiano", "highlife", "bongo", "gqom", "kwaito", "gengetone",
               "naija", "alté", "zouk", "kizomba", "ndombolo", "maskandi", "bikutsi"],
    "midtosten": ["arab", "khaleeji", "turk", "türk", "arabesk", "persian", "iran", "israel",
                  "mizrahi", "raï", "maghreb", "shaabi", "mahraganat", "kurdish"],
    "sorasia": ["bollywood", "indian", "tamil", "telugu", "punjabi", "hindi", "kannada",
                "malayalam", "marathi", "bengali", "bhangra", "devotional", "filmi", "pakistan",
                "qawwali", "sufi", "sinhala", "nepal", "carnatic", "hindustani"],
    "ostasia": ["k-pop", "kpop", "j-pop", "j-rock", "anime", "enka", "kayokyoku", "mandopop",
                "cantopop", "c-pop", "chinese", "thai", "luk thung", "dangdut", "indonesia",
                "malaysia", "opm", "pinoy", "v-pop", "vietnam", "mongol", "khmer", "lao",
                "japan", "korea"],
}
GLOBAL_OVERRIDES = ["afro house"]  # European dance styles that only borrow the word
EXCLUDE_KEYS = ["children", "kinder", "christmas", "holiday", "jul", "navidad", "natal",
                "noël", "weihnacht", "fitness", "spoken", "comedy", "lullab", "kids"]

LISTS = {
    "pop":       ("Verden 100 – Pop/Rock", 100,
                  "De største pop/rock-låtene på Apple Music-topplister fra hele verden. Oppdateres daglig."),
    "smaa":      ("Små land 50 – Skjulte hits", 50,
                  "Pop/rock som er stort i små land, men ikke på de store listene. Oppdateres daglig."),
    "latin":     ("Verden 50 – Latin", 50, "Topp fra Latin-Amerika og Karibia. Oppdateres daglig."),
    "afrika":    ("Verden 50 – Afrika", 50, "Topp fra Afrika. Oppdateres daglig."),
    "midtosten": ("Verden 50 – Midtøsten", 50, "Topp fra Midtøsten og Tyrkia. Oppdateres daglig."),
    "ostasia":   ("Verden 50 – Øst-Asia", 50, "K-pop, J-pop og topp fra Øst- og Sørøst-Asia. Oppdateres daglig."),
    "sorasia":   ("Verden 50 – Sør-Asia", 50, "Bollywood og topp fra India og nabolandene. Oppdateres daglig."),
    "liked":     ("Siste 200 likte", 200, "Mine 200 sist likte sanger. Oppdateres daglig."),
}
ORDER = ["pop", "smaa", "latin", "afrika", "midtosten", "ostasia", "sorasia"]


def log(*a):
    print(time.strftime("[%Y-%m-%d %H:%M:%S]"), *a, flush=True)


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\(.*?\)|\[.*?\]| - .*$|feat\..*$|ft\..*$", "", s)
    return re.sub(r"[^a-z0-9]+", "", s)


# ---------------------------------------------------------------- state
def load_state():
    p = STATE_DIR / "state.json"
    if p.exists():
        return json.loads(p.read_text())
    return {"playlists": {}, "spotify_by_isrc": {}}


def save_state(st):
    p = STATE_DIR / "state.json"
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False))
    tmp.replace(p)


# ---------------------------------------------------------------- apple
def apple_headers():
    env = {}
    for line in (SM / "profiles/profile_default_apple/app.env").read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    b = env.get("APPLE_BEARER_TOKEN", "")
    if not b.lower().startswith("bearer"):
        b = "Bearer " + b
    h = {"Authorization": b, "Origin": "https://music.apple.com"}
    if env.get("APPLE_USER_TOKEN"):
        h["Media-User-Token"] = env["APPLE_USER_TOKEN"]
    return h


def apple_chart(sf, headers):
    songs = []
    for offset in (0, 50):
        for lang in ("en-US", None):
            params = {"types": "songs", "limit": 50, "offset": offset}
            if lang:
                params["l"] = lang
            r = requests.get(f"{AMP}/catalog/{sf}/charts", params=params, headers=headers, timeout=30)
            if r.status_code == 400 and lang:
                continue
            r.raise_for_status()
            break
        data = ((r.json().get("results") or {}).get("songs") or [{}])[0].get("data") or []
        for d in data:
            a = d.get("attributes") or {}
            songs.append({"name": a.get("name", ""), "artist": a.get("artistName", ""),
                          "isrc": a.get("isrc"), "genres": a.get("genreNames") or [],
                          "duration_ms": a.get("durationInMillis")})
        time.sleep(0.3)
    return songs


def genre_class(genres):
    g = " | ".join(genres).lower()
    if any(k in g for k in EXCLUDE_KEYS):
        return "exclude"
    for k in GLOBAL_OVERRIDES:
        g = g.replace(k, "")
    for cls, keys in GENRE_KEYS.items():
        if any(k in g for k in keys):
            return cls
    return "global"


# ---------------------------------------------------------------- build
def build_world(headers):
    tracks = {}  # key -> info
    failed = []
    for region, (western, countries) in REGIONS.items():
        for sf, small in countries:
            try:
                chart = apple_chart(sf, headers)
            except Exception as e:  # noqa: BLE001
                failed.append(sf)
                log(f"  ! {sf}: {e!r}"[:200])
                continue
            for rank, s in enumerate(chart, 1):
                key = s["isrc"] or f"{norm(s['artist'])}|{norm(s['name'])}"
                t = tracks.setdefault(key, {**s, "hits": {}, "regions": collections.defaultdict(float)})
                t["hits"][sf] = rank
                t["regions"][region] += (101 - rank) / len(countries)
            log(f"  {region:<15} {sf}: {len(chart)}")
    ru_ref = set()
    for sf in RU_REFERENCE_SF:
        try:
            for s in apple_chart(sf, headers):
                ru_ref.add(s["isrc"] or f"{norm(s['artist'])}|{norm(s['name'])}")
                ru_ref.add(f"{norm(s['artist'])}|{norm(s['name'])}")
            log(f"  {'(ref)':<15} {sf}: ok")
        except Exception as e:  # noqa: BLE001
            log(f"  ! ref {sf}: {e!r}"[:200])

    def russian_language(t):
        if CYRILLIC.search(f"{t['name']} {t['artist']}"):
            return True
        if (t["isrc"] or "").upper().startswith(RU_ISRC_PREFIXES):
            return True
        return (t["isrc"] in ru_ref) or f"{norm(t['artist'])}|{norm(t['name'])}" in ru_ref

    small_set = {sf for _, (_, cs) in REGIONS.items() for sf, sm in cs if sm}
    western_regions = {r for r, (w, _) in REGIONS.items() if w}

    buckets = {k: [] for k in ORDER}
    for t in tracks.values():
        cls = genre_class(t["genres"])
        if cls == "exclude":
            continue
        regions = set(t["regions"])
        if cls == "global" and not (regions & western_regions):
            # generic genre that only charts outside the West -> that region's local list
            top_region = max((r for r in regions), key=lambda r: t["regions"][r])
            cls = LOCAL_LIST_FOR_REGION.get(top_region, "global")
        if cls == "global":
            score = sum(v for r, v in t["regions"].items() if r in western_regions)
            buckets["pop"].append((score, t))
            if all(sf in small_set for sf in t["hits"]) and not russian_language(t):
                buckets["smaa"].append((sum(101 - r for r in t["hits"].values()), t))
        else:
            buckets[cls].append((sum(t["regions"].values()), t))

    seen_isrc, seen_name, out = set(), set(), {}
    for key in ORDER:
        want = LISTS[key][1]
        picked, per_country = [], collections.Counter()
        for score, t in sorted(buckets[key], key=lambda x: -x[0]):
            nk = f"{norm(t['artist'].split(',')[0].split('&')[0])}|{norm(t['name'])}"
            if (t["isrc"] and t["isrc"] in seen_isrc) or nk in seen_name:
                continue
            if key == "smaa":
                home = min(t["hits"], key=t["hits"].get)  # country where it ranks highest
                if per_country[home] >= SMALL_PER_COUNTRY:
                    continue
                per_country[home] += 1
            picked.append(t)
            if t["isrc"]:
                seen_isrc.add(t["isrc"])
            seen_name.add(nk)
            if len(picked) >= want * 1.3:  # spare candidates for unmatched tracks
                break
        out[key] = picked
    log(f"apple: {len(tracks)} unique songs, failed storefronts: {failed or 'none'}")
    return out


# ---------------------------------------------------------------- spotify
def spotify_id(t, st):
    isrc = t.get("isrc")
    cache = st["spotify_by_isrc"]
    if isrc and isrc in cache:
        return cache[isrc]
    best, best_score = None, -1.0
    queries = ([f"isrc:{isrc}"] if isrc else []) + [f"{t['name']} {t['artist'].split(',')[0]}"]
    for q in queries:
        try:
            items = sc.search_tracks(q, limit=8)
        except Exception as e:  # noqa: BLE001
            log(f"  ! search failed {q!r}: {e!r}"[:200])
            items = []
        for it in items:
            arts = ", ".join(a.get("name", "") for a in it.get("artists", []))
            score, ok = score_candidate(t["name"], [t["artist"]], t.get("duration_ms"),
                                        it.get("name", ""), arts, it.get("duration_ms"))
            if ok and score > best_score:
                best, best_score = it.get("id"), score
        time.sleep(0.3)
        if best:
            break
    if isrc:
        cache[isrc] = best
    return best


def sync_playlist(key, ids, st):
    name, _, desc = LISTS[key]
    pid = st["playlists"].get(key)
    stamp = dt.date.today().isoformat()
    if DRY:
        log(f"  [dry] {name}: {len(ids)} tracks (playlist {'exists' if pid else 'would be created'})")
        return
    if not pid:
        pid = sc.create(name)["id"]
        st["playlists"][key] = pid
        save_state(st)
        log(f"  created {name} ({pid})")
    current = [c["uri"].rsplit(":", 1)[-1] for c in sc.contents(pid)
               if (c.get("uri") or "").startswith("spotify:track:")]
    want = list(dict.fromkeys(ids))
    remove = [i for i in set(current) if i not in set(want)]
    add = [i for i in want if i not in set(current)]
    if remove:
        sc.remove(pid, remove)
    if add:
        sc.add(pid, add)
    try:
        sc.update_details(pid, description=f"{desc} Sist oppdatert {stamp}.")
    except Exception as e:  # noqa: BLE001
        log(f"  ! description update failed: {e!r}"[:160])
    log(f"  {name}: +{len(add)} -{len(remove)} = {len(want)}")


def run():
    st = load_state()
    log("run start" + (" (DRY RUN)" if DRY else ""))
    world = build_world(apple_headers())
    for key in ORDER:
        want = LISTS[key][1]
        ids, missing = [], 0
        for t in world[key]:
            sid = spotify_id(t, st)
            if sid and sid not in ids:
                ids.append(sid)
            elif not sid:
                missing += 1
            if len(ids) >= want:
                break
        save_state(st)
        log(f"{LISTS[key][0]}: {len(ids)} matched, {missing} not on Spotify")
        for t in world[key][:5]:
            log(f"    · {t['artist']} – {t['name']}  [{', '.join(t['genres'][:2])}]  {','.join(list(t['hits'])[:6])}")
        sync_playlist(key, ids, st)
    liked = sorted(sc.favorite_tracks(), key=lambda t: t.get("added_at") or "", reverse=True)
    sync_playlist("liked", [t["id"] for t in liked[:LISTS["liked"][1]]], st)
    save_state(st)
    log("run done")


def seconds_until(hhmm):
    h, m = map(int, hhmm.split(":"))
    now = dt.datetime.now()
    nxt = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if nxt <= now:
        nxt += dt.timedelta(days=1)
    return (nxt - now).total_seconds()


def main():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if os.getenv("ONCE") == "1":
        run()
        return
    if os.getenv("RUN_ON_START", "1") == "1":
        try:
            run()
        except Exception as e:  # noqa: BLE001
            log(f"run failed: {e!r}")
    while True:
        wait = seconds_until(os.getenv("RUN_AT", "06:30"))
        log(f"next run in {wait / 3600:.1f} h")
        time.sleep(wait)
        try:
            run()
        except Exception as e:  # noqa: BLE001
            log(f"run failed: {e!r}")


if __name__ == "__main__":
    sys.exit(main())
