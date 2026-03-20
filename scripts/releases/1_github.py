#!/usr/bin/env python3
"""
Tag and push a GitHub release for capsec-github-action.

Usage:
    python scripts/releases/1_github.py          # dry-run (shows what would happen)
    python scripts/releases/1_github.py --push   # create tag and push

What it does:
    1. Reads the version from action.yml (auto-increments from latest git tag if not set)
    2. Checks that the git tag doesn't already exist on GitHub
    3. Creates a git tag v{version} and pushes it to origin
    4. Updates the floating major tag (v1) to point to the new release

The floating major tag (v1) is how users reference the action:
    uses: bordumb/capsec-github-action@v1

Requires:
    - python3 (no external dependencies)
    - git on PATH
"""

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ACTION_YML = REPO_ROOT / "action.yml"
GITHUB_REPO = "bordumb/capsec-github-action"


def get_latest_tag() -> str | None:
    """Get the latest semver tag from git."""
    result = subprocess.run(
        ["git", "tag", "-l", "v*.*.*", "--sort=-v:refname"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    tags = result.stdout.strip().splitlines()
    return tags[0] if tags else None


def bump_patch(tag: str) -> str:
    """Bump patch version: v1.0.0 -> v1.0.1"""
    m = re.match(r"v(\d+)\.(\d+)\.(\d+)", tag)
    if not m:
        return "v1.0.0"
    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
    return f"v{major}.{minor}.{patch + 1}"


def get_version() -> str:
    """Determine the next version tag."""
    latest = get_latest_tag()
    if latest:
        return bump_patch(latest)
    return "v1.0.0"


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        print(f"ERROR: git {' '.join(args)} failed:\n{result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def local_tag_exists(tag: str) -> bool:
    result = subprocess.run(
        ["git", "tag", "-l", tag],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    return bool(result.stdout.strip())


def remote_tag_exists(tag: str) -> bool:
    result = subprocess.run(
        ["git", "ls-remote", "--tags", "origin", f"refs/tags/{tag}"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    return bool(result.stdout.strip())


def delete_local_tag(tag: str) -> None:
    subprocess.run(
        ["git", "tag", "-d", tag],
        capture_output=True,
        cwd=REPO_ROOT,
    )


def main() -> None:
    push = "--push" in sys.argv

    tag = get_version()
    major_tag = re.match(r"(v\d+)", tag).group(1)  # e.g., "v1"
    latest = get_latest_tag()

    print(f"Latest tag:    {latest or '(none)'}")
    print(f"New tag:       {tag}")
    print(f"Floating tag:  {major_tag} (will point to {tag})")

    # Check remote
    if remote_tag_exists(tag):
        print(f"\nERROR: Git tag {tag} already exists on origin.", file=sys.stderr)
        print("Delete the remote tag first or let it auto-bump.", file=sys.stderr)
        sys.exit(1)

    if local_tag_exists(tag):
        print(f"Local tag {tag} exists but not on origin — deleting stale local tag.")
        delete_local_tag(tag)

    # Clean working tree
    status = git("status", "--porcelain")
    if status:
        print(f"\nERROR: Working tree is not clean:\n{status}", file=sys.stderr)
        print("Commit or stash changes before releasing.", file=sys.stderr)
        sys.exit(1)

    if not push:
        print(f"\nDry run: would create and push tag {tag}")
        print(f"         would update floating tag {major_tag} -> {tag}")
        print("Run with --push to execute.")
        return

    # Create version tag
    print(f"\nCreating tag {tag}...", flush=True)
    result = subprocess.run(
        ["git", "tag", "-a", tag, "-m", f"release: {tag}"],
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        print(f"\nERROR: git tag failed (exit {result.returncode})", file=sys.stderr)
        sys.exit(1)

    # Push version tag
    print(f"Pushing tag {tag} to origin...", flush=True)
    result = subprocess.run(
        ["git", "push", "origin", tag],
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        print(f"\nERROR: git push failed (exit {result.returncode})", file=sys.stderr)
        sys.exit(1)

    # Update floating major tag (v1 -> latest)
    print(f"Updating floating tag {major_tag} -> {tag}...", flush=True)
    if local_tag_exists(major_tag):
        delete_local_tag(major_tag)

    result = subprocess.run(
        ["git", "tag", "-fa", major_tag, "-m", f"{major_tag} floating tag -> {tag}"],
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        print(f"\nERROR: git tag {major_tag} failed (exit {result.returncode})", file=sys.stderr)
        sys.exit(1)

    result = subprocess.run(
        ["git", "push", "origin", major_tag, "--force"],
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        print(f"\nERROR: git push {major_tag} failed (exit {result.returncode})", file=sys.stderr)
        sys.exit(1)

    print(f"\nDone.")
    print(f"  Version tag: {tag}")
    print(f"  Floating:    {major_tag} -> {tag}")
    print(f"  Users reference: uses: {GITHUB_REPO}@{major_tag}")


if __name__ == "__main__":
    main()
