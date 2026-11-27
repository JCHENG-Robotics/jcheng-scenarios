# Acceptance report

> Status: **pass** as of 2026-11-27 for v0.1.0.
> Operator: automated ZCode session. Reviewer: pending.
> Scope: repository structure, schema validity and offline catalog validation only.
> No motion command was sent; the repository has no device, DDS or executor path.

## 1. Gates

| Gate | Command | Level | Result | Evidence |
|---|---|---|---|---|
| Repository gate | `bash scripts/check_repo_gate.sh` | L0 | pass | [evidence/20261127_scaffold/gate.txt](evidence/20261127_scaffold/gate.txt) |
| Catalog validation | `jcheng-scenarios validate --root .` | L0 | pass | [evidence/20261127_scaffold/gate.txt](evidence/20261127_scaffold/gate.txt) |
| No-hardware / no-DDS boundary | `python3 -m pytest -q tests/test_no_hardware.py` | L0 | pass | [evidence/20261127_scaffold/pytest.txt](evidence/20261127_scaffold/pytest.txt) |
| Unit and registry tests | `python3 -m pytest -q` | L1 | pass | [evidence/20261127_scaffold/pytest.txt](evidence/20261127_scaffold/pytest.txt) |
| Documentation links | `python3 -m pytest -q tests/test_docs.py` | L0 | pass | [evidence/20261127_scaffold/pytest.txt](evidence/20261127_scaffold/pytest.txt) |
| Mock integration | Not applicable | L2 | Not applicable | No consumer exists in v0.1.0 |
| Mock end-to-end | Not applicable | L3 | Not applicable | No runtime exists in v0.1.0 |
| Replay | Not applicable | L4 | Not applicable | No recorded scenario run exists |
| Hardware | Not applicable | L5 | Not applicable | No device or motion path |

## 2. Verified claims

| Claim | Level | Evidence |
|---|---|---|
| The repository ships the required admission and documentation files. | L0 | `tests/test_contract.py`, gate output |
| Every shipped JSON Schema is a valid Draft 2020-12 schema with local references only. | L0 | `tests/test_schemas.py` |
| The registry and the `ore_sorting` scenario validate with zero errors. | L0 | `tests/test_schemas.py`, `jcheng-scenarios validate` |
| Duplicate IDs, missing profile files, version mismatches, unknown cross-references and non-finite numbers fail closed. | L1 | `tests/test_registry.py` |
| The CLI returns deterministic exit codes and a machine-readable report. | L1 | `tests/test_cli.py` |
| The catalog contains no hardware, DDS, device or execution tokens in code or scenario data. | L0 | `tests/test_no_hardware.py` |
| Scenario content declares no measurements, thresholds or compatibility results. | L1 | `tests/test_scenario_content.py` |
| Root and `docs/` relative links resolve. | L0 | `tests/test_docs.py` |

## 3. Not verified

| Item | Reason | Risk |
|---|---|---|
| Device compatibility | No `jcheng-devices` profile exists; the vocabulary is `local_draft`. | A requirement may be unsatisfiable on the ArmPi Ultra; no device claim is made. |
| Environment dimensions | All values are `design_target`; no workcell was measured. | A real cell may not fit the declared stations or reach. |
| Task feasibility | No orchestration or motion path has consumed the task specification. | Preconditions may be incomplete or unimplementable. |
| Evaluation metrics and thresholds | No dataset, baseline or operator-accepted target exists. | No success claim can be made. |
| Consumer integration | Applications, simulation and benchmark integrations are `Not started`. | The schemas may change before the first consumer. |
| Hardware behaviour | No device access or supervised run exists. | Nothing here is a hardware validation. |
| Safety | Scenario constraints are not a safety mechanism. | `jcheng-system` remains the only authority; the platform has no e-stop, brake or self-collision model. |

## 4. Limitations

- A schema pass is not a safety certification, a device-compatibility statement
  or a task acceptance result.
- `ore_sorting` is a design declaration, not a customer workcell or a measured
  production scenario.
- The semantic profile deliberately forbids `true_centroid`, `full_extent`,
  `volume`, `mass`, `material_composition`, `ore_grade` and `economic_value`.
  Their absence is a design rule, not an omission.
- Synthetic, public, mock, simulation and replay results are never hardware
  validation. This release has none of them.
- The repository is Experimental and has no released contract. The SCEN schemas
  are local v1 documents.

## 5. Sign-off

| Role | Name | Date | Result |
|---|---|---|---|
| Operator | automated ZCode session | 2026-11-27 | pass at L0/L1 |
| Reviewer | pending | — | pending |

## 6. Machine-readable report

`jcheng-scenarios validate --root . --json` emits a deterministic catalog
validation report. It is **not** an `acceptance-report.v1` document and is not
published as one: no cross-repository acceptance-report contract is consumed in
v0.1.0.

## Related

- [README](README.md)
- [Roadmap](ROADMAP.md)
- [Changelog](CHANGELOG.md)
- [Evidence](evidence/README.md)
- [`jcheng-system` safety](https://github.com/JCHENG-Robotics/jcheng-system/blob/main/docs/SAFETY.md)
- [`.github` acceptance](https://github.com/JCHENG-Robotics/.github/blob/main/ACCEPTANCE.md)
