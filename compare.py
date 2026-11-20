import json
import sys
from pathlib import Path

import pandas as pd

GOLD_DIR = Path("evals") / "gold"
OUT_DIR = Path("data") / "extractions"


# one row per field: paper, part, item, field, value, plus a key for lookups
def rows_for(pmcid, data):
    data = data.get("extraction", data)
    rows = []

    def add(part, item, obj):
        for field, value in obj.items():
            if field == "source":
                for k, v in value.items():
                    rows.append([pmcid, part, item, f"source.{k}", v])
            elif isinstance(value, list):
                rows.append([pmcid, part, item, field, "; ".join(map(str, value))])
            else:
                rows.append([pmcid, part, item, field, value])

    add("paper", "", {k: data.get(k) for k in ["in_scope", "out_of_scope_reason", "intended_application"]})
    for step in data.get("process_steps", []):
        add("step", str(step["order"]), step)
    for recipe in data.get("recipes", []):
        add("recipe", recipe["code"], {k: recipe[k] for k in ["code", "description", "is_control", "base_polymers", "gaps"]})
        for ing in recipe["ingredients"]:
            add("ingredient", ing["name"], ing)
        for prop in recipe["properties"]:
            add("property", f"{prop['name']} | {prop['name_reported']}", prop)
    for best in data.get("best_recipes", []):
        add("best", "", best)

    df = pd.DataFrame(rows, columns=["paper", "part", "item", "field", "value"])
    # same key in both tabs, first column, so VLOOKUP or XLOOKUP finds the matching row
    df.insert(0, "key", df["paper"] + "|" + df["part"] + "|" + df["item"].str.lower() + "|" + df["field"])
    return df


def main():
    split = sys.argv[1] if len(sys.argv) > 1 else "test"
    selection = json.loads((GOLD_DIR / "selection.json").read_text(encoding="utf-8"))
    pmcids = [item["pmcid"] for item in selection if item["split"] == split]

    gold, gemini = [], []
    for pmcid in pmcids:
        gold.append(rows_for(pmcid, json.loads((GOLD_DIR / f"{pmcid}.json").read_text(encoding="utf-8"))))
        path = OUT_DIR / f"{pmcid}.json"
        if path.exists():
            gemini.append(rows_for(pmcid, json.loads(path.read_text(encoding="utf-8"))))

    out = Path("evals") / f"gold_vs_gemini_v5_{split}.xlsx"
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        pd.concat(gold, ignore_index=True).to_excel(writer, sheet_name="gold", index=False)
        pd.concat(gemini, ignore_index=True).to_excel(writer, sheet_name="gemini", index=False)
    print(f"saved {out}")


if __name__ == "__main__":
    main()