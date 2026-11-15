# Labelling notes

Rules for the gold set, and decisions on individual papers. Follow these for every label so the 15 papers are consistent.

## V1 scope

One recipe per paper: the formulation the authors say performed best, or the one the ladder below picks.

- is_control is false for the labelled film. If the paper states the improvement over the control, mention it in the description.
- Process steps: only the steps used for that film. No applies_to.
- Out-of-scope papers: in_scope false, a reason, nothing else.

## Scope

- In scope: a bio-based film for packaging, food contact or edible use, made by solution casting (tape casting included), with measured properties.
- Films used as supports, filters or carriers are out of scope (reason: other).
- coating_only is for liquid dip or spray papers with no cast film. A paper that casts and tests films before applying them is in scope.
- Blends with a synthetic biodegradable polymer (e.g. PVA) are in scope if bio-based polymers are the majority; the synthetic polymer gets origin "synthetic".
- Family tags are search groups. Record the real polymers in base_polymers.
- Incomplete recipes stay in scope. Gaps go in gaps, not a reason to exclude.

## Best recipe ladder

Stop at the first step that applies. Record the step in best_recipes.chosen_by.

1. stated: the authors present the film as their best, optimised or recommended outcome (abstract or conclusion).
2. abstract: the abstract reports one film's values.
3. aim: the film that best meets the paper's stated aim.
4. default: the main new formulation (not the control); if tied, the one with the most measured properties.

- "X had the highest Y" alone is not stated. It is stated only if the abstract or conclusion presents X as the outcome.
- A "best" chosen in a preliminary step (e.g. the best base before adding the active ingredient) is not the paper's best film. Use the aim step for the films built on it.
- If the paper names a best film and a separate best coating, label the film.
- A film that fails a safety test the paper itself runs (e.g. cytotoxic) is not picked by the aim step if a passing film exists.
- Criterion says what the film was best at and, for aim and default, why.
- Stepwise formulations (F3 = F2 + X): the best recipe includes every earlier formulation's ingredients and steps. Quote the "prepared as F2" link in the step for X.

## Fields

Core, always labelled:
in_scope, out_of_scope_reason, recipe code / description / is_control / base_polymers,
ingredient name / role / amount / unit / basis, property name / name_reported / value / std_dev / unit,
best_recipes code / criterion / chosen_by, every source quote.

Secondary, only when clearly stated, otherwise null:
process steps, test_standard, test_details, rh_pct, temperature_c, n_samples,
origin, feedstock, from_waste, intended_application, gaps.

## Ingredients

1. Only ingredients with a non-zero amount in the best film's own row of the formulation table. The methods often list ingredients for all films together.
2. Amounts as written. Never calculate, convert or add up. Use the table's own units when every film has them.
3. No amount stated: amount null. Ratios and ranges go in unit, as written.
4. wt% with no stated base: basis unknown. Dry basis: wt_pct_of_polymer.
5. A solution used as an ingredient is recorded as the solution amount, with its concentration in the name.
6. Water used in separate dispersions is listed once per dispersion.
7. Solvent not named: no solvent ingredient; add it to gaps.
8. Acid used to dissolve chitosan (acetic, citric, mucic, lactic): role ph_adjuster.
9. Origin as the paper states. Glycerol, sorbitol and acetic acid are unknown unless stated. Tween, NaOH, HCl, PVA and metal oxide nanoparticles are synthetic.
10. Feedstock and from_waste only for what the paper says about the material it used.
11. Ingredients made in this paper with the method described: add ingredient_preparation steps. Bought or made in earlier work: ingredient only.
12. CaCl2 used as a desiccant in a WVP cup is not an ingredient.

## Steps

1. Steps cover making the film and end at drying. Peeling, testing and applying the film to food are not steps.
2. Conditioning before a test is not a step.
3. Step order follows the order the paper writes the steps.
4. When the paper mentions the same action twice (a summary, then the detail), label it once, quoting the detail.
5. Actions in one sentence stay one step, unless each has its own conditions. Then split them.
6. Quotes come from the methods when the methods describe the step. A step whose conditions are only fixed in the results or conclusion may quote that section.
7. A step's type may come from the paragraph describing it. Its description and values come only from its quote.
8. A quote covers the description and every value in the step. Leave out purpose clauses.
9. Values with a step field (temperature, time, pH) go in the field. Values with no field (sieve size, rpm, pressure) go in the description.
10. temperature_c is the material's process temperature. Leave it out when the paper cannot say what the reading refers to.
11. Alternative methods with no stated choice: label only the shared steps and values. Quote only the shared part; it may be its own step.

## Properties

1. Only values stated in the text or a table. Figure-only values are skipped.
2. Relative statements ("26 times greater", "decreased by 17%") are not values. Ranges that cover several films are skipped.
3. "Above X" or "below X" stated in the text: value_min or value_max only.
4. Abstract and table disagree: use the table.
5. Properties of the film, not of the film-forming solution or extract. Measurements on coated food only when they measure the coating's stated function (e.g. decay incidence); not general fruit quality.
6. WVTR is not WVP: label WVTR as other. Moisture absorption from humid air is other, not moisture_content or swelling.
7. Significance letters (a, b) after values are ignored.
8. test_details holds only conditions that change the value. No instrument names.
9. Conditioning RH and temperature go on mechanical properties only, from the methods. Write where they came from in test_details. Other tests keep their own conditions.
10. n_samples is the number of specimens tested. Points measured on one specimen go in test_details.
11. TGA or DSC stages near 100 °C are water loss, not degradation.
12. Transposed tables (properties as rows, films as columns): prefer a text quote that names the film.
13. Units as written, including typos and missing units.
14. The ± value goes in std_dev even when the paper says it is standard error; note it below.

