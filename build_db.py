import json
import sqlite3
from pathlib import Path

from schema import PaperExtraction

OUT_DIR = Path("data") / "extractions"
PAPERS_FILE = Path("data") / "papers.jsonl"
DB_PATH = Path("data") / "recipes.db"

TABLES = """
CREATE TABLE papers (
    pmcid TEXT PRIMARY KEY,
    title TEXT,
    doi TEXT,
    journal TEXT,
    year INTEGER,
    licence TEXT,
    family TEXT,
    in_scope INTEGER NOT NULL,
    out_of_scope_reason TEXT,
    intended_application TEXT,
    model TEXT,
    prompt_version TEXT,
    extracted_at TEXT
);

CREATE TABLE recipes (
    pmcid TEXT PRIMARY KEY REFERENCES papers(pmcid),
    code TEXT NOT NULL,
    description TEXT,
    is_control INTEGER,
    base_polymers TEXT,
    chosen_by TEXT,
    criterion TEXT,
    best_section TEXT,
    best_quote TEXT
);

CREATE TABLE ingredients (
    id INTEGER PRIMARY KEY,
    pmcid TEXT NOT NULL REFERENCES recipes(pmcid),
    position INTEGER,
    name TEXT,
    role TEXT,
    amount REAL,
    unit TEXT,
    basis TEXT,
    origin TEXT,
    feedstock TEXT,
    from_waste INTEGER,
    section TEXT,
    table_label TEXT,
    quote TEXT
);

CREATE TABLE steps (
    id INTEGER PRIMARY KEY,
    pmcid TEXT NOT NULL REFERENCES recipes(pmcid),
    step_order INTEGER,
    stage TEXT,
    type TEXT,
    description TEXT,
    temperature_c REAL,
    duration_value REAL,
    duration_unit TEXT,
    ph REAL,
    section TEXT,
    table_label TEXT,
    quote TEXT
);

CREATE TABLE properties (
    id INTEGER PRIMARY KEY,
    pmcid TEXT NOT NULL REFERENCES recipes(pmcid),
    name TEXT,
    name_reported TEXT,
    value REAL,
    value_min REAL,
    value_max REAL,
    std_dev REAL,
    n_samples INTEGER,
    unit TEXT,
    test_standard TEXT,
    test_details TEXT,
    rh_pct REAL,
    temperature_c REAL,
    section TEXT,
    table_label TEXT,
    quote TEXT
);

CREATE TABLE gaps (
    id INTEGER PRIMARY KEY,
    pmcid TEXT NOT NULL REFERENCES recipes(pmcid),
    gap TEXT
);

CREATE VIRTUAL TABLE search USING fts5(pmcid UNINDEXED, kind UNINDEXED, text);
"""

# fills the search index from the loaded tables; IFNULL keeps a missing value from blanking the whole text
SEARCH = """
INSERT INTO search (pmcid, kind, text)
    SELECT pmcid, 'paper', IFNULL(title, '') || ' ' || IFNULL(intended_application, '') FROM papers;
INSERT INTO search (pmcid, kind, text)
    SELECT pmcid, 'recipe', code || ' ' || IFNULL(description, '') || ' ' || IFNULL(criterion, '') || ' ' || IFNULL(best_quote, '')
    FROM recipes;
INSERT INTO search (pmcid, kind, text)
    SELECT pmcid, 'ingredient', IFNULL(name, '') || ' ' || IFNULL(role, '') || ' ' || IFNULL(feedstock, '') || ' ' || IFNULL(quote, '')
    FROM ingredients;
INSERT INTO search (pmcid, kind, text)
    SELECT pmcid, 'step', IFNULL(description, '') || ' ' || IFNULL(quote, '') FROM steps;
INSERT INTO search (pmcid, kind, text)
    SELECT pmcid, 'property', IFNULL(name_reported, '') || ' ' || IFNULL(value, '') || ' ' || IFNULL(unit, '') || ' ' || IFNULL(quote, '')
    FROM properties;
"""


