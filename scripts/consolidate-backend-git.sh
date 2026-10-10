#!/usr/bin/env bash
#
# Consolidate backend/ into the root repository.
#
# Why this exists: the root repo tracks `backend` as a bare gitlink
# (mode 160000, no .gitmodules) while backend/.git is a separate nested
# repository. GitHub therefore sees NO backend files, which means backend CI,
# Docker builds, and PR diffs cannot see backend changes. Retiring the nested
# repo and tracking backend/ as ordinary files fixes all of that.
#
# The nested repo is never deleted: it is renamed to backend/.git.pre-consolidation
# (including all of its history and uncommitted state) so this is fully reversible.
#
# Usage (Git Bash on Windows works fine):
#   scripts/consolidate-backend-git.sh
#
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -d backend/.git ]; then
  echo "backend/.git not found - backend already consolidated. Nothing to do."
  exit 0
fi

if [ -f .gitmodules ] && grep -q "path = backend" .gitmodules; then
  echo "ERROR: backend is registered in .gitmodules as a real submodule."
  echo "Remove it first: git submodule deinit backend && git rm backend"
  exit 1
fi

GITLINK_SHA=$(git ls-files -s backend | awk '$1 == 160000 {print $2; exit}')
echo "Current gitlink entry: ${GITLINK_SHA:-none}"

# Safety: consolidation must never make backend/.env committable.
# --no-index is required while backend/ is still a gitlink: without it,
# git check-ignore aborts with "Pathspec ... is in submodule".
if ! git check-ignore -q --no-index -- backend/.env; then
  echo "ERROR: backend/.env would NOT be git-ignored after consolidation."
  echo "Add '.env' to backend/.gitignore, verify 'git check-ignore --no-index backend/.env', then re-run."
  exit 1
fi

# Safety: the renamed nested .git dir must never be staged as ordinary files.
if ! git check-ignore -q --no-index -- backend/.git.pre-consolidation/HEAD; then
  echo "ERROR: backend/.git.pre-consolidation would NOT be git-ignored after the rename."
  echo "Add '.git.pre-consolidation' to backend/.gitignore and re-run."
  exit 1
fi

echo "Renaming backend/.git -> backend/.git.pre-consolidation (history is preserved)"
mv backend/.git backend/.git.pre-consolidation

echo "Removing the gitlink entry and staging backend/ as normal files"
git rm --cached -q backend
git add backend

STAGED_DANGER=$(git diff --cached --name-only | grep -E '(^|/)\.env$|\.pre-consolidation/|\.db$|(^|/)\.venv/|(^|/)__pycache__/|(^|/)backups/|(^|/)uploads/' || true)
if [ -n "$STAGED_DANGER" ]; then
  echo "ERROR: refusing to continue - dangerous paths got staged:"
  echo "$STAGED_DANGER" | head -20
  echo
  echo "Rollback: git reset -q && mv backend/.git.pre-consolidation backend/.git"
  echo "Then fix the ignore rules and re-run."
  exit 1
fi

echo
echo "Done. backend/ sources are now staged in the root repository."
echo
echo "  Review : git status && git diff --cached --stat | tail -20"
echo "  Commit : git commit -m \"Consolidate backend sources into root repository\""
echo
echo "Rollback (only valid BEFORE the commit above):"
echo "  git rm -r --cached -q backend"
[ -n "$GITLINK_SHA" ] && echo "  git update-index --add --cacheinfo 160000,${GITLINK_SHA},backend"
echo "  mv backend/.git.pre-consolidation backend/.git"
echo
echo "After committing, 'git push' enables backend CI and Docker builds on GitHub."
