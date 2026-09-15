#!/usr/bin/env python3
"""Derive the Debian version for the pinned usdr-lib snapshot.

Produces 0.9.10b~git<YYYYMMDD>.<shortsha>-0+welland1 from the pinned
UPSTREAM_COMMIT (date = commit date, so a re-pin to a newer commit re-versions
deterministically). Independent of HEAD, so packaging commits layered on top do
not change the version.

Why a snapshot rather than the tagged release: upstream's last tag is v0.9.9
(January 2025) and it ships no trixie packages, while main has ~20 months of
fixes and its own changelog already says "Switching to 0.9.10b". The ~git suffix
sorts BELOW an eventual official 0.9.10b and ABOVE 0.9.9.

Upstream's debian/ lives at packaging/debian-bookworm; the workflow copies it to
debian/ at build time rather than vendoring a fork of it, so upstream packaging
changes are picked up automatically. trixie is bookworm+1 and the packaging is
plain debhelper 13, so it applies unmodified.
"""
import argparse
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CHANGELOG = REPO / "debian" / "changelog"
SOURCE = "usdr"
BASE = "0.9.10b"          # the release this snapshot precedes
REVISION = "0+welland1"
MAINTAINER = "Tim 'mithro' Ansell <me@mith.ro>"
# Pinned upstream usdr-lib commit; the version tracks THIS, not packaging HEAD.
UPSTREAM_COMMIT = "069df21"


def _git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args],
                          capture_output=True, text=True, check=True).stdout.strip()


def version():
    sha = _git("rev-parse", "--short=7", UPSTREAM_COMMIT)
    date = _git("log", "-1", "--format=%cd", "--date=format:%Y%m%d", UPSTREAM_COMMIT)
    return f"{BASE}~git{date}.{sha}-{REVISION}"


def write_changelog():
    date = _git("log", "-1", "--format=%cd", "--date=rfc2822", UPSTREAM_COMMIT)
    sha = _git("rev-parse", UPSTREAM_COMMIT)
    CHANGELOG.parent.mkdir(parents=True, exist_ok=True)
    CHANGELOG.write_text(
        f"{SOURCE} ({version()}) unstable; urgency=medium\n\n"
        f"  * Snapshot build of upstream usdr-lib at {sha}\n"
        f"    for Debian 13 (trixie); upstream ships bookworm/bionic only.\n"
        f"  * Packaging copied verbatim from upstream packaging/debian-bookworm.\n\n"
        f" -- {MAINTAINER}  {date}\n"
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-changelog", action="store_true")
    a = ap.parse_args()
    (write_changelog if a.write_changelog else lambda: print(version()))()
