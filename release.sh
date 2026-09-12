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
  --from STEP   Start execution from STEP (1-8). Skips earlier steps.
  --help        Show this help message.

Steps:
  1  Verify preconditions (branch = main, clean working tree)
  2  Create and push git tag VERSION
  3  Build distribution packages (python -m build)
  4  Install built package in a temporary venv and run tests
  5  Sign dist artifacts with GPG (creates .asc detached signatures)
  6  Upload to PyPI (twine upload dist/*.whl dist/*.tar.gz dist/*.asc)
  7  Create GitHub release draft
  8  Copy release notes to CHANGELOG.md

Examples:
  bash $0 4.0beta2
  bash $0 4.0beta2 --from 3
  bash $0 3.1 --from 6
EOF
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --from)
      if [[ -z "${2-}" || ! "$2" =~ ^[1-8]$ ]]; then
        echo "ERROR: --from requires a step number between 1 and 8"
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
echo "Python:       $(python --version 2>&1)"
echo "Starting from step $START_STEP / 8."
echo ""

# ---------------------------------------------------------------------------
# Helper: skip a step if its number is below START_STEP
# ---------------------------------------------------------------------------
should_run() {
  [[ "$1" -ge "$START_STEP" ]]
}

# ---------------------------------------------------------------------------
# Helper: resolve the GPG signing key to use
#   Priority: $GPG_KEY_ID env var  →  first non-expired secret key
# ---------------------------------------------------------------------------
gpg_key_id() {
  if [[ -n "${GPG_KEY_ID:-}" ]]; then
    echo "$GPG_KEY_ID"
    return
  fi
  # Pick the first secret key that is not expired
  gpg --list-secret-keys --keyid-format=long 2>/dev/null \
    | awk '/^sec / && !/\[expired\]/ { if (match($2, /\/[0-9A-F]+$/)) { print substr($2, RSTART+1, RLENGTH-1); exit } }'
}

# ---------------------------------------------------------------------------
# Step 1 — Verify preconditions
# ---------------------------------------------------------------------------
if should_run 1; then
  echo "=== [1/8] Verifying preconditions ==="
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
  echo "=== [2/8] Creating and pushing git tag $VERSION ==="
  git tag "$VERSION"
  git push --tags
  echo "Tag $VERSION pushed."
  echo ""
fi

# ---------------------------------------------------------------------------
# Step 3 — Build distribution packages
# ---------------------------------------------------------------------------
if should_run 3; then
  echo "=== [3/8] Building distribution packages ==="
  pip install --quiet --upgrade build
  python -m build
  echo "Build complete. Artifacts in dist/:"
  ls dist/
  echo ""
fi

# ---------------------------------------------------------------------------
# Step 4 — Install built package in a temporary venv and run tests
# ---------------------------------------------------------------------------
if should_run 4; then
  echo "=== [4/8] Testing the built package ==="

  VENV_DIR=$(mktemp -d)
  WHL=$(ls -t dist/javacore_analyser-*.whl 2>/dev/null | head -n1)
  if [[ -z "$WHL" ]]; then
    echo "ERROR: No wheel found in dist/. Run step 3 first."
    rm -rf "$VENV_DIR"
    exit 1
  fi

  echo "Creating temporary venv in $VENV_DIR ..."
  python -m venv "$VENV_DIR"

  echo "Installing $WHL[full] ..."
  "$VENV_DIR/bin/pip" install --quiet "$WHL[full]"

  echo "Running tests against the installed package ..."
  PYTHONPATH=test "$VENV_DIR/bin/python" -m unittest discover -s test -v

  echo "All tests passed."
  rm -rf "$VENV_DIR"
  echo ""
fi

# ---------------------------------------------------------------------------
# Step 5 — Sign dist artifacts with GPG
# ---------------------------------------------------------------------------
if should_run 5; then
  echo "=== [5/8] Signing dist artifacts with GPG ==="

  KEY_ID=$(gpg_key_id)
  if [[ -z "$KEY_ID" ]]; then
    echo "ERROR: No usable GPG secret key found."
    echo "  Create one with:  gpg --full-gen-key"
    echo "  Or set GPG_KEY_ID=<key-id> to specify a key explicitly."
    exit 1
  fi
  echo "Using GPG key: $KEY_ID"

  # Remove any stale signatures from a previous run
  rm -f dist/*.asc

  SIGNED=0
  for artifact in dist/javacore_analyser-*.whl dist/javacore_analyser-*.tar.gz; do
    if [[ ! -f "$artifact" ]]; then
      continue
    fi
    gpg --batch --yes \
        --detach-sign --armor \
        --local-user "$KEY_ID" \
        "$artifact"
    echo "  Signed: $artifact  →  ${artifact}.asc"
    SIGNED=$((SIGNED + 1))
  done

  if [[ "$SIGNED" -eq 0 ]]; then
    echo "ERROR: No dist artifacts found to sign. Run step 3 first."
    exit 1
  fi

  echo "Signatures in dist/:"
  ls dist/*.asc
  echo ""
fi

# ---------------------------------------------------------------------------
# Step 6 — Upload to PyPI
# ---------------------------------------------------------------------------
if should_run 6; then
  echo "=== [6/8] Uploading to PyPI ==="
  # Use __token__ as the username and your PyPI API token as the password when prompted.
  # Note: PyPI dropped PGP signature support in 2023; .asc files are NOT uploaded here.
  # Signatures are still attached to the GitHub release (step 7) for out-of-band verification.
  pip install --quiet --upgrade twine
  twine upload dist/*.whl dist/*.tar.gz
  echo ""
fi

# ---------------------------------------------------------------------------
# Step 7 — Create GitHub release (draft)
# ---------------------------------------------------------------------------
if should_run 7; then
  echo "=== [7/8] Creating GitHub release (draft) ==="
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
# Step 8 — Copy release notes to CHANGELOG.md
# ---------------------------------------------------------------------------
if should_run 8; then
  echo "=== [8/8] Copying release notes to CHANGELOG.md ==="
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

echo "=== Release $VERSION complete (started from step $START_STEP / 8) ==="
