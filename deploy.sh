#!/bin/sh
# Copy the freshly built site/ into the main branch (built output only) and push.
set -e
ROOT=$(cd "$(dirname "$0")" && pwd)
WT="$ROOT/../ecgmeans-main"
git -C "$ROOT" fetch origin main
[ -d "$WT" ] || git -C "$ROOT" worktree add "$WT" origin/main -B deploy-main
cd "$WT" && git reset -q --hard origin/main
find . -mindepth 1 -maxdepth 1 ! -name .git ! -name .github -exec rm -rf {} +
cp -a "$ROOT/site/." .
git add -A && git commit -q -m "${1:-Deploy build output}" && git push origin HEAD:main
