#!/usr/bin/env bash
# Repository gate for jcheng-scenarios. Run locally or from CI; it touches no
# robot, no device, no DDS graph and no network service.
#
#   bash scripts/check_repo_gate.sh
#
# It checks: required files, no LICENSE, shell/Python syntax, the no-hardware
# boundary, secret/weight scans, the eight schemas, every shipped scenario, the
# test suite and relative documentation links.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

fail() { printf 'GATE FAIL: %s\n' "$*" >&2; exit 1; }
step() { printf '== %s\n' "$*"; }

step "required files"
while IFS= read -r path; do
    [[ -e "$path" ]] || fail "missing $path"
done <<'EOF'
README.md
README.zh-CN.md
ROADMAP.md
CHANGELOG.md
ACCEPTANCE.md
VERSION
LICENSE-REVIEW.md
capability.yaml
registry.yaml
pyproject.toml
docs/ARCHITECTURE.md
docs/SCEN_LAYER.md
docs/SCENARIO_MODEL.md
docs/CAPABILITY_MATCHING.md
docs/EVALUATION_MODEL.md
docs/AUTHORING.md
docs/DEPENDENCY_REVIEW.md
docs/ASSET_AUDIT_20261127.md
scenarios/README.md
scenarios/ore_sorting/scenario.yaml
scenarios/ore_sorting/environment.yaml
scenarios/ore_sorting/semantics.yaml
scenarios/ore_sorting/task.yaml
scenarios/ore_sorting/capability-requirements.yaml
scenarios/ore_sorting/operational-constraints.yaml
scenarios/ore_sorting/evaluation.yaml
schemas/scenario-registry.v1.schema.json
schemas/scenario-profile.v1.schema.json
schemas/environment-profile.v1.schema.json
schemas/semantic-profile.v1.schema.json
schemas/task-specification.v1.schema.json
schemas/capability-requirements.v1.schema.json
schemas/operational-constraints.v1.schema.json
schemas/evaluation-specification.v1.schema.json
src/jcheng_scenarios/__init__.py
src/jcheng_scenarios/__main__.py
src/jcheng_scenarios/cli.py
src/jcheng_scenarios/loader.py
src/jcheng_scenarios/model.py
src/jcheng_scenarios/registry.py
src/jcheng_scenarios/schema.py
tests/test_cli.py
tests/test_contract.py
tests/test_docs.py
tests/test_no_hardware.py
tests/test_registry.py
tests/test_scenario_content.py
tests/test_schemas.py
evidence/README.md
evidence/20261127_scaffold/README.md
scripts/check_repo_gate.sh
.github/CODEOWNERS
.github/workflows/ci.yml
EOF

step "no LICENSE before the review closes"
[[ ! -e LICENSE ]] || fail "LICENSE must not exist before the license review closes"

step "shell syntax"
while IFS= read -r script; do
    bash -n "$script" || fail "bash -n $script"
done < <(find scripts -name '*.sh' -type f | sort)

step "python syntax"
python3 -m compileall -q src tests

step "no hardware, DDS, device or execution access"
python3 -m pytest -q tests/test_no_hardware.py

step "secret scan"
if grep -rInE \
        'ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----' \
        --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ \
        --exclude='check_repo_gate.sh' . >/dev/null 2>&1; then
    fail "possible secret material found"
fi
if find . -path ./.git -prune -o -path ./.venv -prune -o \
        -name '*.env' -print | grep -q .; then
    fail "*.env files must stay outside the repository"
fi
if find . -path ./.git -prune -o -path ./.venv -prune -o \
        \( -name '*.pt' -o -name '*.onnx' -o -name '*.engine' \
        -o -name '*.bag' -o -name '*.db3' -o -name '*.mcap' \) \
        -print | grep -q .; then
    fail "model weights and recorded bags must stay outside the repository"
fi

step "schema self-check"
PYTHONPATH=src python3 - <<'PY'
from jcheng_scenarios.schema import check_all_schemas

problems = check_all_schemas()
if problems:
    raise SystemExit("\n".join(problems))
print("all schemas are valid Draft 2020-12 documents")
PY

step "catalog validation"
PYTHONPATH=src python3 -m jcheng_scenarios validate --root .
PYTHONPATH=src python3 -m jcheng_scenarios list --root .

step "tests"
python3 -m pytest -q

step "documentation links"
python3 -m pytest -q tests/test_docs.py

step "gate OK"
