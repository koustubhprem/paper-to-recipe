import json
from pathlib import Path

from pydantic import ValidationError

from papers_text import paper_as_text, quote_in_text
from schema import PaperExtraction

PROCESSED = Path("data") / "processed"
GOLD_DIR = Path("evals") / "gold"


# check one label; returns a list of problems (empty means OK)
def check(raw, text):
    try:
        label = PaperExtraction.model_validate(raw)
    except ValidationError as e:
        return [f"schema error: {e}"]

    # V1 rule: only the authors' best recipe is labelled
    if label.in_scope and (len(label.recipes) != 1 or len(label.best_recipes) != 1):
        return ["V1 rule: needs exactly 1 recipe and 1 best_recipes entry"]

    quotes = [s.source.quote for s in label.process_steps] + [b.source.quote for b in label.best_recipes]
    for r in label.recipes:
        quotes += [x.source.quote for x in r.ingredients + r.properties]
    return [f'quote not found: "{q}"' for q in quotes if not quote_in_text(q, text)]


def main():
    selection = json.loads((GOLD_DIR / "selection.json").read_text(encoding="utf-8"))
    counts = {"OK": 0, "TODO": 0, "FAIL": 0}

    for item in selection:
        pmcid = item["pmcid"]
        raw = json.loads((GOLD_DIR / f"{pmcid}.json").read_text(encoding="utf-8"))

        # an untouched template is not labelled yet
        if raw.get("in_scope") and not raw.get("recipes"):
            status, problems = "TODO", []
        else:
            paper = json.loads((PROCESSED / f"{pmcid}.json").read_text(encoding="utf-8"))
            problems = check(raw, paper_as_text(paper))
            status = "FAIL" if problems else "OK"

        counts[status] += 1
        print(f"[{status:^4}] {pmcid}")
        for p in problems:
            print(f"         {p}")

    print(f"\nlabelled: {counts['OK']}   to do: {counts['TODO']}   with problems: {counts['FAIL']}")


if __name__ == "__main__":
    main()