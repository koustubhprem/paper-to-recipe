import json
import time
from pathlib import Path

import requests

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"
PAPERS_FILE = Path("data") / "papers.jsonl"
RAW_DIR = Path("data") / "raw"
DELAY = 0.5

def load_papers():
    with PAPERS_FILE.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

# using return because the data size is small enough to fit in memory. If the dataset grows, consider yielding one record at a time instead of loading everything into memory.

def fetch_xml(pmcid, retries=3):
    url = f"{BASE}/{pmcid}/fullTextXML"

    for attempt in range(retries):
        try:
            resp = requests.get(url, timeout=60)
        except requests.RequestException:
            time.sleep(2 ** attempt)
            continue

        if resp.status_code == 200 and resp.content.strip():
            return resp.content
        if resp.status_code == 404:
            return None
        time.sleep(2 ** attempt)
    return None

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    papers = load_papers()
    downloaded, skipped, failed = 0, 0, []

    for i, p in enumerate(papers, start=1):
        out = RAW_DIR / f"{p['pmcid']}.xml"
        # already downloaded on an earlier run
        if out.exists():
            skipped += 1
            continue

        xml = fetch_xml(p["pmcid"])
        if xml is None:
            failed.append(p["pmcid"])
        else:
            out.write_bytes(xml)
            downloaded += 1

        print(f"[{i}/{len(papers)}] {p['pmcid']} {'ok' if xml else 'FAILED'}")
        time.sleep(DELAY)

    print(f"\nDownloaded: {downloaded}   already had: {skipped}   failed: {len(failed)}")
    if failed:
        print("Failed:", ", ".join(failed))

if __name__ == "__main__":
    main()