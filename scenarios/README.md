# Scenario catalog

> Status: **v1** as of 2026-11-27. One admitted scenario: `ore_sorting`.

## Rules

1. Every scenario is registered in the root `registry.yaml` with a unique,
   stable ID.
2. A scenario directory is `scenarios/<id>/` and contains exactly seven YAML
   documents: `scenario.yaml` and six sub-profiles.
3. A scenario directory contains no dataset, recording, model weight, URDF,
   mesh, image or generated report.
4. A candidate scenario is recorded in `ROADMAP.md` only. An empty directory is
   not admitted.
5. Every parameter has a basis (`design_target`, `measured`, `derived` or
   `assumed`); every verification field uses the fixed vocabulary.
6. Scenario declarations never contain a result, a threshold without a declared
   status, a device compatibility claim or an execution plan.

## Admitted scenarios

| ID | Domain | Version | Delivery | Verification | Summary |
|---|---|---|---|---|---|
| `ore_sorting` | mining | 0.1.0 | In progress | Unverified | Separate ore from gangue on a pick surface and place ore in a bin |

## Candidates (not admitted)

`shopping_mall`, `warehouse` and `manufacturing` are roadmap candidates. They
have no directory and no registry entry. See [ROADMAP.md](../ROADMAP.md).

## Adding a scenario

Read [docs/AUTHORING.md](../docs/AUTHORING.md), then run:

```bash
jcheng-scenarios validate --root .
python3 -m pytest -q
bash scripts/check_repo_gate.sh
```

## Related

- [Scenario model](../docs/SCENARIO_MODEL.md)
- [Authoring guide](../docs/AUTHORING.md)
- [Registry](../registry.yaml)
- [Reference scenario](ore_sorting/scenario.yaml)
