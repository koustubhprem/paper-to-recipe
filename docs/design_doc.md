# Design notes

Decisions made while building paper-to-recipe, with the reasoning and the evidence behind them. Newest changes are logged in the change log at the end.

Last updated: 25 Oct 2026

---

## 1. Goal and scope

Build a pipeline that turns open-access research papers into structured, sourced recipes for bio-based films, then a question-answering layer that only answers from those records.

Two layers:
- Extraction: papers to recipe records (ingredients, amounts, steps, properties, test conditions), every value linked to the exact text it came from.
- Grounded RAG: answers questions from the records, cites them, and says "no data" when there is none.

The system compares and retrieves what papers report. It does not generate new recipes or give formulation advice. Recipes are exported "as reported" so they can be reproduced in a lab.

Why this framing: testing Materiom AI showed the weak point is the data layer (wrong or unsourced citations, different answers in different chats, generic recipes), not the text generation. A sourced dataset fixes the cause.

In scope for the MVP:
- 3 material families: starch, chitosan, alginate
- solution-cast films for packaging or food
- values from text and tables only

Out of scope for the MVP:
- composites, foams, boards, 3D-printed pastes
- extruded, blown or moulded films
- values only shown in figures
- paywalled papers, scraping Materiom Commons
- generating or recommending new formulations

---

## 2. Data source

Chosen: Europe PMC REST API.

| Source | Considered for | Decision |
|---|---|---|
| Europe PMC | search + full text | Used. Free, no key. Full text as JATS XML with sections and tables tagged. Licence on every record. |
| OpenAlex | discovery, DOIs, licences | Not needed yet. Europe PMC already gives DOI, journal, year and licence. |
| CORE | repository full text | Not used. Mostly flat text from PDFs, harder to find methods and tables. |
| Semantic Scholar | search, citations | Not used. Limited full text. |
| EBI Search (/ebisearch/ws/rest/{domain}) | general EBI search | Not used for papers. Returns IDs and chosen fields only, no full text, generic query syntax. Possible later use: mapping ingredient names to ChEBI chemical IDs. |

Main reason: structured XML means the methods section and every table can be read directly. With PDFs, the layout has to be reconstructed first.

Trade-off: Europe PMC is life-science focused, so some materials-science journals are thin. The pipeline is not tied to one source, so others can be added later.

---

## 3. Material families

Changed from 8 families (bioplastic, alginate, chitosan, starch, pectin, gelatin, mycelium, cellulose) to 3: starch, chitosan, alginate.

Reasons:
- My 5 Materiom AI tests were on these 3 (potato starch, alginate, chitosan), so a head-to-head comparison needs them.
- The gold set is labelled by hand. 3 families keeps it manageable.
- All three are polysaccharides made into films the same way (dissolve, cast, dry) and tested with the same methods, so properties are comparable.
- Mycelium and cellulose composites are not cast films, so they were out of scope anyway.
- Measured accuracy on 3 families is a stronger result than unmeasured output on 8.

Adding a family later is one line in queries.py plus a few more gold papers. Pectin and gelatin are the easiest next ones.

---

## 4. Search query (queries.py)

The query decides what the whole dataset contains, so it was sized and tested before downloading anything.

### 4.1 Starting point was too narrow

| Query | Hits |
|---|---|
| TITLE_ABS:"alginate film" AND OPEN_ACCESS:y | 38 |
| same + "tensile strength" | 15 |

An exact phrase misses "alginate films", "alginate-based film", "sodium alginate membrane". Fix: material word and film words matched separately, with film/films/membrane/bioplastic.

### 4.2 Property gate

The query requires at least one of: tensile strength, elongation at break, water vapour permeability (both spellings).

This is a gate, not the list of what gets extracted. It only checks the paper measured something. Extraction later takes every property the paper reports.

Chosen because nearly every packaging-film paper reports them, they are standard tests (ASTM D882, ASTM E96), and my Materiom AI tests asked about them.

