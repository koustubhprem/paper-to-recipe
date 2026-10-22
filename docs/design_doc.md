# Design notes: corpus selection

## 1. Scope
Three material families, ~50 usable papers each (~150 total): papers on
solution-cast films for packaging or food that report measured properties.

## 2. Why starch, chitosan and alginate
- Widely used and heavily researched, so plenty of open-access papers.
- All polysaccharides made into films by similar casting methods and tested
  with the same standards, so their properties are comparable.
- They match the five Materiom AI test questions (potato starch, alginate,
  chitosan), which allows a head-to-head comparison.
- Keeps the hand-labelled gold set manageable (10 papers per family).
- Adding a family later is a one-line change in queries.py.

## 3. How we identify the right papers (queries.py)
Keep a paper only if:
- the family name AND a film word (film, membrane, bioplastic) are in the
  title/abstract, so the paper is mainly about that material as a film;
- it reports tensile strength, elongation at break or water vapour
  permeability anywhere in the text. This is a gate showing the paper
  measured something; extraction later captures all properties.
  A wider gate added only 9-17% more papers, so we kept it narrow;
- it mentions packaging, edible or food;
- it is open access with full text in Europe PMC;
- its licence is CC BY, CC BY-SA or CC0, so extracted data can be shared.

Exclude:
- Medical papers (wound, drug delivery, scaffold, tissue engineering):
  different application; ~50% of chitosan/alginate hits before filtering.
- Petroleum plastics in title/abstract (PBAT, PE, PP, PBS, PCL): not bio-based.
- Extruded, blown or moulded films: different process, so properties aren't
  comparable with cast films. Reversible later.
- Review papers: no original recipes, and they repeat other papers' results.

## 4. Sampling and bias (list_papers.py)
- API ranking bias: top results lean towards recent active-packaging papers.
  Fix: collect ALL matching papers, then pick 80 per family at random
  (seed 42, sorted first, so the sample is reproducible).
- 80 sampled to keep ~50 after full-text, licence and relevance checks.
- Blend papers (e.g. starch + chitosan) are only counted once.
- Equal numbers per family, not proportional to the literature.
- The year spread will lean recent because the field has grown (real, not
  an artefact). Year-based sampling is parked: check the year distribution
  after download and add it only if baseline films are missing.
- The paper list is saved in git (data/papers.jsonl), because Europe PMC
  changes daily and re-running the search would give a different set.

## Known biases (for the data card)
Open-access and CC-licence skew, Europe PMC's life-science focus,
English-only keywords, positive-results bias, recipe clustering
(e.g. glycerol at 20/30/40%), figures not digitised.