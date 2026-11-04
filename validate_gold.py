import json
from pathlib import Path

from pydantic import ValidationError

from papers_text import paper_as_text, quote_in_text
from schema import PaperExtraction

PROCESSED = Path("data") / "processed"
GOLD_DIR = Path("evals") / "gold"


# every quote in a label, with where it was used
def all_quotes(label):
    for step in label.process_steps:
        yield f"step {step.order}", step.source.quote
    for recipe in label.recipes:
        for ing in recipe.ingredients:
            yield f"{recipe.code} ingredient '{ing.name}'", ing.source.quote
        for prop in recipe.properties:
            yield f"{recipe.code} property '{prop.name}'", prop.source.quote
    for best in label.best_recipes:
        yield f"best recipe {best.code}", best.source.quote


def main():
    selection = json.loads((GOLD_DIR / "selection.json").read_text(encoding="utf-8"))
    done, todo, problems = 0, 0, 0

    for item in selection:
        pmcid = item["pmcid"]
        raw = json.loads((GOLD_DIR / f"{pmcid}.json").read_text(encoding="utf-8"))

        # an untouched template is not labelled yet
        if raw.get("in_scope") and not raw.get("recipes"):
            print(f"[TODO] {pmcid}")
            todo += 1
            continue

        try:
            label = PaperExtraction.model_validate(raw)
        except ValidationError as e:
            print(f"[FAIL] {pmcid} schema error:\n{e}\n")
            problems += 1
            continue

        paper = json.loads((PROCESSED / f"{pmcid}.json").read_text(encoding="utf-8"))
        text = paper_as_text(paper)
        missing = [(where, q) for where, q in all_quotes(label) if not quote_in_text(q, text)]

        if missing:
            print(f"[FAIL] {pmcid} quotes not found in the paper:")
            for where, q in missing:
                print(f"         {where}: \"{q}\"")
            problems += 1
        else:
            n_props = sum(len(r.properties) for r in label.recipes)
            print(f"[ OK ] {pmcid}  {len(label.recipes)} recipes, {n_props} properties")
            done += 1

    print(f"\nlabelled: {done}   to do: {todo}   with problems: {problems}")


if __name__ == "__main__":
    main()