import re

# one plain-text version of a paper, used for labelling, for the LLM and for checking quotes
def paper_as_text(paper):
    parts = [f"# {paper.get('title', '')}", "", "## Abstract", paper.get("abstract", "")]
    for sec in paper.get("sections", []):
        parts += ["", f"## {sec['heading']} [{sec['kind']}]", sec["text"]]
    for table in paper.get("tables", []):
        parts += ["", f"## {table['label']}: {table['caption']}"]
        parts += [" | ".join(row) for row in table["rows"]]
    return "\n".join(parts)


# lower-case and collapse whitespace so small formatting differences don't matter
def normalise(text):
    return re.sub(r"\s+", " ", text).strip().lower()


def quote_in_text(quote, text):
    return normalise(quote) in normalise(text)