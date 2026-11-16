# Results

## Setup

- Model: gemini-3.8-flash, default temperature
- Prompt: v3 (rules in the system instruction, one invented example, every schema field required)
- Papers: 9 dev papers from the gold set (8 in scope, 1 out of scope)
- Graded by hand against the gold labels, using the rules below

## Dev results, prompt v3

| Category | Gold | Gemini | Matched | Recall / accuracy | Precision |
|---|---|---|---|---|---|
| in_scope | 9 | 9 | 9 | 1.00 | |
| best film | 9 | 9 | 9 | 1.00 | |
| chosen_by (in-scope papers) | 8 | 8 | 7 | 0.88 | |
| base polymers | 15 | 16 | 15 | 1.00 | 0.94 |
| ingredients | 44 | 43 | 43 | 0.98 | 1.00 |
| ingredient fields | 215 | 215 | 203 | 0.94 | |
| steps | 80 | 73 | 75 | 0.94 | 1.00 |
| step fields | 225 | 225 | 208 | 0.92 | |
| properties | 73 | 74 | 73 | 1.00 | 0.99 |
| property fields | 219 | 219 | 209 | 0.95 | |

Counts are added up across papers first, then divided.

## Per paper

| Paper | Film | chosen_by | Ingredients | Ingredient fields | Steps | Step fields | Properties | Property fields |
|---|---|---|---|---|---|---|---|---|
| PMC13025781 | ok | ok | 5/5 | 25/25 | 7/7 | 21/21 | 12/12 | 36/36 |
| PMC10934414 | ok | ok | 5/5 | 25/25 | 7/7 | 20/21 | 6/6 | 18/18 |
| PMC10422339 | ok | ok | 9/9 | 42/45 | 12/12 | 31/36 | 9/9 | 27/27 |
| PMC11083475 | ok | ok | 7/7 | 35/35 | 9/9 | 25/27 | 14/14 | 41/42 |
| PMC7558937 | out of scope, ok | | | | | | | |
| PMC7281565 | ok | ok | 3/3 | 12/15 | 7/8 | 20/21 | 10/10 | 27/30 |
| PMC13610544 | ok | ok | 8/9 | 39/40 | 14/14 | 38/42 | 15/15 | 44/45 |
| PMC11241157 | ok | aim vs default | 3/3 | 11/15 | 12/15 | 35/36 | 1/1 | 1/3 |
| PMC11717021 | ok | ok | 3/3 | 14/15 | 7/8 | 18/21 | 6/6 | 15/18 |

Items are shown as found / in gold. Fields are shown as correct / compared.

## How it was graded

- Only the best recipe of each paper is graded.
- Best film: codes match after ignoring spaces, case and dash style.
- If the film is wrong, the rest of the paper is not graded.
- Ingredients match if they are the same substance, steps if they are the same action from the same sentence, properties if they are the same measurement.
- Recall = found / in gold. Precision = correct / given by Gemini.
- Fields graded on matched items: ingredient amount, unit, role, basis, origin; step type, duration, temperature; property value, std_dev, unit.
- Numbers must be equal as written. Units ignore spacing and formatting.
- An empty unit and "dimensionless" count as equal.
- If the paper gives two values for the same thing, either value counts.
- A Gemini step that covers several gold steps (merge), or several Gemini steps for one gold step (split), counts as found. Lost conditions count as field errors.
- An extra item that is correct under the labelling rules counts as gold missed: it is added to gold and counts as correct.

Not graded: descriptions, criterion, name_reported, test details, test standard, intended application, step order, gaps.

## Gold fixes made during grading

| Paper | Fix |
|---|---|
| PMC13025781 | one property added (gold missed) |
| PMC11083475 | DPPH and ABTS added (Figure 4 confirms they are EDCA3's); glycerol origin unknown; NaOH and HCl unit "to pH ..." with basis other, as in the example |
| PMC7281565 | glycerol origin unknown; ferulic acid origin to check |
| PMC13610544 | peel washing step added; DPPH range replaced by the four Table 5 values; IC50 added; glycerol origin unknown |
| PMC11241157 | acetic acid origin unknown |

## Error patterns

| Pattern | Papers |
|---|---|
| Powers of ten moved into the value (4.37E-19 instead of 4.37 with × 10−19 in the unit) | PMC7281565, PMC11241157, PMC11717021 |
| Preparation steps for the raw material missed | PMC7281565, PMC11241157, PMC11717021 |
| Steps merged, losing a temperature | PMC10422339, PMC13610544 |
| "dimensionless" written where the paper gives no unit | PMC10422339, PMC11083475, PMC7281565, PMC13610544 |
| n_samples taken from points measured on one film | PMC13025781, PMC10422339, PMC11083475 |
| Tween 80 origin not given as synthetic | PMC10422339, PMC13610544 |
| % w/w mapped to basis pct_w_v | PMC11241157 |
| Contradictions in the paper not listed as gaps | PMC11083475, PMC13610544 |

## Notes

- Gemini rarely adds anything it should not: item precision is 0.94 - 1.00.
- Most misses are preparation steps. Nothing critical as such in the data. Not critical because, anyways all the data is being captured and stored correctly in right steps.
- The power-of-ten conversion matters most for the data, because the same quantity would be stored two different ways across papers. Prompt v4 adds one line to rule 3 to fix it. This is somehting that is recurring but fixable