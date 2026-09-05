"""The authoring prompt and the knowledge-base schema use the same words (#16).

`test_reference_bank_identifiers.py` checks the *output* side: every entry in a
shipped bank carries a resolution status and, where it claims one, an
identifier. This module checks the *input* side — that the meta-prompt which
produces those banks actually asks for what the schema requires.

The gap between the two is a hand transcription. Nothing parses the meta-prompt;
a human pastes it into a model, the model emits a Reference Bank as prose, and a
human transcribes that prose into YAML. So the prompt's wording is the only
thing standing between a new domain and another 25-entry bank with zero
identifiers, and it had been sitting in the repo for months with no test
touching it at all — 3,962 lines that nothing in the suite read.

What can actually be checked at this boundary is vocabulary. If the prompt asks
for `not_a_locatable_work` and the schema spells it `unlocatable`, the
transcription step invents the mapping once per entry and the laws in the
sibling module reject the result. Pinning the two spellings together is cheap
and is the failure that would otherwise be found 55 entries later.

What is deliberately NOT checked here: that any bank was actually authored with
v3.27. The three shipped banks predate it — the corpus is `guides/v325_new/` and
the copywriting input prompt names v3.25 — so an assertion that production banks
came from this prompt would be false today and would stay false until a fourth
domain is authored. This module makes no claim about the shipped guides.

v3.26 is left untouched on purpose. It is the record of a released version, and
editing it in place would make the tracked file no longer be the v3.26 that
exists. A test below pins that.
"""

from pathlib import Path

# Anchored to this file, not the working directory (#61), and the meta-prompts
# are TRACKED — unlike the trace fixtures in #114, they are present in a fresh
# clone, so these laws need no skip guard. Verified by running the suite in a
# detached worktree, which carries no ignored files.
_THEORY = Path(__file__).resolve().parents[2] / "theory" / "history" / "meta_prompts"
PROMPT_PATH = _THEORY / "meta_prompt_v3_27.md"
PRIOR_PATH = _THEORY / "meta_prompt_v3_26.md"

# Imported rather than re-spelled. If the schema's vocabulary changes, this
# module must fail — copying the four strings here would let the two sides
# drift silently, which is the exact defect being guarded against.
from anvikshiki_v4.tests.test_reference_bank_identifiers import VALID_STATUSES


def _prompt() -> str:
    return PROMPT_PATH.read_text()


def test_the_prompt_exists_and_is_substantial():
    """Denominator for every law below. A missing or truncated file would make
    the `in` checks fail loudly, but an empty one passes nothing meaningful."""
    assert PROMPT_PATH.exists(), PROMPT_PATH
    assert len(_prompt().splitlines()) > 3900


def test_every_schema_status_is_named_in_the_prompt():
    """The load-bearing law. The author is told to write exactly the words the
    bank is validated against."""
    text = _prompt()
    missing = sorted(s for s in VALID_STATUSES if s not in text)
    assert not missing, (
        f"{len(missing)} of {len(VALID_STATUSES)} schema statuses are absent "
        f"from the authoring prompt: {missing}. An author following this prompt "
        f"would produce a bank that test_reference_bank_identifiers.py rejects."
    )


def test_the_prompt_names_every_identifier_field_the_schema_reads():
    """`test_every_resolved_entry_carries_an_identifier` accepts work_id, doi
    or url, and `test_a_resolved_entry_without_an_isbn_says_why` reads isbn_13
    and isbn_note. All five must be askable for."""
    text = _prompt()
    fields = ["doi", "work_id", "url", "isbn_13", "isbn_note"]
    missing = [f for f in fields if f not in text]
    assert not missing, f"{missing} of {len(fields)} identifier fields unnamed"


def test_the_prompt_requires_the_date_and_method():
    """`checked` and `via` are required of every entry by the sibling module.
    A locator resolves at a moment in time; without the date a stale identifier
    is indistinguishable from a fresh one."""
    text = _prompt()
    for token in ("checked", "via"):
        assert token in text, token


def test_the_prompt_forbids_writing_fabricated():
    """`test_no_entry_is_marked_fabricated` rejects the word. The prompt must
    say so, or an author meets that law only by accident. `not_found` means we
    looked and failed; it is not a finding that the source is invented."""
    text = _prompt()
    assert "fabricated" in text, "the prohibition is not stated at all"
    assert "not_found` is **not** `fabricated`" in text or \
           "not_found is not fabricated" in text, \
           "the distinction between not_found and fabricated is not drawn"


def test_ambiguous_is_told_to_choose_nothing():
    """`test_ambiguous_entries_list_their_candidates_and_choose_none` rejects an
    ambiguous entry that carries an identifier. The prompt must ask for
    candidates and forbid picking, or that law fires on the first ambiguity."""
    text = _prompt()
    assert "candidates" in text
    assert "choose neither" in text or "none was chosen" in text


def test_the_gate_counts_what_the_template_asks_for():
    """A requirement stated in the template and unchecked at the gate is one the
    generator can skip silently. The Stage 3 self-audit must name it."""
    text = _prompt()
    gate_start = text.index("STAGE 3 GATE")
    gate = text[gate_start:gate_start + 3000]
    assert "resolution" in gate.lower(), "the gate does not audit resolution status"
    assert "identifier" in gate.lower(), "the gate does not audit identifier presence"


def test_the_prior_version_was_not_rewritten():
    """v3.26 is a released version, and the three shipped banks were authored
    before any identifier requirement existed. Editing it in place would make
    the repo claim those guides came from a prompt requiring identifiers, which
    they demonstrably do not carry — 0 of 25 and 0 of 30. The requirement is a
    new version, not a revision of the old record."""
    prior = PRIOR_PATH.read_text()
    assert "not_a_locatable_work" not in prior, (
        "v3.26 has been edited to include the identifier requirement. It is the "
        "record of a released version; add a new version instead."
    )
    assert "END OF META-PROMPT v3.26" in prior


def test_the_new_version_declares_itself():
    """Two files differing by 90-odd lines with the same version banner is how a
    prompt gets pasted from the wrong copy."""
    text = _prompt()
    assert "END OF META-PROMPT v3.27" in text
    assert "v3.27 CHANGELOG" in text