Narrow vs wide gate (wide added Young's modulus, water solubility, contact angle, biodegradation):

| Family | broad | + narrow gate | + wide gate |
|---|---|---|---|
| starch | 1166 | 618 | 692 |
| chitosan | 2586 | 1020 | 1473 |
| alginate | 996 | 391 | 542 |

Before medical filtering the wide gate added 12% / 44% / 39%, mostly medical papers. After the final filters it added 9-17%. Decision: keep the narrow gate.

### 4.3 Medical papers

Chitosan and alginate are heavily used in wound dressings and drug delivery.

| Family | + narrow gate | with medical words | share |
|---|---|---|---|
| starch | 618 | 118 | 19% |
| chitosan | 1020 | 487 | 48% |
| alginate | 391 | 207 | 53% |

Without a filter, about half the chitosan and alginate corpus would be medical. Out of scope for packaging, and it would dominate the data.

Options compared:
- A: exclude medical words
- B: require packaging words (packaging, edible, food)
- C: both

Chosen: C. We only need about 50 papers per family and have hundreds, so losing some good papers (lower recall) costs little, while keeping bad ones (lower precision) wastes extraction and adds noise. Precision over recall.

### 4.4 Other exclusions found by reading titles

Read 30 titles (10 per family) from approach C and marked each in scope / medical / out of scope. No medical papers left. Two misses:
- "TPS/PBAT blown films": PBAT is a petroleum-based plastic, and blown film is extrusion, not casting. Added SYNTHETIC and NOT_CAST.
- A review paper. Added REVIEW.

| Exclusion | Terms | Searched in | Why |
|---|---|---|---|
| BIOMED | wound, drug delivery, drug release, scaffold, tissue engineering | full text | medical use, strict is fine |
| SYNTHETIC | PBAT, polyethylene, polypropylene, PBS, PCL | title/abstract | not bio-based |
| NOT_CAST | blown, extrusion, extruded, injection/compression moulding | title/abstract | different process, properties not comparable |
| REVIEW | PUB_TYPE "review", "review" in title | type / title | no original recipes, repeats other papers' results |

SYNTHETIC and NOT_CAST only look at title and abstract, so a cast-film paper that says "compared with polyethylene" in its discussion is kept. They only remove papers whose main subject is extrusion or a synthetic blend.

NOT_CAST reasoning: extrusion and moulding need industrial equipment, so most of it is not usable by makers. But the main reason is comparability. The same starch + glycerol recipe gives very different tensile strength cast vs extruded, and the recipes are written differently (screw speed and temperature zones vs dissolve and dry). Excluding them keeps one process for the MVP. Reversible later.

PLA is bio-based so it is not excluded. Starch/PLA blends are usually extruded and get caught by NOT_CAST.

### 4.5 Where each part searches

| Prefix | Searches | Used for |
|---|---|---|
| TITLE_ABS: | title + abstract | material, film words, SYNTHETIC, NOT_CAST |
| no prefix | everything, including full text | PROPS, PACKAGING, BIOMED |
| TITLE: | title | REVIEW backup |
| OPEN_ACCESS:, IN_EPMC:, PUB_TYPE: | metadata | access, full text available, review type |

Topic is restricted to title/abstract so the paper is mainly about that material. Evidence (properties) is searched everywhere because measurements are in the body.

### 4.6 Final query

```
TITLE_ABS:{family} AND (film words) AND (property gate) AND (packaging words)
AND OPEN_ACCESS:y AND IN_EPMC:y
NOT BIOMED NOT SYNTHETIC NOT NOT_CAST NOT REVIEW
```

In words: open-access papers with full text in Europe PMC, mainly about starch, chitosan or alginate films, reporting tensile strength, elongation or WVP, mentioning packaging, edible or food. No medical, petroleum-plastic, extruded/moulded or review papers.

The query lives in one file (queries.py) that every script imports, so there is only one copy.

---

## 5. Sampling the papers (list_papers.py)

### 5.1 Random sample instead of top results

The API returns results in its own ranking order. The top titles were almost all recent active-packaging papers (films with extracts, oils, nanoparticles). Plain baseline films, which my Materiom AI tests asked about, were rare.

Decision: collect all matching papers, then pick at random with a fixed seed (42). Results are sorted by PMCID before sampling so the same sample comes out every run.

Year-based sampling (equal numbers per period) was considered and parked. Most papers really are recent because the field has grown, so recency is partly real, not only an API effect. Check the year distribution after download and only add year sampling if baseline films are missing.

### 5.2 How many

- Changed from 80 to 100 per family (300 total).
- Expect to keep about 50 per family after relevance checks during extraction.
- Equal numbers per family, not in proportion to the literature, so each family can be scored separately and none dominates answers.

### 5.3 Licence

Only CC BY, CC BY-SA, CC0, so extracted data can be shared. Licence text is normalised first ("CC BY", "cc_by", "CC-BY" all become "cc-by").

### 5.4 Duplicates

Two kinds:
- A blend paper matching two families (e.g. starch + chitosan). Handled with a `seen` set so it is only picked once.
- The same paper returned twice within one family. Europe PMC can hold a PubMed record and a PubMed Central record with the same PMCID.

The second one was found because the download reported 300 papers but only 263 files existed (37 duplicates). Fix: deduplicate by PMCID right after the search, before sampling:

```python
records = list({p["pmcid"]: p for p in records}.values())
```

### 5.5 Results after the fix

| Family | unique found | CC licensed | after removing blends | sampled |
|---|---|---|---|---|
| starch | 372 | 320 (86%) | 320 | 100 |
| chitosan | 401 | 329 (82%) | 321 | 100 |
| alginate | 147 | 127 (86%) | 123 | 100 |

- The licence filter removed about 15%, mostly CC BY-NC.
- All 300 sampled papers are CC BY (no CC BY-SA or CC0), typical of open-access publishers such as MDPI.
- Alginate is the thin family: 100 of 123 eligible. If many alginate papers turn out to be out of scope, the alginate query may need widening (e.g. "coating").
- 12 blend papers were kept to one family.

### 5.6 Cleaning

Titles contained HTML for species names (`&lt;i&gt;Trapa bispinosa&lt;/i&gt;`). Unescaped and tags removed before saving.

---

## 6. Download (download_papers.py)

- Endpoint: /{PMCID}/fullTextXML
- 3 retries with waits of 1, 2, 4 seconds; a 404 gives up straight away
- skips files already downloaded, so a stopped run can be restarted
- 0.5 s pause between papers

Result: 300 papers. 2 failed on the first run and downloaded on the second, so the failures were temporary.

---

## 7. Storage

| Data | Where | In git? | Why |
|---|---|---|---|
| paper list | data/papers.jsonl | yes | Europe PMC changes daily; this is the record of exactly which papers were used |
| raw XML | data/raw/ | no | ~50 MB, regenerated from the list in minutes |
| parsed papers | data/processed/ | no | regenerated by parse_papers.py |
| gold labels | evals/gold/ | yes | my own work, small |
| future recipe records | SQLite file in data/ | no | regenerated |
| future RAG index | Chroma in data/ | no | regenerated |
| future export | data/export/ | yes, later | the shareable dataset, CC BY 4.0 |

.gitignore uses `data/*` with `!data/papers.jsonl`. A plain `data/` line would ignore the folder and the exception would not work.

Cloud storage (Google Cloud Storage) only when deploying a demo. Publishing the final dataset on Hugging Face or Zenodo, not the raw papers.

---

## 8. Parsing (parse_papers.py)

Uses Python's built-in xml.etree, no extra install.

For each paper it keeps:
- title and abstract
- each top-level section with heading, a label (methods / results / introduction / conclusion / other) and text
- every table as label, caption and rows

Decisions:
- Section labels come from the heading and the sec-type attribute. Methods is checked first, because "Materials and Methods" also contains words that could match results.
- Tables are stored separately and removed from the section text, so a value does not appear twice.
- Tables are read before sections, because removing them from the text would otherwise lose them.
- Paper metadata from papers.jsonl is merged into each processed file.

Result: 300 parsed, 0 errors, 1,022 tables (3.4 per paper), 4 papers (1.3%) with no detectable methods section. To check during labelling whether those use an unusual heading.

---

## 9. Schema (schema.py)

### 9.1 Purpose

One definition used in three places:
- the format the LLM must fill in (Gemini structured output)
- the format the gold set is labelled in
- automatic validation, so bad extractions are rejected

### 9.2 Structure

```
PaperExtraction (one per paper)
  in_scope, out_of_scope_reason, intended_application
  process_steps[]      shared procedure; applies_to limits a step to some recipes
  recipes[]            one per film formulation, including the control
    ingredients[]
    properties[]
  best_recipes[]       only what the authors say performed best
every ingredient, step, property and best recipe has a source: section or table + exact quote
```

### 9.3 Principles

1. Provenance on everything. Every value has a source with an exact quote, so code can check the quote really exists in the paper. This is how invented values get caught. Page numbers were in the original plan but XML has no pages, and a quote is checkable anyway.
2. Keep what the paper said next to our label: name + name_reported, unit as written, description.
3. Fixed vocabularies with an escape hatch ("other", "unknown"), so data is consistent without forcing wrong labels.
4. The LLM extracts, code derives. Unit conversion and recipe grouping happen afterwards in code, where they can be tested.
5. Comparability built in: basis of amounts, test conditions, control flag.
6. Missing is better than guessed. Most fields are optional; unclear basis or origin is "unknown".
7. Validation rules catch nonsense automatically.

### 9.4 Vocabularies from the corpus

The first lists were drafted from domain knowledge. Then I counted how many of the 300 papers mention each candidate term (notebooks/vocab_check.py).

Properties (papers mentioning):

| Property | Papers |
|---|---|
| tensile strength | 271 (90%) |
| thickness | 266 (89%) |
| elongation at break | 235 (78%) |
| antimicrobial activity | 213 (71%) |
| opacity / transparency | 202 (67%) |
| water vapour permeability | 196 (65%) |
| thermal (TGA/DSC) | 173 (58%) |
| moisture content | 154 (51%) |
| water solubility | 152 (51%) |
| swelling / water uptake | 143 (48%) |
| colour (L*a*b*) | 124 (41%) |
| antioxidant activity | 123 (41%) |
| Young's modulus | 117 (39%) |
| contact angle | 87 (29%) |
| oxygen permeability | 74 (25%) |
| biodegradation | 48 (16%) |

Steps (papers mentioning in methods):

| Step | Papers |
|---|---|
| filtration | 160 (53%) |
| homogenising | 134 (45%) |
| centrifugation | 124 (41%) |
| sonication | 116 (39%) |
| CaCl2 crosslinking | 84 (28%) |
| degassing | 72 (24%) |
| neutralising / pH adjustment | 29 (10%) |

Rule: a term gets its own label if it appears in at least 20% of papers, or it matters to Materiom regardless (biodegradation kept at 16% because end of life is central to their work). Neutralisation stays "other" at 10%; the ph field still records the value.

Counts are an upper bound: a mention in an introduction is not a measurement.

What the counts showed:
- 7 common properties were missing from the first draft and would have become "other".
- Antimicrobial at 71% confirms the corpus leans towards active packaging.
- Filtration and centrifugation are mostly used to prepare additives (extracts, nanoparticles), not the film. This led to the stage field.
- Thermal analysis gives several temperatures, so it is split into glass transition, melting and degradation temperature.
- Colour is one label; L*, a*, b*, ΔE are separate entries told apart by name_reported.

### 9.5 Fields added and why

| Field | Where | Why | Example |
|---|---|---|---|
| stage | ProcessStep | separate making an additive, making the film, and treatment after drying | clove oil emulsion = ingredient_preparation; CaCl2 bath = post_treatment |
| test_details | Property | some values mean nothing without the organism or assay | "E. coli, disc diffusion", "DPPH" |
| ph_adjuster | Role | acetic acid dissolves chitosan; it is not really a solvent | acetic acid 1% |
| feedstock, from_waste | Ingredient | what an ingredient was made from, and whether it is a waste stream; central to Materiom | chitosan from lobster shell waste |
| best_recipes (list) | PaperExtraction | papers often name a different best film per property | F3 highest tensile strength, F5 lowest WVP |
| n_samples | Property | a ± value means more from 10 specimens than from 3 | n = 5 |
| intended_application | PaperExtraction | Materiom cares about the application | "fresh-cut fruit packaging" |
| duration_value + duration_unit | ProcessStep | store what the paper says; convert in code | 24 + "h", not 1440 |
| applies_to | ProcessStep | some papers vary the process, not only the ingredients | see 9.6 |

origin (bio-based / mineral / synthetic) and from_waste are separate fields. A bio-based ingredient is not necessarily waste-derived.

### 9.6 Process variation: applies_to

Problem: steps are shared by every film in a paper, which works when films only differ in ingredients. Some papers vary the process:
- a step changed: F1 dried at 40 °C, F2 at 60 °C
- a step added for some films: only F2 and F3 sonicated
- a step left out: the alginate control is not dipped in CaCl2

Without this, a control and a crosslinked film with the same ingredients would look like the same recipe with very different tensile strength (e.g. 18 vs 42 MPa). Grouping would report that as natural variation, RAG could not answer "what does CaCl2 crosslinking do?", and the export would tell someone to crosslink a film that never was.

Options compared:

| Option | changed | added | left out | duplication | labelling effort |
|---|---|---|---|---|---|
| step_changes per recipe | yes | yes | no | low | medium |
| full steps in every recipe | yes | yes | yes | high | high |
| applies_to on shared steps | yes | yes | yes | none | low |

Chosen: applies_to. A list of recipe codes on a step; empty means it applies to every recipe. One optional field covers all three cases. If the LLM misses it, the step applies to all films, which is the same as not having the field, so it cannot make results worse.

Example, control not crosslinked:

```json
{"order": 5, "stage": "post_treatment", "type": "crosslinking",
 "description": "Immersed in 2% CaCl2", "applies_to": ["F1", "F2", "F3"]}
```

steps_for(code) rebuilds one recipe's full procedure: shared steps plus steps listing that code, sorted by order.

### 9.7 Duration as reported

The first version asked the LLM to convert "24 h" to 1440 minutes. That is a derived value made by the LLM and breaks principle 4. Changed to duration_value + duration_unit (s, min, h, day), converted in code. Temperature stays as temperature_c because papers almost always use °C.

### 9.8 Validation rules

- a property must have a value or a range
- value_min cannot be larger than value_max
- a duration needs both value and unit
- out of scope needs a reason; in scope must not have one
- every code in applies_to and best_recipes must be a real recipe
- values outside a fixed vocabulary are rejected (e.g. role "binder")

9 tests in tests/test_schema.py, all passing.

### 9.9 Not stored in the schema

| Not stored | Why |
|---|---|
| DOI, journal, year, licence, family | already in papers.jsonl, joined by PMCID |
| converted units, recipe signature | derived later in code |
| food shelf-life results | about the food, not the material |
| values in figures | non-goal for the MVP |

### 9.10 Considered and not done

| Idea | Decision | Why |
|---|---|---|
| separate transparency vs opacity, water absorption vs swelling | deferred | authors use them loosely; finer labels lower agreement between me and the LLM. name_reported and unit keep the difference; can split later in code |
| more step types (stirring, cooling, washing, freeze-drying, neutralisation) | deferred | add only what reaches the 20% rule; stirring is part of most mixing steps; freeze-drying is mostly for foams |
| mean / single / range field | not done | ranges already have their own fields; papers almost always report mean ± SD |
| reported / inferred flag on every field | not done | roughly doubles the schema and an LLM's own judgement of "inferred" is unreliable. The quote shows the evidence, "unknown" defaults discourage guessing, evals measure accuracy |
| author-picked vs calculated best | not needed | the schema only stores author claims; anything calculated is done later in code |

Test used for any new field: will it be used, can it be labelled consistently, is it common enough to matter. Each field costs LLM accuracy and labelling time.

The schema is frozen until the gold set shows a real gap.

---

## 10. Same recipe in several papers

Common (e.g. potato starch + glycerol). Treated as useful: several labs measuring the same recipe gives a range instead of one number.

- Same recipe in different studies: keep each record, group later by a normalised recipe signature, report range and number of papers.
- Same study counted twice: remove.
- Answers should say "1 study" vs "7 studies" so a single result does not look as solid as a replicated one.
- Grouping needs ingredient names, amount basis and starch source normalised first. Planned for week 3, after extraction.

---

## 11. Gold set (next)

- 15 papers at random, 5 per family (seed 7)
- per family: 3 dev (used to improve the prompt), 2 test (held out until the final run)
- labelled before writing any LLM prompt, so the labels are not shaped by the prompt
- random means some may be out of scope; those are labelled in_scope false with a reason, which tests that part too
- one function, paper_as_text(), produces the text I label from, the text the LLM will read, and the text quotes are checked against
- validate_gold.py checks each label against the schema and checks every quote exists in the paper
- start with 3 papers to measure my real pace (estimate 30-60 min per paper), then decide on 15 or fewer

Labelling rules:
1. one recipe per film formulation, including the control
2. quotes copied exactly from the .md file, short; table rows with | separators
3. not stated = null; unclear basis or origin = "unknown"
4. values as reported (24 + "h"); units as written
5. properties of the film only, not of the food it was tested on
6. best_recipes only when the authors say so

---

## 12. Stack

| Part | Tool | Why |
|---|---|---|
| schema and validation | Pydantic | Gemini accepts a Pydantic schema for structured output; named in Materiom's job ad |
| extraction | Gemini Python SDK directly | one call per paper; a framework adds layers and makes debugging harder |
| RAG flow | LangGraph | retrieve, generate, check numbers, abstain if the check fails: a flow with a branch. Named in the job ad. Build a plain Python version first |
| LangChain | small parts only if useful (e.g. text splitters) | not the whole framework |
| records | SQLite | single file, no server |
| passages for RAG | Chroma | local vector store |
| tests | pytest | unit tests for code; data checks kept separate |

Training or fine-tuning a model is not part of this. The LLM reads papers (extraction) and answers from retrieved records (RAG). Training would blur facts and lose the link to sources, the same problem Materiom AI has.

---

## 13. Known biases (for the data card)

From the search:
- open-access and licence skew: OA publishers (MDPI, Frontiers) over-represented; big subscription journals thin; all 300 are CC BY
- Europe PMC is life-science focused; food and biomedical journals well covered, pure materials journals less
- English-only keywords; papers saying "coating", "sheet" or "thermoplastic starch" may be missed
- the property gate excludes papers that only report biodegradation or only describe look and feel
- the corpus leans towards active packaging (antimicrobial in 71% of papers)

From what gets published:
- positive results: failed recipes are rarely published, so values look better than real experience
- recipe clustering: many papers test glycerol at 20/30/40%, few test unusual recipes
- research concentrated in a few countries with their local feedstocks
- recent papers dominate because the field has grown
- test methods and conditions differ between papers

From the pipeline:
- values only in figures are lost, so papers with tables are favoured
- extraction will be more accurate on tables than long text
- sampled equally per family, not in proportion to the literature

To report: papers by journal, year and family, plus these points.

---

## 14. Related work

| Work | What it does | Gap |
|---|---|---|
| Materiom Commons | community recipe library | properties often without test method or source |
| Future Materials Bank, Koynē, Biomaterials Library Lithuania | design-focused material libraries | little measured, sourced data |
| Polymer Scholar (Georgia Tech, 2023) | ~300k polymer property records from abstracts | abstracts only; authors state processing and measurement conditions are not captured |
| ChemDataExtractor (Cambridge) | auto-generated property databases | properties, not recipes; not bio-based films |
| text-mined synthesis recipes (Berkeley/MIT) | recipes for inorganic materials | inorganic only |
| Dagdelen et al. 2024 | LLM structured extraction for materials | general method, not a dataset for this domain |
| Materiom AI | Gemini chatbot with literature retrieval | my tests: wrong material cited, inconsistent answers, no database recipes |

I did not find an open tool that combines full-text recipe extraction, test conditions and per-value sources for bio-based films. Searched widely but not exhaustively, so I do not claim it is the first.

---

## 15. What testing Materiom AI showed

| Test | Result |
|---|---|
| potato starch film, 30% glycerol, with citations | cited a corn starch paper; said no tensile value exists although the cited paper tests 30% glycerol |
| 3 alginate recipes from the Materiom database | generic recipes with round amounts, no recipe IDs or links |
| chitosan WVP with and without citric acid | claimed a consistent reduction; studies actually split three ways |
| same question as test 1 in a new chat | different numbers and different references; 1 of 3 references accurate |
| fields of a Materiom recipe | generic structure, did not match the real record |
| "what sources do you use?" | answered from a paper about another search engine (BASE) |

The last one shows it answers from whatever retrieval returns, even a poor match. My RAG layer must abstain when the best match is weak and answer "what sources do you use" from a fixed description of the corpus.

---

## 16. Timeline

Planned 3 weeks; now about 4. Week 1 took longer because time went into query design, bias checks and finding the duplicates.

| Week | Dates | Goal | Status |
|---|---|---|---|
| 1 | 19-25 Oct | corpus | done: 300 papers listed, downloaded, parsed |
| 2 | 26 Oct-1 Nov | schema, gold set, model choice | schema done; gold set next |
| 3 | 2-8 Nov | extraction on all papers, scored on gold set | |
| 4 | 9-15 Nov | RAG, comparison with Materiom AI, README, report | |

If week 3 slips, the RAG layer becomes a retrieval-only demo. Extraction quality is not cut.

---

## 17. Open items

- check headings of the 4 papers with no methods section
- check year distribution of the 300 papers (data card, and whether year sampling is needed)
- confirm Materiom Commons step types beyond Grinding, Mixing, Drying, Other
- ask Materiom whether they have an import format for new records
- choose extraction model after a 5-paper comparison
- add check_data.py (duplicate, licence, missing-file and broken-XML checks)

---

## Change log

| Date | Change | Reason |
|---|---|---|
| 21 Oct | repo set up: Python template .gitignore, MIT licence | |
| 22 Oct | 8 families → 3 | match Materiom AI tests, manageable gold set, comparable films |
| 22 Oct | broadened film words; added property gate | exact phrase found only 38 alginate papers |
| 22 Oct | added BIOMED + PACKAGING (approach C) | ~50% of chitosan/alginate hits were medical |
| 22 Oct | added SYNTHETIC, NOT_CAST, REVIEW | found by reading titles |
| 22 Oct | kept narrow property gate | wide gate added only 9-17% after filters |
| 22 Oct | random sample with seed, not top results | API ranking leans to recent active packaging |
| 22 Oct | year sampling parked | recency is partly real; check after download |
| 24 Oct | raw data kept locally | small and regenerable |
| 25 Oct | 80 → 100 papers per family | more room for papers dropped later |
| 25 Oct | deduplicate within family | 300 entries but only 263 unique papers |
| 25 Oct | .gitignore: data/* and !data/papers.jsonl | data folder was not ignored |
| 25 Oct | schema v1 | structure and principles |
| 25 Oct | vocabularies rebuilt from corpus counts; stage, test_details, ph_adjuster | first draft missed 7 common properties |
| 25 Oct | feedstock, from_waste, best recipe | origin of materials and authors' best film were missing |
| 25 Oct | applies_to, duration as reported, n_samples, best_recipes list, intended_application, scope consistency, code checks | process variation; LLM should not derive values; review of the design |
| 25 Oct | schema frozen until gold set | |