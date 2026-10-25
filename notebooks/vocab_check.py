import json
import re
from collections import Counter
from pathlib import Path

PROCESSED = Path("data") / "processed"

# idea is to check which properties and steps are most commonly mentioned in the papers, to help guide the design of a recipe extraction model. The regexes are not perfect, but they should be good enough to get a rough idea of what is being discussed in the papers.
PROPERTIES = {
    "tensile strength": r"tensile strength",
    "elongation at break": r"elongation at break|\bEAB\b",
    "young's modulus": r"young.?s modulus|elastic modulus",
    "water vapour permeability": r"water vapou?r permeability|\bWVP\b",
    "water solubility": r"water solubility|solubility in water",
    "moisture content": r"moisture content",
    "contact angle": r"contact angle",
    "thickness": r"thickness",
    "swelling / water uptake": r"swelling|water uptake|water absorption",
    "opacity / transparency": r"opacity|transparency|transmittance",
    "colour (L*a*b*)": r"colou?r\b.*\bL\*|\bL\*.*\ba\*",
    "oxygen permeability": r"oxygen permeability|\bOTR\b|\bOP\b",
    "thermal (TGA/DSC)": r"\bTGA\b|\bDSC\b|glass transition|thermal stability",
    "antioxidant activity": r"antioxidant activity|\bDPPH\b|\bABTS\b",
    "antimicrobial activity": r"antimicrobial|antibacterial|inhibition zone",
    "biodegradation": r"biodegradation|soil burial",
}

STEPS = {
    "sonication": r"sonicat|ultrasound|ultrason",
    "homogenising": r"homogeni[sz]",
    "degassing": r"degass|vacuum to remove|air bubbles",
    "neutralising / pH adjustment": r"neutrali[sz]|ph (was )?adjusted",
    "filtration": r"filter|filtrat",
    "crosslinking bath (CaCl2)": r"cacl2|calcium chloride",
    "centrifugation": r"centrifug",
}


def methods_text(paper):
    return " ".join(s["text"] for s in paper["sections"] if s["kind"] == "methods")


def all_text(paper):
    tables = " ".join(" ".join(" ".join(r) for r in t["rows"]) + " " + t["caption"]
                      for t in paper["tables"])
    return " ".join(s["text"] for s in paper["sections"]) + " " + tables


def count(papers, patterns, text_fn):
    counts = Counter()
    for p in papers:
        text = text_fn(p)
        for label, pattern in patterns.items():
            if re.search(pattern, text, re.I):
                counts[label] += 1
    return counts


def main():
    papers = [json.loads(f.read_text(encoding="utf-8")) for f in PROCESSED.glob("*.json")]
    n = len(papers)
    print(f"{n} papers\n")

    print("Papers mentioning each property:")
    for label, c in count(papers, PROPERTIES, all_text).most_common():
        print(f"  {label:28} {c:>4}  ({c / n:.0%})")

    print("\nPapers mentioning each step in their methods:")
    for label, c in count(papers, STEPS, methods_text).most_common():
        print(f"  {label:28} {c:>4}  ({c / n:.0%})")


if __name__ == "__main__":
    main()