"""Step 1: build the list of papers for the corpus.

For each material family, find every paper that matches the final query,
keep only those with an allowed Creative Commons licence, pick a random
sample, and save the list to data/papers.jsonl. Nothing is downloaded yet.
"""
import html
import json
import random
import re
from collections import Counter
from pathlib import Path

import requests

from queries import FAMILIES, build_query

URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
PER_FAMILY = 100
SEED = 42
ALLOWED_LICENCES = {"cc-by", "cc-by-sa", "cc0"}
OUT_FILE = Path("data") / "papers.jsonl"


def search_all(query):
    """Return every result for a query, following the pages."""
    results = []
    cursor = "*"
    while True:
        params = {
            "query": query,
            "format": "json",
            "resultType": "core",
            "pageSize": 1000,
            "cursorMark": cursor,
        }
        resp = requests.get(URL, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        page = data["resultList"]["result"]
        results.extend(page)

        next_cursor = data.get("nextCursorMark")
        if not page or next_cursor == cursor:
            break
        cursor = next_cursor
    return results


def clean_licence(raw):
    """'CC BY', 'cc_by', 'CC-BY' -> 'cc-by'."""
    if not raw:
        return ""
    return raw.strip().lower().replace("_", "-").replace(" ", "-")


def clean_title(raw):
    """Turn '&lt;i&gt;Trapa&lt;/i&gt; shell' into 'Trapa shell'."""
    text = html.unescape(raw or "")
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def to_record(r, family):
    """Keep only the fields we need from one API result."""
    journal = r.get("journalInfo", {}).get("journal", {}).get("title")
    return {
        "pmcid": r.get("pmcid"),
        "doi": r.get("doi"),
        "title": clean_title(r.get("title")),
        "journal": journal,
        "year": int(r["pubYear"]) if r.get("pubYear") else None,
        "licence": clean_licence(r.get("license")),
        "family": family,
    }


def main():
    rng = random.Random(SEED)
    chosen = []
    seen = set()

    for family in FAMILIES:
        results = search_all(build_query(family))
        records = [to_record(r, family) for r in results if r.get("pmcid")]
        records = list({p["pmcid"]: p for p in records}.values())
        licensed = [p for p in records if p["licence"] in ALLOWED_LICENCES]
        fresh = [p for p in licensed if p["pmcid"] not in seen]

        fresh.sort(key=lambda p: p["pmcid"])
        sample = rng.sample(fresh, min(PER_FAMILY, len(fresh)))

        for p in sample:
            seen.add(p["pmcid"])
        chosen.extend(sample)

        print(f"{family:10} found: {len(records):>4}   "
              f"licensed: {len(licensed):>4}   "
              f"new: {len(fresh):>4}   sampled: {len(sample):>3}")

    OUT_FILE.parent.mkdir(exist_ok=True)
    with OUT_FILE.open("w", encoding="utf-8") as f:
        for p in chosen:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    print(f"\nSaved {len(chosen)} papers to {OUT_FILE}")
    print("Licences:", dict(Counter(p["licence"] for p in chosen)))
    years = [p["year"] for p in chosen if p["year"]]
    if years:
        print(f"Years: {min(years)}-{max(years)}")


if __name__ == "__main__":
    main()