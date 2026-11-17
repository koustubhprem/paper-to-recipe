# paper-to-recipe

Use open-access research papers to create sustainable biomaterial recipes, so that tinkerers and anyone interested in the field can make their own materials based on research.

The pipeline reads papers on bio-based packaging films (starch, chitosan and alginate) and turns each one into a structured recipe: the authors' best film, its ingredients and amounts, the process steps, and the measured properties. Every value comes with the exact quote from the paper, so it can be checked.

## Status

| Stage | Status |
|---|---|
| Corpus: search, download and parse papers from Europe PMC | done |
| Schema for a recipe, with validation and tests | done |
| Gold set: 15 papers labelled by hand (9 dev, 6 test) | done |
| Extraction with Gemini | done (prompt v4 in progress) |
| Evaluation on dev papers | done |
| Evaluation on test papers | next |
| Full run on ~300 papers | planned |
| SQLite database and search | planned |
| Chat over the recipes (RAG) with citations | planned |

## Dev results

Gemini's output on 9 papers, checked by hand against my own labels.

| What was checked | Result |
|---|---|
| Picked the same best film as per gold label | 9 of 9 papers |
| Ingredients found | 98% |
| Process steps found | 94% |
| Properties found | 100% |
| Values correct (amounts, temperatures, property values…) | 94% (620 of 659) |
| Wrong items added that aren't in the paper's recipe | 1 of 206 |

Full results and how they were graded: [docs/results.md](docs/results.md).

## How it works

```
Europe PMC search -> download -> parse -> plain text -> Gemini -> validated JSON per paper
                                                              |
                                  gold labels (hand-made) -> evaluation
```

1. **Corpus.** `list_papers.py` searches Europe PMC for each material family and keeps open-access papers with a CC BY, CC BY-SA or CC0 licence. `download_papers.py` fetches the full-text XML and `parse_papers.py` splits it into sections and tables.
2. **Schema.** `schema.py` defines a recipe with Pydantic: scope, process steps, ingredients, properties, gaps and the best recipe. Fixed lists keep values consistent across papers (for example `tensile_strength`, `plasticizer`), and the paper's own wording is kept next to them.
3. **Extraction.** `extract.py` sends one whole paper to Gemini with the extraction rules, one invented example and the JSON schema, with every field required. The reply is saved raw, then validated, then saved with the model and prompt version.
4. **Evaluation.** The output is compared with hand-made gold labels for the best recipe: the film chosen, which items were found, and whether their values are right.

### Choosing the best recipe

Most papers don't say which film is best, so the best recipe is chosen by the first rule that applies, and the rule is recorded:

1. **stated**: the abstract or conclusion presents it as the best or recommended film
2. **abstract**: the abstract reports its values
3. **aim**: it best meets the paper's stated aim
4. **default**: the main new formulation, not the control

## Project layout

```
queries.py              search queries per material family
list_papers.py          build the paper list
download_papers.py      download full-text XML
parse_papers.py         split papers into sections and tables
papers_text.py          plain text of a paper, and the quote check
make_gold_dataset.py    pick the gold papers and write readable views
validate_gold.py        check gold labels against the schema and the paper text
schema.py               the recipe schema
extract.py              extract one paper with Gemini
json_to_excel.py        gold vs Gemini in Excel, one row per field
tests/                  schema tests
evals/gold/             gold labels and the dev/test split
evals/example.json      the invented example sent with every call
docs/                   labelling notes and results
```

## Setup (Windows)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create a `.env` file in the project root with your Gemini API key (it is ignored by git):

```
GEMINI_API_KEY=your-key-here
```

## Usage

```powershell
# build the corpus
python list_papers.py
python download_papers.py
python parse_papers.py

# check the schema and the gold labels
pytest
python validate_gold.py

# extract one paper
python extract.py PMC13025781

# compare gold and Gemini for the dev papers
python json_to_excel.py dev
```

Example output of `extract.py`:

```
PMC13025781: 48,210 characters, calling gemini-3.8-flash ...
PMC13025781: reply in 42 s, validating ...
PMC13025781  best: SA + Gly + MAX1.5 + CONE (aim)  5 ingredients, 7 steps, 12 properties, 2 gaps
```

## Limitations

- One recipe per paper: the best film only.
- Values shown only in figures are not extracted.
- Values are stored as written, without unit conversion.
- When papers contradict themselves, these are recorded as gaps.
- The gold set is small: 9 dev and 6 test papers.

## Licence

Code: MIT. Papers are used under their own Creative Commons licences.
