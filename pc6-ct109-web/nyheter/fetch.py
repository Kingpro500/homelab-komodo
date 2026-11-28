"""Nyhetsoversikt: henter toppsakene per land og oversetter overskrifter til norsk.

Leser feeds.json, skriver /data/data.json (lest av nyheter/index.html via nginx).
Kun Python-standardbiblioteket. Kjører i en løkke hvert INTERVAL sekund.
"""
import email.utils
import html
import json
import os
import re
import time
import urllib.parse
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

APP = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("DATA_DIR", "/data")
INTERVAL = int(os.environ.get("INTERVAL", "1800"))
PER_COUNTRY = int(os.environ.get("PER_COUNTRY", "10"))
PER_PAPER = int(os.environ.get("PER_PAPER", "3"))
TARGET = "no"
NO_TRANSLATE = {"no", "nb", "nn", "sv", "da", "en"}
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131 Safari/537.36"

CACHE_FILE = os.path.join(DATA, "translations.json")
cache = {}


def log(*a):
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), *a, flush=True)


_last_google = 0.0


def get(url, timeout=20):
    """HTTP GET. Kall til Google News strupes (min. 2 s mellomrom) og prøves igjen én gang ved 429."""
    global _last_google
    google = urllib.parse.urlparse(url).netloc == "news.google.com"
    for attempt in (1, 2):
        if google:
            wait = _last_google + 2.0 - time.time()
            if wait > 0:
                time.sleep(wait)
            _last_google = time.time()
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429 and google and attempt == 1:
                log("429 fra Google, venter 60 s")
                time.sleep(60)
                continue
            raise


def text(el, tag):
    c = el.find(tag)
    return (c.text or "").strip() if c is not None and c.text else ""


def parse_feed(raw, kind):
    root = ET.fromstring(raw)
    items = []
    for it in root.iter("item"):
        title = html.unescape(text(it, "title"))
        link = text(it, "link")
        pub = text(it, "pubDate")
        src_el = it.find("source")
        source = (src_el.text or "").strip() if src_el is not None and src_el.text else ""
        if kind == "gnews" and source and title.endswith(" - " + source):
            title = title[: -len(" - " + source)]
        ts = None
        if pub:
            try:
                ts = email.utils.parsedate_to_datetime(pub).astimezone(timezone.utc).isoformat()
            except Exception:
                pass
        if len(title.strip(" -–")) >= 8 and title.strip() != source and link:
            items.append({"original": title, "link": link, "source": source, "published": ts})
    # Atom
    ns = "{http://www.w3.org/2005/Atom}"
    for it in root.iter(ns + "entry"):
        title = html.unescape(text(it, ns + "title"))
        l = it.find(ns + "link")
        link = l.get("href") if l is not None else ""
        ts = text(it, ns + "updated") or text(it, ns + "published")
        if title and link:
            items.append({"original": title, "link": link, "source": "", "published": ts or None})
    return items


DISC_FILE = os.path.join(DATA, "discovered.json")
discovered = {}
FEED_RE = re.compile(r'<link\b[^>]*>', re.I)


def find_feed(url):
    """Gi en avisforside -> RSS/Atom-adresse (fra <link rel=alternate>). Huskes i discovered.json."""
    known = discovered.get(url)
    if known and known.get("feed") and time.time() - known["t"] < 7 * 86400:
        return known["feed"]
    if known and not known.get("feed") and time.time() - known["t"] < 86400:
        raise ValueError("ingen RSS (husket, prøves igjen om et døgn)")
    try:
        return _discover(url)
    except Exception:
        discovered[url] = {"feed": None, "t": time.time()}
        raise


def _discover(url):
    raw = get(url)
    head = raw[:4000].lstrip().lower()
    if head.startswith(b"<?xml") or b"<rss" in head or b"<feed" in head:
        feed = url
    else:
        feed = None
        for tag in FEED_RE.findall(raw.decode("utf-8", "replace")):
            if re.search(r'type=["\']application/(rss|atom)\+xml', tag, re.I):
                m = re.search(r'href=["\']([^"\']+)', tag, re.I)
                if m:
                    feed = urllib.parse.urljoin(url, html.unescape(m.group(1)))
                    break
        if not feed:
            for guess in ("rss", "feed", "rss.xml", "feed/", "?service=rss"):
                g = urllib.parse.urljoin(url if url.endswith("/") else url + "/", guess)
                try:
                    b = get(g, 10)[:2000].lower()
                    if b"<rss" in b or b"<feed" in b:
                        feed = g
                        break
                except Exception:
                    pass
    if not feed:
        raise ValueError("fant ingen RSS-feed på siden")
    discovered[url] = {"feed": feed, "t": time.time()}
    return feed


