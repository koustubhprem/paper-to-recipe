import unittest
from pydantic import ValidationError
import pytest

from schema import PaperExtraction, ProcessStep, Property

SRC = {"section": "table", "table_label": "Table 2", "quote": "TS 5.1 ± 0.3 MPa"}
M = {"section": "methods", "quote": "from methods"}
raises = unittest.TestCase().assertRaises


# a valid paper: control + one glycerol film, control not crosslinked
def example():
    return {
        "in_scope": True,
        "intended_application": "food packaging",
        "process_steps": [
            {"order": 1, "type": "heating", "description": "Starch gelatinised",
             "temperature_c": 90, "duration_value": 30, "duration_unit": "min", "source": M},
            {"order": 2, "type": "drying", "description": "Dried",
             "temperature_c": 40, "duration_value": 24, "duration_unit": "h", "source": M},
            {"order": 3, "stage": "post_treatment", "type": "crosslinking",
             "description": "CaCl2 bath", "applies_to": ["G30"], "source": M},
        ],
        "recipes": [
            {"code": "G0", "description": "Control", "is_control": True,
             "base_polymers": ["potato starch"],
             "ingredients": [{"name": "potato starch", "role": "matrix", "source": SRC}],
             "properties": [{"name": "tensile_strength", "name_reported": "TS", "value": 12.4,
                             "unit": "MPa", "source": SRC}]},
            {"code": "G30", "description": "30% glycerol", "is_control": False,
             "base_polymers": ["potato starch"],
             "ingredients": [
                 {"name": "potato starch", "role": "matrix", "source": SRC},
                 {"name": "glycerol", "role": "plasticizer", "amount": 30, "unit": "%",
                  "basis": "wt_pct_of_polymer", "source": SRC},
             ],
             "properties": [{"name": "tensile_strength", "name_reported": "TS", "value": 5.1,
                             "std_dev": 0.3, "n_samples": 5, "unit": "MPa", "source": SRC}]},
        ],
        "best_recipes": [
            {"code": "G30", "criterion": "most flexible", "source": M},
        ],
    }


def test_valid_example():
    paper = PaperExtraction.model_validate(example())
    assert paper.recipes[1].properties[0].n_samples == 5


def test_steps_for_respects_applies_to():
    paper = PaperExtraction.model_validate(example())
    assert [s.type for s in paper.steps_for("G0")] == ["heating", "drying"]
    assert [s.type for s in paper.steps_for("G30")] == ["heating", "drying", "crosslinking"]


def test_applies_to_unknown_recipe_rejected():
    data = example()
    data["process_steps"][2]["applies_to"] = ["G99"]
    with raises(ValidationError):
        PaperExtraction.model_validate(data)


def test_best_recipe_must_exist():
    data = example()
    data["best_recipes"][0]["code"] = "G99"
    with raises(ValidationError):
        PaperExtraction.model_validate(data)


def test_duration_needs_unit():
    with raises(ValidationError):
        ProcessStep(order=1, type="drying", description="Dried", duration_value=24, source=M)


def test_property_needs_value():
    with raises(ValidationError):
        Property(name="tensile_strength", name_reported="TS", unit="MPa", source=SRC)


def test_range_order():
    with raises(ValidationError):
        Property(name="thickness", name_reported="thickness", value_min=0.2,
                 value_max=0.1, unit="mm", source=SRC)


def test_unknown_role_rejected():
    data = example()
    data["recipes"][0]["ingredients"][0]["role"] = "binder"
    with raises(ValidationError):
        PaperExtraction.model_validate(data)


def test_scope_must_be_consistent():
    with raises(ValidationError):
        PaperExtraction(in_scope=False)
    with pytest.raises(ValidationError):
        PaperExtraction(in_scope=True, out_of_scope_reason="review")
    assert PaperExtraction(in_scope=False, out_of_scope_reason="review").recipes == []