# paper details from the search step (title, journal, year...), keyed by pmcid
def load_paper_info():
    if not PAPERS_FILE.exists():
        return {}
    with PAPERS_FILE.open(encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    return {row["pmcid"]: row for row in rows}


def insert_paper(conn, record, info):
    pmcid = record["pmcid"]
    ex = PaperExtraction.model_validate(record["extraction"])

    conn.execute(
        """INSERT INTO papers (pmcid, title, doi, journal, year, licence, family, in_scope,
                               out_of_scope_reason, intended_application, model, prompt_version, extracted_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (pmcid, info.get("title"), info.get("doi"), info.get("journal"), info.get("year"),
         info.get("licence"), info.get("family"), ex.in_scope, ex.out_of_scope_reason,
         ex.intended_application, record.get("model"), record.get("prompt_version"), record.get("extracted_at")),
    )
    if not ex.in_scope:
        return

    # only the best recipe is stored; pmcid is its key, so a paper can have only one recipe
    best = ex.best_recipes[0]
    recipe = next(r for r in ex.recipes if r.code == best.code)
    conn.execute(
        """INSERT INTO recipes (pmcid, code, description, is_control, base_polymers,
                                chosen_by, criterion, best_section, best_quote)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (pmcid, recipe.code, recipe.description, recipe.is_control, "; ".join(recipe.base_polymers),
         best.chosen_by, best.criterion, best.source.section, best.source.quote),
    )

    for position, ing in enumerate(recipe.ingredients, start=1):
        conn.execute(
            """INSERT INTO ingredients (pmcid, position, name, role, amount, unit, basis, origin,
                                        feedstock, from_waste, section, table_label, quote)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (pmcid, position, ing.name, ing.role, ing.amount, ing.unit, ing.basis, ing.origin,
             ing.feedstock, ing.from_waste, ing.source.section, ing.source.table_label, ing.source.quote),
        )

    for step in ex.steps_for(best.code):
        conn.execute(
            """INSERT INTO steps (pmcid, step_order, stage, type, description, temperature_c,
                                  duration_value, duration_unit, ph, section, table_label, quote)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (pmcid, step.order, step.stage, step.type, step.description, step.temperature_c,
             step.duration_value, step.duration_unit, step.ph, step.source.section,
             step.source.table_label, step.source.quote),
        )

    for prop in recipe.properties:
        conn.execute(
            """INSERT INTO properties (pmcid, name, name_reported, value, value_min, value_max, std_dev,
                                       n_samples, unit, test_standard, test_details, rh_pct, temperature_c,
                                       section, table_label, quote)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (pmcid, prop.name, prop.name_reported, prop.value, prop.value_min, prop.value_max,
             prop.std_dev, prop.n_samples, prop.unit, prop.test_standard, prop.test_details, prop.rh_pct,
             prop.temperature_c, prop.source.section, prop.source.table_label, prop.source.quote),
        )

    for gap in recipe.gaps:
        conn.execute("INSERT INTO gaps (pmcid, gap) VALUES (?, ?)", (pmcid, gap))


def main():
    files = sorted(OUT_DIR.glob("PMC*.json"))
    if not files:
        print(f"no extractions found in {OUT_DIR}")
        return
    info = load_paper_info()

    # rebuilt from scratch every run, so it always matches the extraction files
    DB_PATH.unlink(missing_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(TABLES)

    # one transaction: either every paper is loaded or none is
    with conn:
        for path in files:
            record = json.loads(path.read_text(encoding="utf-8"))
            insert_paper(conn, record, info.get(record["pmcid"], {}))

    # fill the search index from the tables just loaded
    conn.executescript(SEARCH)

    for table in ["papers", "recipes", "ingredients", "steps", "properties", "gaps", "search"]:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table:<12} {count}")
    conn.close()
    print(f"\nsaved {DB_PATH}")


if __name__ == "__main__":
    main()