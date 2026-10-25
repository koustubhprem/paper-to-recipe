from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

# allowed values for each labelled field; "other"/"unknown" catch anything that doesn't fit

# what an ingredient does in the film
Role = Literal[
    "matrix", "plasticizer", "crosslinker", "filler", "active_agent",
    "emulsifier", "solvent", "ph_adjuster", "other",
]
# what an amount is measured against
Basis = Literal[
    "g", "ml", "pct_w_v", "pct_v_v", "wt_pct_of_polymer", "wt_pct_of_total",
    "other", "unknown",
]
# what kind of material an ingredient is
Origin = Literal["bio_based", "mineral", "synthetic", "unknown"]
# which part of the procedure a step belongs to
Stage = Literal["ingredient_preparation", "film_formation", "post_treatment"]
# kind of processing step
StepType = Literal[
    "grinding", "dissolving", "mixing", "heating", "homogenising", "sonicating",
    "filtering", "centrifuging", "degassing", "casting", "drying",
    "crosslinking", "conditioning", "other",
]
# time units as written in papers; converted to minutes later in code
TimeUnit = Literal["s", "min", "h", "day"]
# measured properties, chosen from term counts across the corpus
PropertyName = Literal[
    "tensile_strength", "elongation_at_break", "youngs_modulus", "thickness",
    "water_vapour_permeability", "oxygen_permeability", "water_solubility",
    "moisture_content", "swelling", "contact_angle", "opacity", "colour",
    "glass_transition_temperature", "melting_temperature", "degradation_temperature",
    "antimicrobial_activity", "antioxidant_activity", "biodegradation", "other",
]
# reasons a paper is excluded after reading it
OutOfScope = Literal[
    "review", "not_solution_cast", "coating_only", "medical",
    "no_measured_properties", "other",
]


# where a value was found, with an exact quote so it can be checked later
class Source(BaseModel):
    section: Literal["abstract", "methods", "results", "other", "table"]
    table_label: Optional[str] = Field(None, description="e.g. 'Table 2', only if section is 'table'")
    quote: str = Field(description="exact text from the paper, max 200 characters")


# one ingredient of a film, with its amount as reported and what it was made from
class Ingredient(BaseModel):
    name: str = Field(description="as written in the paper")
    role: Role
    amount: Optional[float] = None
    unit: Optional[str] = Field(None, description="as written, e.g. 'g', '% w/v', 'wt%'")
    basis: Basis = "unknown"
    origin: Origin = "unknown"
    feedstock: Optional[str] = Field(None, description="what it was made from, as written, e.g. 'shrimp shell', 'brown seaweed', 'avocado seed'")
    from_waste: Optional[bool] = Field(None, description="true if the paper says it comes from a waste or by-product stream")
    source: Source


# one step of the procedure, with duration kept as reported
class ProcessStep(BaseModel):
    order: int
    stage: Stage = Field("film_formation", description="ingredient_preparation for extracts, emulsions or nanoparticles made before the film; post_treatment for steps after drying, e.g. a CaCl2 bath")
    type: StepType
    description: str
    temperature_c: Optional[float] = None
    duration_value: Optional[float] = None
    duration_unit: Optional[TimeUnit] = None
    ph: Optional[float] = None
    applies_to: list[str] = Field([], description="recipe codes this step applies to; leave empty if it applies to every recipe")
    source: Source

    # a duration needs both its number and its unit
    @model_validator(mode="after")
    def duration_complete(self):
        if (self.duration_value is None) != (self.duration_unit is None):
            raise ValueError("duration_value and duration_unit must be given together")
        return self


# one measured value of a film, with its test conditions
class Property(BaseModel):
    name: PropertyName
    name_reported: str = Field(description="as written, e.g. 'TS', 'WVP', 'L*'")
    value: Optional[float] = None
    value_min: Optional[float] = None
    value_max: Optional[float] = None
    std_dev: Optional[float] = None
    n_samples: Optional[int] = Field(None, description="number of specimens tested, if stated")
    unit: str = Field(description="as written, e.g. 'MPa', 'g·mm/m²·day·kPa'")
    test_standard: Optional[str] = Field(None, description="e.g. 'ASTM D882'")
    test_details: Optional[str] = Field(None, description="e.g. 'E. coli, disc diffusion', 'DPPH', 'soil burial 30 days'")
    rh_pct: Optional[float] = None
    temperature_c: Optional[float] = None
    source: Source

    # reject properties with no number, or a range where min > max
    @model_validator(mode="after")
    def has_a_value(self):
        if self.value is None and self.value_min is None and self.value_max is None:
            raise ValueError("property needs a value or a range")
        if self.value_min is not None and self.value_max is not None and self.value_min > self.value_max:
            raise ValueError("value_min is larger than value_max")
        return self


# one film formulation tested in the paper, e.g. each glycerol level
class Recipe(BaseModel):
    code: str = Field(description="the paper's label for this film, e.g. 'F1', 'CS-G30', 'control'")
    description: str
    is_control: bool
    base_polymers: list[str] = Field(description="e.g. ['potato starch'] or ['chitosan', 'pectin']")
    ingredients: list[Ingredient]
    properties: list[Property]


# a formulation the authors themselves say performed best, and at what
class BestRecipe(BaseModel):
    code: str = Field(description="must match the code of one of the recipes")
    criterion: str = Field(description="what it was best at, as stated, e.g. 'highest tensile strength'")
    source: Source


# everything extracted from one paper
class PaperExtraction(BaseModel):
    in_scope: bool
    out_of_scope_reason: Optional[OutOfScope] = None
    intended_application: Optional[str] = Field(None, description="as stated, e.g. 'fresh-cut fruit packaging'")
    # shared procedure; a step with applies_to set is only used for those recipes
    process_steps: list[ProcessStep] = []
    recipes: list[Recipe] = []
    best_recipes: list[BestRecipe] = []

    # in_scope and out_of_scope_reason must agree
    @model_validator(mode="after")
    def scope_consistent(self):
        if not self.in_scope and self.out_of_scope_reason is None:
            raise ValueError("out_of_scope_reason is required when in_scope is false")
        if self.in_scope and self.out_of_scope_reason is not None:
            raise ValueError("out_of_scope_reason must be empty when in_scope is true")
        return self

    # every recipe code used in steps or best_recipes must exist
    @model_validator(mode="after")
    def codes_exist(self):
        codes = {r.code for r in self.recipes}
        for step in self.process_steps:
            unknown = set(step.applies_to) - codes
            if unknown:
                raise ValueError(f"step {step.order} applies_to unknown recipes: {sorted(unknown)}")
        for best in self.best_recipes:
            if best.code not in codes:
                raise ValueError(f"best_recipes code '{best.code}' is not one of the recipes")
        return self

    # the full procedure for one recipe: shared steps plus the ones meant for it
    def steps_for(self, code):
        return sorted(
            (s for s in self.process_steps if not s.applies_to or code in s.applies_to),
            key=lambda s: s.order,
        )