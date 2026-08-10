#!/usr/bin/env bash
# Release script for javacore-analyser
# Run from the project root on the `main` branch with a clean working tree.
#
# Usage:
#   bash release.sh <VERSION>             # run all steps (1-7)
#   bash release.sh <VERSION> --from 3   # resume from step 3 onwards
#   bash release.sh --help

set -euo pipefail

REPO="IBM/javacore-analyser"
VERSION=""
START_STEP=1

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
usage() {
  cat <<EOF
Usage: $0 <VERSION> [--from STEP] [--help]

  VERSION       The release version tag to create, e.g. 4.0beta2, 3.1, 2.0.1
  --from STEP   Start execution from STEP (1-7). Skips earlier steps.
  --help        Show this help message.

Steps:
  1  Verify preconditions (branch = main, clean working tree)
  2  Create and push git tag VERSION
  3  Build distribution packages (python -m build)
  4  Install built package in a temporary venv and run tests
  5  Upload to PyPI (twine upload)
  6  Create GitHub release draft
  7  Copy release notes to CHANGELOG.md

Examples:
  bash $0 4.0beta2
  bash $0 4.0beta2 --from 3
  bash $0 3.1 --from 5
EOF
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --from)
      if [[ -z "${2-}" || ! "$2" =~ ^[1-7]$ ]]; then
        echo "ERROR: --from requires a step number between 1 and 7"
        exit 1
      fi
      START_STEP="$2"
      shift 2
      ;;
    --help|-h)
      usage
      ;;
    -*)
      echo "ERROR: Unknown option '$1'. Use --help for usage."
      exit 1
      ;;
    *)
      if [[ -z "$VERSION" ]]; then
        VERSION="$1"
      else
        echo "ERROR: Unexpected argument '$1'. VERSION is already set to '$VERSION'."
        exit 1
      fi
      shift
      ;;
  esac
done

if [[ -z "$VERSION" ]]; then
  echo "ERROR: VERSION is required."
  echo ""
  usage
fi

echo "Release:      $VERSION"
echo "Repository:   $REPO"
echo "Starting from step $START_STEP."
echo ""

# ---------------------------------------------------------------------------
# Helper: skip a step if its number is below START_STEP
# ---------------------------------------------------------------------------
should_run() {
  [[ "$1" -ge "$START_STEP" ]]
}

# ---------------------------------------------------------------------------
# Step 1 — Verify preconditions
# ---------------------------------------------------------------------------
if should_run 1; then
  echo "=== [1/7] Verifying preconditions ==="
  BRANCH=$(git rev-parse --abbrev-ref HEAD)
  if [[ "$BRANCH" != "main" ]]; then
    echo "ERROR: must be on 'main' branch (currently on '$BRANCH')"
    exit 1
  fi
  if [[ -n "$(git status --porcelain)" ]]; then
    echo "ERROR: working tree is not clean. Commit or stash your changes first."
    exit 1
  fi
  echo "Branch: $BRANCH — working tree clean. OK."
  echo ""
fi

# ---------------------------------------------------------------------------
# Step 2 — Create and push git tag
# ---------------------------------------------------------------------------
if should_run 2; then
  echo "=== [2/7] Creating and pushing git tag $VERSION ==="
  git tag "$VERSION"
  git push --tags
  echo "Tag $VERSION pushed."
  echo ""
fi

# ---------------------------------------------------------------------------
# Step 3 — Build distribution packages
# ---------------------------------------------------------------------------
if should_run 3; then
  echo "=== [3/7] Building distribution packages ==="
  pip install --quiet build
  python -m build
  echo "Build complete. Artifacts in dist/:"
  ls dist/
  echo ""
fi

# ---------------------------------------------------------------------------
# Step 4 — Install built package in a temporary venv and run tests
# ---------------------------------------------------------------------------
if should_run 4; then
  echo "=== [4/7] Testing the built package ==="

  VENV_DIR=$(mktemp -d)
  WHL=$(ls dist/javacore_analyser-"${VERSION}"-*.whl 2>/dev/null | head -n1)
  if [[ -z "$WHL" ]]; then
    echo "ERROR: No wheel found in dist/ for version $VERSION. Run step 3 first."
    rm -rf "$VENV_DIR"
    exit 1
  fi

  echo "Creating temporary venv in $VENV_DIR ..."
  python -m venv "$VENV_DIR"

  echo "Installing $WHL ..."
  "$VENV_DIR/bin/pip" install --quiet "$WHL"

  echo "Running tests against the installed package ..."
  PYTHONPATH=test "$VENV_DIR/bin/python" -m unittest discover -s test -v

  echo "All tests passed."
  rm -rf "$VENV_DIR"
  echo ""
fi

# ---------------------------------------------------------------------------
# Step 5 — Upload to PyPI
# ---------------------------------------------------------------------------
if should_run 5; then
  echo "=== [5/7] Uploading to PyPI ==="
  # Use __token__ as the username and your PyPI API token as the password when prompted.
  pip install --quiet twine
  twine upload dist/*
  echo ""
fi

# ---------------------------------------------------------------------------
# Step 6 — Create GitHub release (draft)
# ---------------------------------------------------------------------------
if should_run 6; then
  echo "=== [6/7] Creating GitHub release (draft) ==="
  gh release create "$VERSION" dist/* \
    --repo "$REPO" \
    --generate-notes \
    --title "$VERSION" \
    --draft
  echo "Draft release created. Review it with:"
  echo "  gh release view $VERSION --web --repo $REPO"
  echo ""
  echo "Publish the draft once the notes look good:"
  echo "  gh release edit $VERSION --draft=false --repo $REPO"
  echo ""
fi

# ---------------------------------------------------------------------------
# Step 7 — Copy release notes to CHANGELOG.md
# ---------------------------------------------------------------------------
if should_run 7; then
  echo "=== [7/7] Copying release notes to CHANGELOG.md ==="
  NOTES=$(gh release view "$VERSION" --json body --jq '.body' --repo "$REPO")
  TMP=$(mktemp)
  {
    printf "# Changelog\n\n## [%s] - %s\n%s\n\n\n" \
      "$VERSION" "$(date +%Y-%m-%d)" "$NOTES"
    tail -n +2 CHANGELOG.md
  } > "$TMP"
  mv "$TMP" CHANGELOG.md
  echo "CHANGELOG.md updated. Review and commit the change:"
  echo "  git add CHANGELOG.md && git commit --signoff -m \"Ref #release Add $VERSION release notes\""
  echo ""
fi

echo "=== Release $VERSION complete (started from step $START_STEP) ==="