def site_search_url(url, country, lang=None):
    host = urllib.parse.urlparse(url).netloc.removeprefix("www.")
    path = urllib.parse.urlparse(url).path.strip("/")
    # Undermapper som /en eller /chicago tas med så søket treffer riktig utgave
    q = f"site:{host}/{path}" if path and "/" not in path and len(path) > 2 else f"site:{host}"
    edition = "hl=en-US&gl=US&ceid=US:en"
    if lang in (None, country.get("lang")):
        for s in country.get("sources", []):
            if s.get("type") == "gnews":
                edition = "&".join(kv for kv in urllib.parse.urlparse(s["url"]).query.split("&") if not kv.startswith("q="))
    return "https://news.google.com/rss/search?q=" + urllib.parse.quote(q + " when:2d") + "&" + edition


def translate(s, lang):
    key = f"{lang}|{s}"
    if key in cache:
        cache[key]["seen"] = time.time()
        return cache[key]["t"]
    t = None
    try:
        q = urllib.parse.quote(s)
        r = json.loads(get(f"https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=auto&tl={TARGET}&q={q}", 15))
        first = r[0]
        t = first if isinstance(first, str) else first[0]
    except Exception as e:
        log("oversettelse (google) feilet:", type(e).__name__, e)
        try:
            q = urllib.parse.quote(s)
            r = json.loads(get(f"https://api.mymemory.translated.net/get?q={q}&langpair={lang}|{TARGET}", 15))
            if r.get("responseStatus") == 200:
                t = r["responseData"]["translatedText"]
        except Exception as e2:
            log("oversettelse (mymemory) feilet:", type(e2).__name__, e2)
    if t:
        t = html.unescape(t).strip()
        cache[key] = {"t": t, "seen": time.time()}
    time.sleep(0.3)
    return t


def load_cache():
    global cache, discovered
    try:
        with open(CACHE_FILE) as f:
            cache = json.load(f)
    except Exception:
        cache = {}
    try:
        with open(DISC_FILE) as f:
            discovered = json.load(f)
    except Exception:
        discovered = {}


def tr_items(items, lang):
    for it in items:
        if lang not in NO_TRANSLATE:
            it["title"] = translate(it["original"], lang) or it["original"]
        else:
            it["title"] = it.pop("original")
    return items


def save_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, ensure_ascii=False)
    os.replace(tmp, path)


def run_once():
    with open(os.path.join(APP, "feeds.json")) as f:
        conf = json.load(f)
    out = []
    for c in conf["countries"]:
        lang = c.get("lang", "en")
        lists, errors = [], []
        for src in c["sources"]:
            try:
                lists.append(parse_feed(get(src["url"]), src.get("type", "rss")))
            except Exception as e:
                errors.append(f"{src['url']}: {type(e).__name__}: {e}")
                log(c["name"], "feilet:", errors[-1])
        # flett kildene: 1. fra hver, 2. fra hver, ...
        items, seen = [], set()
        for i in range(max((len(l) for l in lists), default=0)):
            for l in lists:
                if i < len(l) and l[i]["link"] not in seen and l[i]["original"].lower() not in seen:
                    seen.add(l[i]["link"])
                    seen.add(l[i]["original"].lower())
                    items.append(l[i])
        items = tr_items(items[:PER_COUNTRY], lang)
        papers = []
        for pp in c.get("papers", []):
            plang = pp.get("lang", lang)
            entry = {"name": pp["name"], "home": pp["url"], "lang": plang, "lean": pp.get("lean"), "items": [], "error": None, "via": "rss"}
            try:
                got = parse_feed(get(find_feed(pp["url"])), "rss")
                if not got:
                    raise ValueError("tom feed")
            except Exception as e:
                # reserve: Google News-søk på avisens eget domene (siste 2 døgn, nyeste først)
                log(c["name"], pp["name"], "RSS feilet, bruker Google News-søk:", f"{type(e).__name__}: {e}"[:120])
                try:
                    got = parse_feed(get(site_search_url(pp["url"], c, plang)), "gnews")
                    got.sort(key=lambda x: x["published"] or "", reverse=True)
                    entry["via"] = "gnews"
                    if not got:
                        entry["error"] = "ingen saker funnet"
                except Exception as e2:
                    got = []
                    entry["error"] = f"{type(e2).__name__}: {e2}"[:200]
                    log(c["name"], pp["name"], "feilet:", entry["error"])
            entry["items"] = tr_items(got[:PER_PAPER], plang)
            papers.append(entry)
        out.append({k: c.get(k) for k in ("code", "name", "flag")} | {"lang": lang, "items": items, "papers": papers, "error": "; ".join(errors) or None})
    # rydd cache: glem oversettelser som ikke er brukt på 7 dager
    cutoff = time.time() - 7 * 86400
    for k in [k for k, v in cache.items() if v.get("seen", 0) < cutoff]:
        del cache[k]
    save_json(CACHE_FILE, cache)
    save_json(DISC_FILE, discovered)
    save_json(os.path.join(DATA, "data.json"), {"updated": datetime.now(timezone.utc).isoformat(), "interval": INTERVAL, "countries": out})
    log("ferdig:", sum(len(c["items"]) for c in out), "saker fra", len(out), "land")


def main():
    os.makedirs(DATA, exist_ok=True)
    load_cache()
    while True:
        try:
            run_once()
        except Exception as e:
            log("runde feilet:", type(e).__name__, e)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
