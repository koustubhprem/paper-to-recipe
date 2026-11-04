import json
import random
from collections import defaultdict
from pathlib import Path

from papers_text import paper_as_text

PROCESSED = Path("data") / "processed"
VIEW_DIR = Path("data") / "gold_view"
GOLD_DIR = Path("evals") / "gold"
PER_FAMILY = 5
DEV_PER_FAMILY = 3
SEED = 7

TEMPLATE = {
    "in_scope": True,
    "out_of_scope_reason": None,
    "intended_application": None,
    "process_steps": [],
    "recipes": [],
    "best_recipes": [],
}


def main():
    VIEW_DIR.mkdir(parents=True, exist_ok=True)
    GOLD_DIR.mkdir(parents=True, exist_ok=True)

    # group processed papers by family
    by_family = defaultdict(list)
    papers = {}
    for path in sorted(PROCESSED.glob("*.json")):
        paper = json.loads(path.read_text(encoding="utf-8"))
        papers[paper["pmcid"]] = paper
        by_family[paper["family"]].append(paper["pmcid"])

    # pick papers at random per family; the first few are dev, the rest held out as test
    rng = random.Random(SEED)
    picked = {f: rng.sample(sorted(by_family[f]), PER_FAMILY) for f in sorted(by_family)}

    # labelling order goes round the families, so each round covers all three
    selection = []
    for i in range(PER_FAMILY):
        for family in sorted(picked):
            selection.append({
                "order": len(selection) + 1,
                "pmcid": picked[family][i],
                "family": family,
                "split": "dev" if i < DEV_PER_FAMILY else "test",
            })

    (GOLD_DIR / "selection.json").write_text(json.dumps(selection, indent=2), encoding="utf-8")

    for item in selection:
        pmcid = item["pmcid"]
        (VIEW_DIR / f"{pmcid}.md").write_text(paper_as_text(papers[pmcid]), encoding="utf-8")

        # never overwrite a label you have already started
        label_file = GOLD_DIR / f"{pmcid}.json"
        if not label_file.exists():
            label_file.write_text(json.dumps(TEMPLATE, indent=2), encoding="utf-8")

        print(f"{item['order']:>2}  {item['split']:5} {item['family']:9} {pmcid}  {papers[pmcid].get('title', '')[:60]}")

    print(f"\n{len(selection)} papers selected")
    print(f"read:  {VIEW_DIR}/<pmcid>.md")
    print(f"label: {GOLD_DIR}/<pmcid>.json")


if __name__ == "__main__":
    main()