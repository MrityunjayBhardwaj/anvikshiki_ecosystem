# anvikshiki_v4/paths.py
"""Resolving the repo-relative data paths that callers pass around.

Knowledge bases and guide directories are referred to throughout the tree by
repo-relative literals — "anvikshiki_v4/data/business_expert.yaml",
"guides/business_expert". Those resolve against the current working directory,
which is mutable and belongs to whoever started the process, so the same
literal named a real file from the repo root and nothing at all from anywhere
else. The test suite reported 263 passed or 73 file-not-found errors on the
same commit depending on where pytest was launched, and a server started from
the wrong directory served answers with no knowledge loaded.

This module exists because that was the second such fix. The first anchored
knowledge-base loading; when guide loading needed the identical treatment, the
choice was to write the same resolution twice or to put it in one place. The
next caller that takes a repo-relative path should use `resolve_repo_path` and
inherit the behaviour rather than reimplement it.
"""

import errno
import os
from pathlib import Path

# This file lives at <repo>/anvikshiki_v4/paths.py, so the repo root is two
# levels up. Anchored to __file__ because that does not move; cwd does.
REPO_ROOT = Path(__file__).resolve().parent.parent


def resolve_repo_path(path: str | os.PathLike, *, description: str = "path") -> Path:
    """Resolve a path that may be absolute, cwd-relative, or repo-relative.

    Order, chosen so that nothing which works today changes behaviour:
      1. the path as given — absolute, or relative to the working directory
      2. the same path relative to the repo root
      3. neither exists → FileNotFoundError naming the path the caller asked
         for, not the anchored one it never mentioned

    The repo-root attempt is a fallback, never an override, so a caller that
    deliberately points at a file beside its own working directory keeps it,
    and a typo stays a typo rather than being laundered into a silent success.
    """
    candidate = Path(path)
    if candidate.exists():
        return candidate

    anchored = REPO_ROOT / path
    if anchored.exists():
        return anchored

    raise FileNotFoundError(
        errno.ENOENT, f"{os.strerror(errno.ENOENT)} ({description})", str(path)
    )
