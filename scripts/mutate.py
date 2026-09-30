"""Run the occam suite once per source mutation and report which laws caught it.

    PYTHONPATH=$(pwd) .venv/bin/python scripts/mutate.py MUTATIONS.json

MUTATIONS.json is a list of {"name", "file", "old", "new"}. Each `old` must
occur in `file` exactly once, or the run stops before touching anything: an
anchor that matches nothing is a mutation that never happened, and it would
read as "survived". The unmutated suite must be green first, or every
mutation would read as killed. Bytecode is disabled and __pycache__ removed first, because
a same-size edit restored within the same second reuses the mutated .pyc.
The file is restored byte-for-byte after each run, and a mutation that changes
no line stops the run, so a zero-line diff cannot pass as a verdict.
"""

import difflib, json, os, shutil, subprocess, sys
from pathlib import Path

muts = json.loads(Path(sys.argv[1]).read_text())
for m in muts:
    n = Path(m["file"]).read_text().count(m["old"])
    if n != 1:
        sys.exit(f"{m['name']}: anchor matched {n} times in {m['file']}")
env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
for d in Path("occam").rglob("__pycache__"):
    shutil.rmtree(d)
base = subprocess.run([sys.executable, "-m", "pytest", "occam", "-q", "-p", "no:cacheprovider"],
                      capture_output=True, text=True, env=env)
if base.returncode != 0:
    # A red baseline kills every mutation, and every "KILLED" would be a lie.
    sys.exit("the suite is red before any mutation, so no verdict would mean "
             "anything; fix it first:\n" + base.stdout[-2000:])
killed = 0
for m in muts:
    for d in Path("occam").rglob("__pycache__"):
        shutil.rmtree(d)
    p = Path(m["file"]); orig = p.read_bytes()
    mutated = orig.decode().replace(m["old"], m["new"], 1)
    changed = sum(1 for l in difflib.unified_diff(orig.decode().splitlines(), mutated.splitlines(), n=0)
                  if l[:1] in "+-" and not l.startswith(("+++", "---")))
    p.write_text(mutated)
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", "occam", "-q", "-p", "no:cacheprovider"],
                           capture_output=True, text=True, env=env)
    finally:
        p.write_bytes(orig)
    failed = [l.split("::")[-1] for l in r.stdout.splitlines() if l.startswith("FAILED")]
    if not changed:
        sys.exit(f"{m['name']}: the mutation changed no line — harness error, not a verdict")
    killed += bool(failed) and r.returncode != 0
    print(f"{'KILLED ' if failed else 'SURVIVED'} {m['name']}  (exit {r.returncode}; {changed} lines changed)")
    for f in failed:
        print("    ", f)
print(f"{killed} of {len(muts)} mutations killed")
sys.exit(0 if killed == len(muts) else 1)
