# Scaffold evidence — 2026-11-27

> Scope: repository admission and offline structural validation for v0.1.0.
> Levels: L0 (static/contract) and L1 (unit). No L2–L5 claim.
> No motion command was sent. No device, DDS graph, ROS node or robot was used.

## Environment

| Item | Value |
|---|---|
| Host | Operator workstation, Linux x86_64 |
| Python | Host Python 3 (3.10+ required; CI covers 3.10 and 3.12) |
| Runtime dependencies | PyYAML 6.x, jsonschema 4.x |
| Test dependency | pytest 7.4+ |
| Robot / DDS | None |

The exact versions observed in the captured run are recorded in `gate.txt` and
`pytest.txt` where the commands print them.

## Commands

```bash
PYTHONPATH=src python3 -m jcheng_scenarios validate --root .
python3 -m pytest -q
bash scripts/check_repo_gate.sh
```

## Results

| File | Content |
|---|---|
| [`gate.txt`](gate.txt) | Full repository gate output: required files, no-license check, syntax, boundary tests, secret/weight scans, catalog validation, tests, documentation links |
| [`pytest.txt`](pytest.txt) | Full pytest output |

Both files are captured command output. They are not edited.

## What this evidence supports

- The repository ships its required files and no `LICENSE`.
- The eight JSON Schemas are valid and self-contained.
- The registry and `ore_sorting` scenario validate with zero errors.
- Negative fixtures fail closed.
- No hardware, DDS, device or execution token appears in code or scenario data.
- Relative documentation links resolve.

## What it does not support

- Device compatibility, task feasibility, metric thresholds or scenario results.
- Any hardware, real-robot, simulation or benchmark claim.
- A safety certification.
- A claim that another repository consumes the catalog.

## Related

- [Acceptance](../../ACCEPTANCE.md)
- [Evidence policy](../README.md)
- [Roadmap](../../ROADMAP.md)
