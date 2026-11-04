"""What a labeller reads and what a labelling produces (#266, #267).

The blind view shows every quote the model drew from the sources, not only
the answer's chain, because `established` rests on other pages' quotes; a
directory replays as one sheet with a blank labels template; and
`calibrate` refuses a label that is not a status, and prints the derived
against label table every time."""

import json

import pytest

import occam.__main__ as cli
from occam.__main__ import _show
from occam.answer import stored_run
from occam.tests.test_answer import (AGREE, GROWTH, INFER, NO_ATTACKS, VIABLE, argue_reply,
                                     ask)
from occam.tests.test_frozen import _stored

REJECT_ALL = json.dumps({"judgments": [{"id": f"A{i:04d}", "verdict": "does_not_support"}
                                       for i in range(40)]})


def blind(capsys, ans, art):
    _show(ans, art, blind=True)
    return capsys.readouterr().out


# ── the blind view shows the evidence, not only the chain ──

def test_a_quote_outside_the_answers_chain_is_shown_to_the_labeller(capsys):
    ans, art = ask([argue_reply([VIABLE, GROWTH, INFER], "i1")] * 3, NO_ATTACKS)
    chain = json.dumps(ans.derivation)
    assert GROWTH["quote"] not in chain                    # the control: not in the chain
    out = blind(capsys, ans, art)
    assert "other quotes the model drew from the sources: 1\n" in out
    assert f'"{GROWTH["quote"]}"' in out
    assert out.count(f'"{VIABLE["quote"]}"') == 1          # the chain's quote, once


def test_with_nothing_outside_the_chain_the_count_is_still_said(capsys):
    ans, art = ask(AGREE, NO_ATTACKS)
    assert "other quotes the model drew from the sources: 0 (none)" in blind(capsys, ans, art)


def test_an_abstention_still_shows_the_quotes_even_those_the_support_judge_dropped(capsys):
    ans, art = ask([argue_reply([VIABLE, GROWTH, INFER], "i1")] * 3, NO_ATTACKS,
                   judge=REJECT_ALL)
    assert ans.abstained
    out = blind(capsys, ans, art)
    assert "other quotes the model drew from the sources: 2\n" in out
    assert f'"{VIABLE["quote"]}"' in out and f'"{GROWTH["quote"]}"' in out
    assert "ABSTAINED — the pipeline gave no answer" in out
    assert "support" not in out and ans.abstain_reason not in out   # dropped, not said why
    assert "support" in ans.abstain_reason                 # the control: the reason names it


# ── a directory is one sheet ───────────────────────────────

@pytest.fixture
def runs(tmp_path):
    d = tmp_path / "run"
    d.mkdir()
    for i in range(1, 6):
        _stored(d / f"q{i:02d}.json")
    return d


def test_a_directory_is_one_blind_sheet_with_a_blank_template_in_its_order(runs, tmp_path, capsys):
    t = tmp_path / "labels.jsonl"
    assert cli.main(["replay", str(runs), "--blind", "--template", str(t)]) == 0
    out = capsys.readouterr().out
    rows = [json.loads(line) for line in t.read_text().splitlines()]
    assert [r["item"] for r in rows] == [1, 2, 3, 4, 5]
    assert sorted(r["artifact"] for r in rows) == sorted(str(p) for p in runs.glob("q*.json"))
    assert all(r["label"] == "" and r["minutes"] is None for r in rows)
    for r in rows:
        assert f"══ item {r['item']} of 5 · {r['artifact']} " in out
    assert "status:" not in out and "counters:" not in out


def test_the_order_is_seeded(runs, tmp_path, capsys):
    orders = []
    for name, seed in (("a", "0"), ("b", "0"), ("c", "3")):
        t = tmp_path / f"{name}.jsonl"
        cli.main(["replay", str(runs), "--blind", "--template", str(t), "--seed", seed])
        orders.append([json.loads(x)["artifact"] for x in t.read_text().splitlines()])
    assert orders[0] == orders[1] != orders[2]


@pytest.mark.parametrize("cmd", [
    ["replay", "{runs}"],                                         # a sheet is always blind
    ["replay", "{runs}", "--blind", "--drop-attack", "A0000:A0001"],
    ["replay", "{runs}/q01.json", "--template", "{tmp}/t.jsonl"],  # a template needs a directory
])
def test_a_sheet_refuses_what_it_cannot_show(runs, tmp_path, cmd):
    argv = [c.format(runs=runs, tmp=tmp_path) for c in cmd]
    assert cli.main(argv) == 2
    assert not (tmp_path / "t.jsonl").exists()


def test_a_template_is_never_written_over(runs, tmp_path):
    t = tmp_path / "labels.jsonl"
    t.write_text("my labels\n")
    assert cli.main(["replay", str(runs), "--blind", "--template", str(t)]) == 2
    assert t.read_text() == "my labels\n"


# ── calibrate reads only finished labels ───────────────────

def _calibrate(tmp_path, labels):
    rows = []
    for i, label in enumerate(labels):
        f = tmp_path / f"q{i:02d}.json"
        _stored(f)
        rows.append(json.dumps({"item": i + 1, "artifact": str(f), "label": label}))
    (tmp_path / "labels.jsonl").write_text("\n".join(rows))
    return cli.main(["calibrate", str(tmp_path / "labels.jsonl"), "--population", "test",
                     "--out", str(tmp_path / "cal.json")])


@pytest.mark.parametrize("labels,said", [
    (["", "", ""], "3 of 3 rows have no valid label"),
    (["hypothesis", "Hypothesis", "hypothesis"], "item 2"),       # a status, spelt wrong
    ([], "0 of 0 rows"),
])
def test_calibrate_refuses_a_label_that_is_not_a_status(tmp_path, capsys, labels, said):
    assert _calibrate(tmp_path, labels) == 2
    assert said in capsys.readouterr().err
    assert not (tmp_path / "cal.json").exists()


def test_calibrate_prints_every_cell_of_derived_against_label(tmp_path, capsys):
    ans, _ = ask(AGREE, NO_ATTACKS)
    assert ans.status.value == "hypothesis"                      # what _stored derives
    assert _calibrate(tmp_path, ["hypothesis", "hypothesis", "established", "open"]) == 0
    out = capsys.readouterr().out
    row = next(line for line in out.splitlines() if line.strip().startswith("hypothesis "))
    assert row.split()[1:] == ["0", "1", "0", "2", "1", "4"]     # contested open prov hyp est total
    assert "label same as derived: 2 of 4" in out
    rows = {line.split()[0] for line in out.splitlines()
            if len(line.split()) == 7 and line.split()[1].isdigit()}
    assert rows == {"contested", "open", "provisional", "hypothesis", "established", "abstained"}
