#!/usr/bin/env bash
# Push, rebasing on the remote if another run pushed first. Data paths never conflict
# because every capture writes new, uniquely named files. The one shared file per source,
# _latest.json, takes this run's version on conflict (`-X theirs` during a rebase means the
# commit being replayed); at worst the next run stores one redundant copy.
set -euo pipefail
branch="$1"
for i in 1 2 3 4 5; do
  if git push origin "HEAD:${branch}"; then exit 0; fi
  echo "push rejected (attempt $i); rebasing"
  git fetch origin "$branch"
  git rebase -X theirs "origin/${branch}" || { git rebase --abort; exit 1; }
  sleep $((i * 5))
done
exit 1
