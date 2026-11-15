import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from google import genai

from papers_text import paper_as_text
from schema import PaperExtraction

MODEL = "gemini-3.8-flash"
PROMPT_VERSION = "v2"
PROCESSED = Path("data") / "processed"
OUT_DIR = Path("data") / "extractions"
EXAMPLE_PATH = Path("evals") / "example.json"

RULES = """You extract one film recipe from a research paper into JSON that follows the given schema.

1. Scope. in_scope is true only for a bio-based film for packaging, food contact or edible use, made by casting from a solution, with measured properties. Films used as supports, filters or carriers are out of scope. If out of scope, give in_scope false, a reason, and leave process_steps, recipes and best_recipes empty.

2. One recipe. Give exactly one recipe and one best_recipes entry: the film the authors present as their best. Choose it in this order and record the step in chosen_by:
   stated: the abstract or conclusion presents it as the best, optimised or recommended film ("X had the highest Y" alone is not enough);
   abstract: the abstract reports the values of one film;
   aim: the film that best meets the paper's stated aim (a film that fails a safety test in the paper is not chosen if another passes);
   default: the main new formulation, not the control.
   A best base formulation chosen before adding the active ingredient is not the best film.
   An in-scope paper always has a best_recipes entry; the default step always gives one.

3. Values as written. Never calculate, convert, add up or estimate. If something is not stated, use null. Ratios and ranges go in unit as written. Ignore significance letters after values. If the abstract and a table disagree, use the table.

4. Ingredients. Only ingredients present in the best film. A solution used as an ingredient is recorded as the solution amount with its concentration in the name. An acid used to dissolve chitosan has role ph_adjuster. origin, feedstock and from_waste only as the paper states them; glycerol, sorbitol and acetic acid are unknown unless stated.

5. Steps. Steps cover making the best film only, in the order the paper writes them, and end at drying. Leave out steps for ingredients the best film does not contain. Leave applies_to empty. Conditioning, peeling, testing and applying the film to food are not steps. If the best film is "prepared as" another film plus something, include the other film's steps. An ingredient the authors make in this paper with the method given gets ingredient_preparation steps. If the paper gives alternative methods without saying which was used, give only the steps they share. Whenever you give duration_value, also give duration_unit (s, min, h or day); if no duration is stated, leave both out.

6. Properties. Only properties of the film, stated as numbers in the text or tables. Skip values shown only in figures, relative statements such as "3 times higher", and properties of the solution or extract. Conditioning humidity and temperature go on mechanical properties. Water vapour transmission rate is name other, not water_vapour_permeability.

7. Quotes. Every source.quote is copied exactly from the paper text below, usually under 200 characters. Table quotes are the table row as written with | separators. A step's description says only what its quote supports; never describe values the quote does not contain. Use section "other" for the conclusion and introduction.

8. gaps. List what someone would need to make the film that the paper does not state, such as a missing amount, solvent, time or method. Do not list missing measurements. If the paper gives no steps or no ingredients for the best film, leave that list empty and add a gap starting with "critical:" that says what is missing, e.g. "critical: film preparation method not given".

9. The example below shows the format only. It is an invented paper and is shortened: a real answer includes every step, ingredient and property that the rules allow. Do not copy its content.
"""

# read the API key from .env
load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


# load one parsed paper and turn it into the text the model reads
def load_paper_text(pmcid):
    paper = json.loads((PROCESSED / f"{pmcid}.json").read_text(encoding="utf-8"))
    return paper_as_text(paper)


# the invented example label, sent without indentation to save tokens
def load_example():
    data = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
    return json.dumps(data, ensure_ascii=False)


# send the rules, the example, the paper and the schema; return the raw JSON text
def call_gemini(text):
    prompt = (f"{RULES}\n=== EXAMPLE (format only, invented paper) ===\n{load_example()}"
              f"\n=== PAPER ===\n{text}")
    reply = client.interactions.create(
        model=MODEL,
        input=prompt,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": PaperExtraction.model_json_schema(),
        },
    )
    return reply.output_text


# keep the raw reply before validating, so nothing is lost if validation fails
def save_raw(pmcid, raw):
    (OUT_DIR / "raw").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "raw" / f"{pmcid}.json").write_text(raw, encoding="utf-8")


# save the validated extraction with the run details
def save_extraction(pmcid, extraction):
    record = {
        "pmcid": pmcid,
        "model": MODEL,
        "prompt_version": PROMPT_VERSION,
        "extracted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "extraction": extraction.model_dump(),
    }
    path = OUT_DIR / f"{pmcid}.json"
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")


# read, call, save raw, validate, save; print each stage
def extract_paper(pmcid):
    text = load_paper_text(pmcid)
    print(f"{pmcid}: {len(text):,} characters, calling {MODEL} ...")
    start = time.time()
    raw = call_gemini(text)
    print(f"{pmcid}: reply in {time.time() - start:.0f} s, validating ...")
    save_raw(pmcid, raw)
    extraction = PaperExtraction.model_validate_json(raw)
    save_extraction(pmcid, extraction)
    return extraction


# one-line summary of what came back; validation guarantees a best recipe when in scope
def summary(pmcid, ex):
    if not ex.in_scope:
        return f"{pmcid}  out of scope ({ex.out_of_scope_reason})"
    b = ex.best_recipes[0]
    r = next(r for r in ex.recipes if r.code == b.code)
    return (f"{pmcid}  best: {b.code} ({b.chosen_by})  "
            f"{len(r.ingredients)} ingredients, {len(ex.steps_for(b.code))} steps, "
            f"{len(r.properties)} properties, {len(r.gaps)} gaps")


def main():
    pmcid = sys.argv[1]
    extraction = extract_paper(pmcid)
    print(summary(pmcid, extraction))


if __name__ == "__main__":
    main()