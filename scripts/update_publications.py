#!/usr/bin/env python3
"""Refresh data/publications.json from Soumyajit Karmakar's Google Scholar profile.

Runs daily from .github/workflows/update-publications.yml. The website keeps its
hand-curated publication list and only adds items from this file whose titles it
does not already show.

Sources, tried in order:
  1. SerpAPI's Google Scholar Author API, if the SERPAPI_KEY secret is set
     (most reliable: Google Scholar usually blocks direct requests from GitHub's servers).
  2. The `scholarly` library, which reads Google Scholar directly.
  3. ORCID public API (0000-0003-4867-0970) as a fallback, only if both Scholar routes fail.

The file is only rewritten when a source returns at least one item, so a blocked
request never empties the list on the website.
"""
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.parse
import urllib.request

SCHOLAR_ID = "7H-o4dgAAAAJ"
ORCID = "0000-0003-4867-0970"
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "publications.json"
UA = {"User-Agent": "compchemsk-website-updater/1.0 (+https://github.com/compchemsk)"}


def get_json(url, timeout=40):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def scholar_link(title):
    return "https://scholar.google.com/scholar?q=" + urllib.parse.quote('"' + title + '"')


def from_serpapi(key):
    items, start = [], 0
    while True:
        q = urllib.parse.urlencode({"engine": "google_scholar_author", "author_id": SCHOLAR_ID,
                                    "hl": "en", "num": 100, "start": start, "sort": "pubdate", "api_key": key})
        data = get_json("https://serpapi.com/search.json?" + q)
        arts = data.get("articles") or []
        for a in arts:
            items.append({
                "title": a.get("title", "").strip(),
                "authors": a.get("authors", ""),
                "venue": a.get("publication", ""),
                "year": int(a["year"]) if str(a.get("year", "")).isdigit() else None,
                "citations": (a.get("cited_by") or {}).get("value"),
                "url": a.get("link") or scholar_link(a.get("title", "")),
            })
        if len(arts) < 100:
            break
        start += 100
    return items


def from_scholarly():
    from scholarly import scholarly  # imported lazily: optional dependency
    author = scholarly.search_author_id(SCHOLAR_ID)
    author = scholarly.fill(author, sections=["publications"])
    items = []
    for p in author.get("publications", []):
        bib = p.get("bib", {})
        title = (bib.get("title") or "").strip()
        if not title:
            continue
        year = bib.get("pub_year")
        items.append({
            "title": title,
            "authors": bib.get("author", "").replace(" and ", ", "),
            "venue": bib.get("citation", ""),
            "year": int(year) if str(year).isdigit() else None,
            "citations": p.get("num_citations"),
            "url": scholar_link(title),
        })
    return items


def from_orcid():
    req = urllib.request.Request(f"https://pub.orcid.org/v3.0/{ORCID}/works",
                                 headers={**UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as r:
        data = json.loads(r.read().decode("utf-8"))
    items = []
    for g in data.get("group", []):
        s = (g.get("work-summary") or [{}])[0]
        title = (((s.get("title") or {}).get("title") or {}).get("value") or "").strip()
        if not title:
            continue
        year = (((s.get("publication-date") or {}).get("year") or {}).get("value"))
        doi = next((e.get("external-id-value") for e in (s.get("external-ids") or {}).get("external-id", [])
                    if e.get("external-id-type") == "doi"), None)
        items.append({
            "title": title,
            "authors": "",  # ORCID summaries carry no author list
            "venue": ((s.get("journal-title") or {}).get("value") or ""),
            "year": int(year) if str(year).isdigit() else None,
            "citations": None,
            "url": f"https://doi.org/{doi}" if doi else scholar_link(title),
            "type": s.get("type"),
        })
    return items


def main():
    attempts = []
    key = os.environ.get("SERPAPI_KEY", "").strip()
    if key:
        attempts.append(("google-scholar (SerpAPI)", lambda: from_serpapi(key)))
    attempts.append(("google-scholar (scholarly)", from_scholarly))
    attempts.append(("orcid", from_orcid))

    for name, fn in attempts:
        try:
            items = [i for i in fn() if i.get("title")]
        except Exception as e:  # blocked, rate-limited, network error, missing package
            print(f"[{name}] failed: {e}", file=sys.stderr)
            continue
        if not items:
            print(f"[{name}] returned nothing", file=sys.stderr)
            continue
        items.sort(key=lambda i: (i.get("year") or 0), reverse=True)
        payload = {
            "updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "source": name,
            "profile": f"https://scholar.google.com/citations?user={SCHOLAR_ID}",
            "items": items,
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        old = json.loads(OUT.read_text()) if OUT.exists() else {}
        if old.get("items") == items and old.get("source") == name:
            print(f"[{name}] {len(items)} items, no change")
            return 0
        OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        print(f"[{name}] wrote {len(items)} items to {OUT}")
        return 0

    print("All sources failed; keeping the existing data/publications.json.", file=sys.stderr)
    return 0  # do not fail the workflow; the site keeps its last good data


if __name__ == "__main__":
    sys.exit(main())