## Quotes

1. Copied exactly from the .md file, not retyped. Table rows keep the | separators.
2. Normally up to 200 characters. One longer quote is allowed when a step's values are spread over adjacent sentences.
3. Section "other" for the conclusion, introduction and anything outside abstract, methods, results and tables.
4. Copy recipe codes from the paper; some use Unicode dashes (‐) or extra spaces.

## Gaps

- Only what's needed to make the film: amounts, conditions, methods, sourcing.
- Not missing measurements. Not values a reader can work out from what's given (e.g. a ratio).
- Contradictions in amounts go in gaps, after converting to the same unit to check.
- A bought ingredient with a named supplier or specification is not a gap.

## Paper decisions

### PMC13025781 (alginate, dev)
- Best: SA2.5 − G1y − MAX1.5, stated: abstract calls it the optimized composition.
- Values from Table 2: 6.63 ± 0.06 MPa and 96.4 ± 9.9 %. The abstract says 6.88; used the table.
- MAX supplied by another lab; no preparation steps; gap for the product name.

### PMC10934414 (chitosan, dev)
- Best: Chit-MCC-Gly-MA, stated.
- Mechanical values in a figure only.

### PMC10422339 (starch, dev)
- Best: VCO 3 wt%, stated (lowest WVTR, summarised in the conclusion).
- NCC and VCO wt% base not stated.

### PMC11083475 (alginate, dev)
- Best: EDCA3, abstract.
- Methods say curcumin 2 mg/mL (0.2%), Table 1 says 0.03% w/v; used Table 1, gap added.
- Abstract WVP 1.67 contradicts Table 2 (1.25); used Table 2.

### PMC7558937 (chitosan, dev)
- Out of scope: chitosan–clay film used as a papain carrier for wine stabilisation. Matched the query on "food".

### PMC7281565 (starch, dev)
- Best: ferulic acid film, aim.
- Starch family but the film is corn fiber arabinoxylan.
- Table 5 says FA 10% w/w solution; methods and Tables 6–7 say dry basis; used dry basis.

### PMC13610544 (alginate, dev)
- Best: F3, stated ("most favourable visual preservation outcome overall").
- Pectin and extract both from orange peel waste. Degassed 15 mL vs cast 20 mL, as written.

### PMC11241157 (chitosan, dev)
- Best: SP_Chi, default. Comparison study with no named best.
- Chitosan family but pectin films (chitosan 20%). Most film data in figures.

### PMC11717021 (starch, dev)
- Best: CRG‐ST, stated.
- Carrageenan film with starch added. Starch level, glycerol and extraction method not stated.
- Extraction option A (water, blender, 95% ethanol) vs option B (0.01 M KOH, pure ethanol); only shared steps labelled.

### PMC9266268 (alginate, test)
- Best: AWA, stated.
- Apples dip-coated, but free films cast and tested, so in scope.
- Decay incidence on apples recorded as antimicrobial_activity; fruit quality left out.
- Solvent for the alginate not named.

### PMC13209360 (chitosan, test)
- Best: CS E, aim (highest antioxidant activity; antioxidant properties are the stated focus).
- Table 5 glycerol column mislabelled (% w/pdm header, g/100 mL values); used the methods.
- Vegetable glycerol: origin bio_based.

### PMC10379064 (starch, test)
- Best: G1.5_75, aim. G1.5 is the stated optimal base, not the paper's best film.
- "G2.5_75" (best coating) is not in any table.
- Which extract made the film is not stated; only the shared step labelled.
- Table 4 thickness has no unit.

### PMC10380360 (alginate, test)
- Best: CA-1, aim. Highest emission, and the title and conclusion present acid–base sensing as the purpose. Alternative CA-3 (ozonated oil, from the purpose sentence).
- Gels called 2% but amounts give about 4%; chitosan batch 2000 g vs 980 g.

### PMC8124804 (chitosan, test)
- Best: CSNF-F1, aim. Only film non-cytotoxic and more antifungal than the control; F3 has the highest antifungal activity but is cytotoxic.
- Chitosan made in-house from spider crab shell waste. "CS-based" basis undefined.

### PMC10978958 (starch, test)
- Best: PVA/ST/CS/NiO-CuONP 1%, stated.
- PVA:ST:CS 4:2:4 (40% synthetic PVA), in scope by majority rule. Contains NiO–CuO nanoparticles (nickel: food-contact concern).
- Recipe code written three ways. Glycerol listed in materials but not in the method.

## Not planned

Ideas noted while labelling. Not part of the current plan.


- Vocabulary: water_vapour_transmission_rate, moisture_absorption, compatibilizer, hydrophobic_agent, ph_adjusting, not_packaging, Source.section conclusion.
- Property.conditions_source, checked like other quotes.
- ProcessStep.alternative ("A"/"B") if alternative methods are common in the 300-paper run.
- Several sources per step, for values in non-adjacent sentences.
- Ingredient availability: commercial, made_in_paper, made_elsewhere.
- nano_type on ingredients: bio_nanofiller, inorganic_nanoparticle, nano_capsule.
- Normalised values next to the originals (WVP, thickness, amounts).
