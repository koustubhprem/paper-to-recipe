"""Final Europe PMC search query for the paper-to-recipe corpus."""

FAMILIES = ["starch", "chitosan", "alginate"]

# Must be about a film-like material
FILM = ("(TITLE_ABS:film OR TITLE_ABS:films "
        "OR TITLE_ABS:membrane OR TITLE_ABS:bioplastic)")

# Must report at least one measured property we care about
PROPS = ('("tensile strength" OR "elongation at break" '
         'OR "water vapor permeability" OR "water vapour permeability")')

# Must be about packaging or food
PACKAGING = "(packaging OR edible OR food)"

# Exclusions
BIOMED = ('(wound OR "drug delivery" OR "drug release" '
          'OR scaffold OR "tissue engineering")')
SYNTHETIC = ("(TITLE_ABS:PBAT OR TITLE_ABS:polyethylene OR TITLE_ABS:polypropylene "
             "OR TITLE_ABS:PBS OR TITLE_ABS:PCL)")
NOT_CAST = ('(TITLE_ABS:blown OR TITLE_ABS:extrusion OR TITLE_ABS:extruded '
            'OR TITLE_ABS:"injection molding" OR TITLE_ABS:"compression molding" '
            'OR TITLE_ABS:"compression moulding")')
REVIEW = '(PUB_TYPE:"review" OR TITLE:review)'


def build_query(family):
    """Return the full search query for one material family."""
    return (
        f"TITLE_ABS:{family} AND {FILM} AND {PROPS} AND {PACKAGING} "
        f"AND OPEN_ACCESS:y AND IN_EPMC:y "
        f"NOT {BIOMED} NOT {SYNTHETIC} NOT {NOT_CAST} NOT {REVIEW}"
    )