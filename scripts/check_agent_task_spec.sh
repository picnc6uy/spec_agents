#!/usr/bin/env bash
# agent-task discipline hook: require .agent/tasks/<id>.md on agent/<id> branches.
#
# Source of truth: planning/agent-task/scripts/check_agent_task_spec.sh
# Mirrored into each canonical repo at scripts/check_agent_task_spec.sh and
# wired into .pre-commit-config.yaml as a local hook.
#
# Behavior:
#   - On `main` or any non-agent/* branch: pass (operator-controlled commits).
#   - On `agent/<id>` with `.agent/tasks/<id>.md`: pass.
#   - On `agent/<id>` without that spec: fail with guidance.
#
# Bypass (rare, intentional): `git commit --no-verify`. Use only when the
# operator has explicitly waived the spec for this commit.
#
# See planning/dev-env-handoff.md ("Prompts are soft; protocols are hard")
# and planning/v1-state-report.md for the rationale.

set -eu

branch=$(git branch --show-current)
case "$branch" in
    agent/*) ;;
    *) exit 0 ;;
esac

task_id="${branch#agent/}"
spec=".agent/tasks/${task_id}.md"

if [ ! -f "$spec" ]; then
    cat >&2 <<EOM
agent-task discipline: branch $branch requires $spec
  run:  agent-task new $task_id <type>
  or:   git commit --no-verify   (if operator has waived the spec)
EOM
    exit 1
fi
