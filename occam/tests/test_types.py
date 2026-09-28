"""Occam's copied types are held to the engine's (#150).

The package may not import the engine — doing so loads the whole knowledge
base — so the ordered types are copied. A copy that drifts would make
preference compare differently here than there, silently. Tests may import
what the package may not, so the comparison lives here.
"""

from occam.types import Pramana


def test_pramana_matches_the_engine_member_for_member():
    from anvikshiki_v4.schema_v4 import PramanaType
    assert {m.name: m.value for m in Pramana} == {m.name: m.value for m in PramanaType}
