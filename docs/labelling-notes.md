# Labelling notes

Rules for the gold set, and decisions on individual papers. Follow these for every label so the 15 papers are consistent.

## V1 scope

One recipe per paper: the formulation the authors say performed best.

- Use the film the authors call best or optimised.
- If they name different bests for different properties, use the one in their main claim (abstract or conclusion), and put the criterion in best_recipes.
- If no best is named, use the formulation whose results the abstract highlights.
- is_control is false. If the paper states the improvement over the control, mention it in description.
- Process steps: only the steps used for that film. No applies_to.
- Out-of-scope papers: in_scope false, a reason, nothing else.

## Fields

Core, always labelled:
in_scope, out_of_scope_reason, recipe code / description / is_control / base_polymers,
ingredient name / role / amount / unit / basis, property name / name_reported / value / std_dev / unit,
every source quote.

Secondary, only when clearly stated, otherwise null:
process steps, test_standard, test_details, rh_pct, temperature_c, n_samples,
origin, feedstock, from_waste, intended_application.

## General rules

1. Quotes copied exactly from the .md file, short. Table rows keep the | separators.
2. Not stated = null. Unclear basis or origin = "unknown".
3. Values as reported: 24 + "h", units as written.
4. Properties of the film only, not of the food it was tested on.
5. Values only shown in figures are skipped.
6. Ranges that cover several films are skipped.
7. best_recipes only when the authors say so.
8. Control = the film the authors compare against, usually the same film without the additive being tested. Plastic films are never a recipe.
9. Test conditions on properties (rh_pct, temperature_c) come from the method sentence for that test.
10. Amounts: use the table's own units when every film has them (e.g. grams per 100 mL).
11. Origin: go by what the paper says (e.g. glycerol described as synthetic).
12. The ± value goes in std_dev even when the paper says it is standard error; note it below.

## Paper decisions

### PMC13025781 (alginate, dev)
- Best film: SA2.5 − G1y − MAX1.5, "highest tensile strength".
- Values from Table 2: 6.63 ± 0.06 MPa and 96.4 ± 9.9 %. Table 2 labels