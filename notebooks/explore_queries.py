"""Scratch analysis used to design the search query in queries.py.

Findings (Oct 2026):
- Narrow property gate kept: wide gate added only 9-17% more papers.
- ~50% of chitosan/alginate hits were medical before filtering, so
  medical, synthetic-plastic, extrusion and review exclusions were added.
"""
import sys
from pathlib import Path

# Let this script import queries.py from the project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

from queries import FAMILIES, PROPS, build_query

URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

# Wider property gate, only used here for comparison
PROPS_WIDE = ('("tensile strength" OR "elongation at break" '
              'OR "water vapor permeability" OR "water vapour permeability" '
              'OR "young\'s modulus" OR "water solubility" '
              'OR "contact angle" OR "biodegradation")')


def count_hits(query):
    params = {"query": query, "format": "json", "pageSize": 1}
    resp = requests.get(URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()["hitCount"]


def show_titles(query, n=10):
    params = {"query": query, "format": "json", "pageSize": n}
    resp = requests.get(URL, params=params, timeout=30)
    resp.raise_for_status()
    for r in resp.json()["resultList"]["result"]:
        print("   -", r.get("title", ""))


if __name__ == "__main__":
    print("Final query: papers per family (need at least 80)")
    print("and how many a wider property gate would add:\n")

    for family in FAMILIES:
        narrow = build_query(family)
        wide = narrow.replace(PROPS, PROPS_WIDE)

        n = count_hits(narrow)
        w = count_hits(wide)
        extra = (w - n) / n * 100 if n else 0

        print(f"{family:10} final: {n:>5}   wide: {w:>5}   (+{extra:.0f}%)")

    for family in FAMILIES:
        print(f"\n{family}: first 10 titles from the final query")
        show_titles(build_query(family))