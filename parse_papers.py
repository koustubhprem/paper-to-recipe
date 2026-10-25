import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

PAPERS_FILE = Path("data") / "papers.jsonl"
RAW_DIR = Path("data") / "raw"
OUT_DIR = Path("data") / "processed"

METHODS = re.compile(r"method|material|experimental|preparation|synthesis|fabrication|formulation", re.I)
RESULTS = re.compile(r"result|discussion|characteri[sz]ation|propert", re.I)
INTRO = re.compile(r"intro|background", re.I)
CONCLUSION = re.compile(r"conclu", re.I)


def clean(text):
    return re.sub(r"\s+", " ", text).strip()


def text_of(el):
    return clean("".join(el.itertext())) if el is not None else ""


# checks the heading and sec-type attribute, methods first
def classify(heading, sec_type):
    probe = f"{sec_type} {heading}"
    if METHODS.search(probe):
        return "methods"
    if RESULTS.search(probe):
        return "results"
    if INTRO.search(probe):
        return "introduction"
    if CONCLUSION.search(probe):
        return "conclusion"
    return "other"


def remove_tables_and_figures(sec):
    for parent in sec.iter():
        for child in list(parent):
            if child.tag in ("table-wrap", "fig", "disp-formula"):
                parent.remove(child)


def section_text(sec):
    remove_tables_and_figures(sec)
    parts = []
    for el in sec.iter():
        if el.tag == "title":
            parts.append(f"## {text_of(el)}")
        elif el.tag == "p":
            parts.append(text_of(el))
    # drop the section's own heading, it is stored separately
    if parts and parts[0].startswith("## "):
        parts = parts[1:]
    return "\n".join(p for p in parts if p not in ("", "## "))


def parse_table(tw):
    rows = []
    for tr in tw.iter("tr"):
        cells = [text_of(c) for c in tr if c.tag in ("td", "th")]
        if any(cells):
            rows.append(cells)
    return {
        "label": text_of(tw.find("label")),
        "caption": text_of(tw.find("caption")),
        "rows": rows,
    }


def parse_paper(path):
    root = ET.parse(path).getroot()
    meta = root.find(".//article-meta")

    # tables are read before sections, because section_text removes them
    tables = [parse_table(tw) for tw in root.iter("table-wrap")]

    sections = []
    body = root.find("body")
    if body is not None:
        for sec in body.findall("sec"):
            heading = text_of(sec.find("title"))
            sections.append({
                "heading": heading,
                "kind": classify(heading, sec.get("sec-type", "")),
                "text": section_text(sec),
            })

    return {
        "title": text_of(meta.find("title-group/article-title")) if meta is not None else "",
        "abstract": text_of(meta.find("abstract")) if meta is not None else "",
        "sections": sections,
        "tables": tables,
    }


def load_papers():
    with PAPERS_FILE.open(encoding="utf-8") as f:
        return {p["pmcid"]: p for p in (json.loads(line) for line in f if line.strip())}


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    papers = load_papers()
    parsed, no_body, no_methods, n_tables, errors = 0, [], [], 0, []

    for path in sorted(RAW_DIR.glob("*.xml")):
        pmcid = path.stem
        try:
            content = parse_paper(path)
        except ET.ParseError as e:
            errors.append(f"{pmcid} ({e})")
            continue

        record = {**papers.get(pmcid, {"pmcid": pmcid}), **content}
        out = OUT_DIR / f"{pmcid}.json"
        out.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")

        parsed += 1
        n_tables += len(content["tables"])
        if not content["sections"]:
            no_body.append(pmcid)
        elif not any(s["kind"] == "methods" for s in content["sections"]):
            no_methods.append(pmcid)

    print(f"Parsed: {parsed}   errors: {len(errors)}")
    if parsed:
        print(f"Tables: {n_tables} (avg {n_tables / parsed:.1f} per paper)")
    print(f"No body text: {len(no_body)}   no methods section found: {len(no_methods)}")
    if no_methods:
        print("No methods:", ", ".join(no_methods[:15]))
    if errors:
        print("Errors:", ", ".join(errors))


if __name__ == "__main__":
    main()